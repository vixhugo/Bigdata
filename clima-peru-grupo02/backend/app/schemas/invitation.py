"""
Schemas Pydantic para el sistema de invitaciones.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator
import re


# ═══════════════════════════════════════════════════════════════════════════════
# INVITATION REQUESTS  ─────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class InvitationCreate(BaseModel):
    """Solicitud para crear una nueva invitación."""
    email: EmailStr
    full_name: Optional[str] = None
    role_id: int
    message: Optional[str] = None
    expires_in_days: int = 7  # default: 7 días

    model_config = {"str_strip_whitespace": True}

    @field_validator("expires_in_days")
    @classmethod
    def validate_expires_in_days(cls, v: int) -> int:
        if v < 1 or v > 30:
            raise ValueError("La fecha de expiración debe estar entre 1 y 30 días.")
        return v


class InvitationAcceptRequest(BaseModel):
    """Solicitud para aceptar una invitación."""
    token: str
    full_name: str
    password: str
    confirm_password: str

    model_config = {"str_strip_whitespace": True}

    @field_validator("full_name")
    @classmethod
    def name_min_length(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres.")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una mayúscula.")
        if not re.search(r"[0-9]", v):
            raise ValueError("La contraseña debe contener al menos un número.")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        password = info.data.get("password")
        if password and v != password:
            raise ValueError("Las contraseñas no coinciden.")
        return v


# ═══════════════════════════════════════════════════════════════════════════════
# INVITATION RESPONSES  ────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class InvitationResponse(BaseModel):
    """Respuesta con los detalles de una invitación."""
    id: int
    email: str
    full_name: Optional[str] = None
    role_id: int
    role_name: Optional[str] = None
    token: str
    is_accepted: bool
    accepted_at: Optional[datetime] = None
    expires_at: datetime
    message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    invited_by_email: Optional[str] = None
    invited_by_name: Optional[str] = None

    model_config = {"from_attributes": True}


class InvitationListResponse(BaseModel):
    items: List[InvitationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class InvitationStatusResponse(BaseModel):
    """Respuesta al verificar estado de invitación."""
    token: str
    is_valid: bool
    is_expired: bool
    is_accepted: bool
    email: str
    full_name: Optional[str] = None
    role_id: int
    role_name: Optional[str] = None
    message: Optional[str] = None
    expires_at: datetime


class AcceptInvitationResponse(BaseModel):
    """Respuesta al aceptar una invitación."""
    message: str
    success: bool
    user_email: str
    user_id: int
    role_name: str
    token: str  # para login automático

