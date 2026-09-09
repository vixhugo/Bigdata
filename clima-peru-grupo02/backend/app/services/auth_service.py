"""
Servicio de autenticación: hashing, JWT, login, registro, recuperación de contraseña.
Bloqueo temporal tras múltiples intentos fallidos.
"""
from __future__ import annotations
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models.auth import User, Role, Permission
from app.schemas.auth import (
    RegisterRequest, LoginRequest,
    TokenResponse, TokenData, UserResponse
)

# ─── Configuración criptográfica ──────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT — usa variable de entorno o clave generada (solo desarrollo)
SECRET_KEY: str = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES

if settings.APP_ENV.lower() in {"production", "prod"} and "CHANGE-IN-PROD" in SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY debe configurarse antes de iniciar en producción.")

# Política de bloqueo
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


# ─── Helpers de contraseña ────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ─── Helpers de JWT ───────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        email: str = payload.get("email", "")
        roles: list[str] = payload.get("roles", [])
        if user_id is None:
            return None
        return TokenData(user_id=int(user_id), email=email, roles=roles)
    except JWTError:
        return None


def _build_token_response(user: User) -> TokenResponse:
    expire_seconds = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "roles": user.get_role_names(),
    })
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expire_seconds,
    )


# ─── Helpers de recuperación ──────────────────────────────────────────────────

def _generate_reset_token(length: int = 48) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# ═══════════════════════════════════════════════════════════════════════════════
# AuthService
# ═══════════════════════════════════════════════════════════════════════════════

class AuthService:

    # ── Registro ──────────────────────────────────────────────────────────────

    @staticmethod
    def register(payload: RegisterRequest, db: Session) -> User:
        """Crea un nuevo usuario y le asigna el rol 'user' por defecto."""
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise ValueError("Ya existe una cuenta con ese correo electrónico.")

        user = User(
            full_name=payload.full_name,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            is_active=True,
            is_verified=False,
        )

        # Asignar rol 'user' por defecto
        default_role = db.query(Role).filter(Role.name == "user").first()
        if default_role:
            user.roles.append(default_role)

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    # ── Login ─────────────────────────────────────────────────────────────────

    @staticmethod
    def login(
        payload: LoginRequest,
        db: Session,
        ip_address: Optional[str] = None
    ) -> tuple[TokenResponse, User]:
        """
        Autentica al usuario. Lanza ValueError con el motivo en caso de fallo.
        Retorna (TokenResponse, User) en caso de éxito.
        """
        user = db.query(User).filter(User.email == payload.email).first()

        # Usuario no existe
        if not user:
            raise ValueError("Correo o contraseña incorrectos.")

        # Cuenta desactivada
        if not user.is_active:
            raise ValueError("Tu cuenta ha sido desactivada. Contacta al administrador.")

        # Bloqueo temporal
        now = datetime.now(timezone.utc)
        if user.locked_until:
            locked_until_aware = user.locked_until.replace(tzinfo=timezone.utc) if user.locked_until.tzinfo is None else user.locked_until
            if now < locked_until_aware:
                remaining = int((locked_until_aware - now).total_seconds() // 60) + 1
                raise ValueError(
                    f"Cuenta bloqueada temporalmente. Intenta en {remaining} minuto(s)."
                )
            else:
                # Limpiar bloqueo expirado
                user.failed_login_attempts = 0
                user.locked_until = None

        # Verificar contraseña
        if not verify_password(payload.password, user.hashed_password):
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
                db.commit()
                raise ValueError(
                    f"Demasiados intentos fallidos. Cuenta bloqueada por {LOCKOUT_MINUTES} minutos."
                )
            db.commit()
            remaining_attempts = MAX_FAILED_ATTEMPTS - user.failed_login_attempts
            raise ValueError(
                f"Correo o contraseña incorrectos. Te quedan {remaining_attempts} intento(s)."
            )

        # Login exitoso — resetear contadores
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = now
        user.last_login_ip = ip_address
        db.commit()
        db.refresh(user)

        return _build_token_response(user), user

    # ── Recuperación de contraseña ────────────────────────────────────────────

    @staticmethod
    def request_password_reset(email: str, db: Session) -> Optional[str]:
        """
        Genera y guarda un token de recuperación.
        Retorna el token (para enviarlo por email o mostrarlo en dev).
        Retorna None si el email no existe (no se revela al cliente).
        """
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None  # silencioso por seguridad

        token = _generate_reset_token()
        user.password_reset_token = hash_password(token)
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=2)
        db.commit()
        return token  # en producción se enviaría por email

    @staticmethod
    def reset_password(token: str, new_password: str, db: Session) -> bool:
        """Valida el token y actualiza la contraseña."""
        # Buscar usuarios con token activo
        now = datetime.now(timezone.utc)
        users_with_token = (
            db.query(User)
            .filter(User.password_reset_token.isnot(None))
            .all()
        )
        target_user = None
        for u in users_with_token:
            if u.password_reset_expires:
                expires_aware = u.password_reset_expires.replace(tzinfo=timezone.utc) if u.password_reset_expires.tzinfo is None else u.password_reset_expires
                if now < expires_aware and verify_password(token, u.password_reset_token):
                    target_user = u
                    break

        if not target_user:
            return False

        target_user.hashed_password = hash_password(new_password)
        target_user.password_reset_token = None
        target_user.password_reset_expires = None
        target_user.failed_login_attempts = 0
        target_user.locked_until = None
        db.commit()
        return True

    # ── Cambio de contraseña (usuario autenticado) ────────────────────────────

    @staticmethod
    def change_password(
        user: User,
        current_password: str,
        new_password: str,
        db: Session
    ) -> bool:
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("La contraseña actual es incorrecta.")
        user.hashed_password = hash_password(new_password)
        db.commit()
        return True

    # ── Obtener usuario por token ─────────────────────────────────────────────

    @staticmethod
    def get_user_from_token(token: str, db: Session) -> Optional[User]:
        token_data = decode_access_token(token)
        if not token_data:
            return None
        return db.query(User).filter(User.id == token_data.user_id).first()

    # ── Construir UserResponse ────────────────────────────────────────────────

    @staticmethod
    def build_user_response(user: User) -> UserResponse:
        perms = user.get_all_permissions()
        return UserResponse(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
            is_verified=user.is_verified,
            avatar_url=user.avatar_url,
            last_login=user.last_login,
            last_login_ip=user.last_login_ip,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=user.roles,
            permissions=list(perms),
        )
