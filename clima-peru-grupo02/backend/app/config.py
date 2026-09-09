"""
Configuración centralizada de MeteoPerú.
"""
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Configuración del servidor FastAPI."""
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
    )

    APP_ENV: str = Field(default="development")

    # Proyecto
    PROJECT_NAME: str = "MeteoPerú"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # Base de datos
    DATABASE_URL: str = Field(
        default="sqlite:///./clima_peru.db",
        description="URL de conexión a la base de datos"
    )
    DATABASE_ECHO: bool = Field(default=False)

    # JWT
    JWT_SECRET_KEY: str = Field(
        default=os.getenv("JWT_SECRET_KEY", "c1ima-peru-jwt-secret-!CHANGE-IN-PROD!-"),
        description="Clave secreta para JWT (usar variable de entorno en producción)"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)

    # Servidor
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=8000)
    RELOAD: bool = Field(default=True)

    # API Meteorológica (Open-Meteo)
    OPEN_METEO_API_BASE: str = "https://api.open-meteo.com/v1"

    # Notificaciones por correo (opcional)
    SMTP_HOST: str = Field(default="", description="Servidor SMTP (ej. smtp.gmail.com)")
    SMTP_PORT: int = Field(default=587, description="Puerto SMTP")
    SMTP_USER: str = Field(default="", description="Usuario SMTP")
    SMTP_PASSWORD: str = Field(default="", description="Contraseña SMTP")
    SMTP_FROM_EMAIL: str = Field(default="", description="Email remitente")

    # URL del frontend (para enlaces en emails)
    FRONTEND_URL: str = Field(default="http://localhost:5173")


settings = Settings()
