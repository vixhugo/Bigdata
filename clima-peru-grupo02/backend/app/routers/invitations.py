"""
Router para gestión de invitaciones estilo GitHub.
Endpoints:
  - POST   /invitations           - Crear invitación (admin)
  - GET    /invitations           - Listar invitaciones (admin)
  - GET    /invitations/{id}      - Detalle de invitación (admin)
  - DELETE /invitations/{id}      - Revocar invitación (admin)
  - GET    /invitations/verify    - Verificar estado de invitación (público)
  - POST   /invitations/accept    - Aceptar invitación (público)
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models.auth import User, Role
from app.models.invitation import Invitation
from app.schemas.invitation import (
    InvitationCreate, InvitationAcceptRequest,
    InvitationResponse, InvitationListResponse, InvitationStatusResponse,
    AcceptInvitationResponse
)
from app.schemas.auth import MessageResponse, TokenResponse
from app.services.auth_service import (
    create_access_token, hash_password, verify_password,
    decode_access_token
)
from app.services.audit_service import create_audit_log
from app.routers.auth_deps import (
    get_current_user, get_current_active_user,
    require_super_admin, require_any_admin, get_client_ip, get_user_agent
)
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/invitations", tags=["invitations"])


# ─── Endpoint: Crear invitación (admin) ───────────────────────────────────────

@router.post("", response_model=InvitationResponse)
async def create_invitation(
    invitation_data: InvitationCreate,
    current_user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """
    Crea una nueva invitación para un usuario.
    Solo administradores pueden invitar nuevos usuarios.
    """
    # Verificar si el email ya está registrado
    existing_user = db.query(User).filter(User.email == invitation_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este email ya está registrado en el sistema.",
        )
    
    # Verificar si ya existe una invitación activa para este email
    existing_invitation = (
        db.query(Invitation)
        .filter(
            Invitation.email == invitation_data.email,
            Invitation.is_accepted == False,
            Invitation.expires_at > datetime.now(timezone.utc)
        )
        .first()
    )
    if existing_invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una invitación activa para {invitation_data.email}. Expira el {existing_invitation.expires_at}.",
        )
    
    # Verificar rol
    role = db.query(Role).filter(Role.id == invitation_data.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado.",
        )
    
    # Generar token único
    token = f"inv_{secrets.token_urlsafe(32)}"
    
    # Calcular fecha de expiración
    expires_at = datetime.now(timezone.utc) + timedelta(days=invitation_data.expires_in_days)
    
    # Crear invitación
    new_invitation = Invitation(
        invited_by_id=current_user.id,
        invited_by_email=current_user.email,
        email=invitation_data.email,
        full_name=invitation_data.full_name,
        role_id=invitation_data.role_id,
        role_name=role.name,
        token=token,
        is_accepted=False,
        expires_at=expires_at,
        message=invitation_data.message,
    )
    
    try:
        db.add(new_invitation)
        db.commit()
        db.refresh(new_invitation)
        
        # Registrar auditoría
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="invitation_created",
            category="invitations",
            target_type="invitation",
            target_id=str(new_invitation.id),
            target_display=f"Invitation to {invitation_data.email}",
            details={"role_id": invitation_data.role_id, "expires_in_days": invitation_data.expires_in_days},
        )
        
        email_sent = EmailService().send_invitation_email(
            invitation_id=new_invitation.id,
            email=new_invitation.email,
            token=new_invitation.token,
            full_name=new_invitation.full_name,
            expires_at=new_invitation.expires_at,
        )
        if not email_sent:
            db.delete(new_invitation)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="La invitación no pudo enviarse. Configura el servicio SMTP e inténtalo nuevamente.",
            )
        
        return new_invitation
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la invitación: {str(e)}",
        )


# ─── Endpoint: Listar invitaciones (admin) ────────────────────────────────────

@router.get("", response_model=InvitationListResponse)
async def list_invitations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, description="all, pending, accepted, expired"),
    current_user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """
    Lista todas las invitaciones con paginación.
    """
    from app.models.invitation import Invitation as InvitationModel
    
    query = db.query(InvitationModel)
    
    if status_filter == "pending":
        query = query.filter(
            InvitationModel.is_accepted == False,
            InvitationModel.expires_at > datetime.now(timezone.utc)
        )
    elif status_filter == "accepted":
        query = query.filter(InvitationModel.is_accepted == True)
    elif status_filter == "expired":
        query = query.filter(InvitationModel.expires_at < datetime.now(timezone.utc))
    
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    
    invitations = (
        query.order_by(InvitationModel.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    return InvitationListResponse(
        items=invitations,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ─── Endpoint: Verificar estado de invitación (público) ───────────────────────

@router.get("/verify/{token}", response_model=InvitationStatusResponse)
async def verify_invitation(
    token: str,
    db: Session = Depends(get_db),
):
    """
    Verifica si una invitación es válida y devuelve sus detalles.
    Uso: El usuario hace clic en el link de la invitación.
    """
    invitation = (
        db.query(Invitation)
        .filter(Invitation.token == token)
        .first()
    )
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitación no encontrada.",
        )
    
    # Verificar si ya fue aceptada
    if invitation.is_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta invitación ya ha sido aceptada.",
        )
    
    # Verificar si expiró
    if invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta invitación ha expirado.",
        )
    
    return InvitationStatusResponse(
        token=token,
        is_valid=True,
        is_expired=False,
        is_accepted=False,
        email=invitation.email,
        full_name=invitation.full_name,
        role_id=invitation.role_id or 0,
        role_name=invitation.role_name,
        message=invitation.message,
        expires_at=invitation.expires_at,
    )


# ─── Endpoint: Aceptar invitación (público) ───────────────────────────────────

@router.post("/accept", response_model=AcceptInvitationResponse)
async def accept_invitation(
    accept_data: InvitationAcceptRequest,
    db: Session = Depends(get_db),
):
    """
    Acepta una invitación y crea el usuario.
    Uso: El usuario completa el formulario con su nombre y contraseña.
    """
    # Buscar invitación
    invitation = (
        db.query(Invitation)
        .filter(Invitation.token == accept_data.token)
        .first()
    )
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitación no encontrada.",
        )
    
    # Verificar si ya fue aceptada
    if invitation.is_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta invitación ya ha sido aceptada.",
        )
    
    # Verificar si expiró
    if invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta invitación ha expirado.",
        )
    
    # Verificar que el email coincida
    # Nota: En un sistema real, el email se verificaría antes de llegar aquí
    # through the frontend route
    
    # Hash de contraseña
    hashed_password = hash_password(accept_data.password)
    
    # Crear usuario
    try:
        new_user = User(
            full_name=accept_data.full_name,
            email=invitation.email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,  # Verificado por invitación
        )
        
        # Asignar rol
        if invitation.role_id:
            role = db.query(Role).filter(Role.id == invitation.role_id).first()
            if role:
                new_user.roles.append(role)
        
        db.add(new_user)
        db.flush()
        
        # Marcar invitación como aceptada
        invitation.is_accepted = True
        invitation.accepted_at = datetime.now(timezone.utc)
        invitation.accepted_by_email = invitation.email
        invitation.accepted_by_name = accept_data.full_name
        
        db.commit()
        
        # Registrar auditoría
        create_audit_log(
            db=db,
            user_id=None,  # Usuario aún no creado
            user_email=invitation.email,
            user_name=accept_data.full_name,
            action="invitation_accepted",
            category="invitations",
            target_type="invitation",
            target_id=str(invitation.id),
            target_display=f"Invitation to {invitation.email}",
            details={"user_id": new_user.id},
        )
        
        # Notificar al admin que creó la invitación
        if invitation.invited_by_id and invitation.invited_by_email:
            EmailService().send_admin_notification(
                admin_email=invitation.invited_by_email,
                user_name=accept_data.full_name,
                user_email=new_user.email,
            )
        
        # Crear token para login automático
        access_token = create_access_token(
            data={"sub": str(new_user.id), "email": new_user.email, "roles": new_user.get_role_names()}
        )
        
        return AcceptInvitationResponse(
            message="¡Bienvenido a MeteoPerú! Tu cuenta ha sido creada con éxito.",
            success=True,
            user_email=new_user.email,
            user_id=new_user.id,
            role_name=invitation.role_name or "user",
            token=access_token,
        )
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al aceptar la invitación: {str(e)}",
        )


# ─── Endpoint: Revocar invitación (admin) ─────────────────────────────────────

@router.delete("/{invitation_id}", response_model=MessageResponse)
async def revoke_invitation(
    invitation_id: int,
    current_user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """
    Revoca una invitación pendiente.
    """
    invitation = (
        db.query(Invitation)
        .filter(Invitation.id == invitation_id)
        .first()
    )
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitación no encontrada.",
        )
    
    if invitation.is_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede revocar una invitación ya aceptada.",
        )
    
    try:
        db.delete(invitation)
        db.commit()
        
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="invitation_revoked",
            category="invitations",
            target_type="invitation",
            target_id=str(invitation_id),
            target_display=f"Revoked invitation to {invitation.email}",
            details={},
        )
        
        return MessageResponse(message="Invitación revocada con éxito.")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al revocar la invitación: {str(e)}",
        )
