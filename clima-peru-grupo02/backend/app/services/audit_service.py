"""
Servicio de auditoría: registra eventos de seguridad y cambios administrativos.
"""
from __future__ import annotations
import json
from typing import Optional, Any

from sqlalchemy.orm import Session

from app.models.auth import AuditLog, User


class AuditService:

    # ─── Método principal ─────────────────────────────────────────────────────

    @staticmethod
    def log(
        db: Session,
        action: str,
        category: str = "general",
        user: Optional[User] = None,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        target_display: Optional[str] = None,
        details: Optional[Any] = None,
        status: str = "success",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Registra un evento de auditoría en la base de datos.

        Parámetros:
          action        — clave del evento (ej. "login", "user_created")
          category      — agrupación (ej. "auth", "users", "roles")
          user          — objeto User que ejecutó la acción (opcional)
          details       — dict/str con detalles adicionales (se serializa a JSON)
        """
        # Resolver datos del usuario desde el objeto o parámetros individuales
        resolved_user_id = user_id
        resolved_email = user_email
        resolved_name = user_name

        if user:
            resolved_user_id = resolved_user_id or user.id
            resolved_email = resolved_email or user.email
            resolved_name = resolved_name or user.full_name

        # Serializar details a JSON si es un dict/list
        details_str: Optional[str] = None
        if details is not None:
            if isinstance(details, (dict, list)):
                details_str = json.dumps(details, ensure_ascii=False, default=str)
            else:
                details_str = str(details)

        entry = AuditLog(
            user_id=resolved_user_id,
            user_email=resolved_email,
            user_name=resolved_name,
            action=action,
            category=category,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else None,
            target_display=target_display,
            details=details_str,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    # ─── Atajos por categoría ─────────────────────────────────────────────────

    @classmethod
    def log_login(
        cls, db: Session, user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        return cls.log(
            db, action="login", category="auth",
            user=user, status="success",
            ip_address=ip_address, user_agent=user_agent,
            details={"ip": ip_address}
        )

    @classmethod
    def log_login_failed(
        cls, db: Session, email: str,
        reason: str = "Credenciales inválidas",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        return cls.log(
            db, action="login_failed", category="auth",
            user_email=email, status="failure",
            ip_address=ip_address, user_agent=user_agent,
            details={"reason": reason, "email": email}
        )

    @classmethod
    def log_logout(
        cls, db: Session, user: User,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        return cls.log(
            db, action="logout", category="auth",
            user=user, status="success",
            ip_address=ip_address
        )

    @classmethod
    def log_register(
        cls, db: Session, new_user: User,
        created_by: Optional[User] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        return cls.log(
            db, action="user_registered", category="users",
            user=created_by, status="success",
            target_type="user", target_id=new_user.id,
            target_display=new_user.email,
            ip_address=ip_address,
            details={"new_user_email": new_user.email, "new_user_name": new_user.full_name}
        )

    @classmethod
    def log_user_created(
        cls, db: Session, new_user: User,
        created_by: User,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        return cls.log(
            db, action="user_created", category="users",
            user=created_by, status="success",
            target_type="user", target_id=new_user.id,
            target_display=new_user.email,
            ip_address=ip_address,
            details={
                "created_email": new_user.email,
                "created_name": new_user.full_name,
                "roles": new_user.get_role_names()
            }
        )

    @classmethod
    def log_user_updated(
        cls, db: Session, target_user: User,
        updated_by: User,
        changes: dict,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        return cls.log(
            db, action="user_updated", category="users",
            user=updated_by, status="success",
            target_type="user", target_id=target_user.id,
            target_display=target_user.email,
            ip_address=ip_address,
            details={"changes": changes}
        )

    @classmethod
    def log_user_deleted(
        cls, db: Session, target_user: User,
        deleted_by: User,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        return cls.log(
            db, action="user_deleted", category="users",
            user=deleted_by, status="success",
            target_type="user", target_id=target_user.id,
            target_display=target_user.email,
            ip_address=ip_address,
            details={"deleted_email": target_user.email, "deleted_name": target_user.full_name}
        )

    @classmethod
    def log_user_status_changed(
        cls, db: Session, target_user: User,
        changed_by: User, new_status: bool,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        action = "user_activated" if new_status else "user_deactivated"
        return cls.log(
            db, action=action, category="users",
            user=changed_by, status="success",
            target_type="user", target_id=target_user.id,
            target_display=target_user.email,
            ip_address=ip_address,
            details={"is_active": new_status}
        )

    @classmethod
    def log_password_changed(
        cls, db: Session, user: User,
        changed_by: Optional[User] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        actor = changed_by or user
        return cls.log(
            db, action="password_changed", category="auth",
            user=actor, status="success",
            target_type="user", target_id=user.id,
            target_display=user.email,
            ip_address=ip_address
        )

    @classmethod
    def log_password_reset_requested(
        cls, db: Session, email: str,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        return cls.log(
            db, action="password_reset_requested", category="auth",
            user_email=email, status="success",
            ip_address=ip_address,
            details={"email": email}
        )

    @classmethod
    def log_role_created(
        cls, db: Session, role_name: str, role_id: int,
        created_by: User,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        return cls.log(
            db, action="role_created", category="roles",
            user=created_by, status="success",
            target_type="role", target_id=role_id,
            target_display=role_name,
            ip_address=ip_address,
            details={"role_name": role_name}
        )

    @classmethod
    def log_role_updated(
        cls, db: Session, role_name: str, role_id: int,
        updated_by: User, changes: dict,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        return cls.log(
            db, action="role_updated", category="roles",
            user=updated_by, status="success",
            target_type="role", target_id=role_id,
            target_display=role_name,
            ip_address=ip_address,
            details={"changes": changes}
        )

    @classmethod
    def log_role_deleted(
        cls, db: Session, role_name: str, role_id: int,
        deleted_by: User,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        return cls.log(
            db, action="role_deleted", category="roles",
            user=deleted_by, status="success",
            target_type="role", target_id=role_id,
            target_display=role_name,
            ip_address=ip_address
        )

    @classmethod
    def log_role_assigned(
        cls, db: Session, target_user: User,
        role_names: list[str],
        assigned_by: User,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        return cls.log(
            db, action="roles_assigned", category="roles",
            user=assigned_by, status="success",
            target_type="user", target_id=target_user.id,
            target_display=target_user.email,
            ip_address=ip_address,
            details={"assigned_roles": role_names}
        )

    @classmethod
    def log_permissions_updated(
        cls, db: Session, role_name: str, role_id: int,
        updated_by: User, added: list[str], removed: list[str],
        ip_address: Optional[str] = None
    ) -> AuditLog:
        return cls.log(
            db, action="permissions_updated", category="permissions",
            user=updated_by, status="success",
            target_type="role", target_id=role_id,
            target_display=role_name,
            ip_address=ip_address,
            details={"added": added, "removed": removed}
        )


# ─── Atajo de función (no clase) para facilitar importaciones ─────────────────

def create_audit_log(
    db: Session,
    action: str,
    category: str = "general",
    user: Optional[User] = None,
    user_id: Optional[int] = None,
    user_email: Optional[str] = None,
    user_name: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    target_display: Optional[str] = None,
    details: Optional[Any] = None,
    status: str = "success",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Wrapper de AuditService.log para usar sin el prefijo de clase."""
    return AuditService.log(
        db, action=action, category=category,
        user=user, user_id=user_id, user_email=user_email, user_name=user_name,
        target_type=target_type, target_id=target_id, target_display=target_display,
        details=details, status=status,
        ip_address=ip_address, user_agent=user_agent
    )
