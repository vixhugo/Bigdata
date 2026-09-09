"""
Modelos ORM para el sistema de invitaciones estilo GitHub.
Tabla: invitations
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Invitation(Base):
    """Invitación para unirse al sistema (estilo GitHub)."""
    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, index=True)
    # Usuario que envió la invitación (admin)
    invited_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    invited_by_email = Column(String(255), nullable=True)  # snapshot
    
    # Usuario receptor (el que recibe la invitación)
    email = Column(String(255), nullable=False, index=True)
    full_name = Column(String(200), nullable=True)
    
    # Token único de invitación
    token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Rol que se asignará al usuario al aceptar
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    role_name = Column(String(80), nullable=True)  # snapshot
    
    # Estado de la invitación
    is_accepted = Column(Boolean, default=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    accepted_by_email = Column(String(255), nullable=True)  # snapshot
    accepted_by_name = Column(String(200), nullable=True)   # snapshot
    
    # Caducidad
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Mensaje personalizado (opcional)
    message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ── Helpers ──────────────────────────────────────────────────────────────
    def is_expired(self) -> bool:
        """Verifica si la invitación ha expirado."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return self.expires_at < now

    def is_valid(self) -> bool:
        """Verifica si la invitación es válida (no expirada y no aceptada)."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return not self.is_accepted and self.expires_at > now
