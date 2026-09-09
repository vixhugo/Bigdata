from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from app.config import settings
from app.database import Base, engine
from app.seed.seed_data import init_db_and_seed
from app.seed.seed_auth import seed_auth
from app.database import SessionLocal

# ─── Routers meteorológicos ────────────────────────────────────────────────────
from app.routers import (
    weather,
    cities,
    departments,
    alerts,
    compare,
    history,
    rankings,
    export,
    favorites,
)

# ─── Routers de autenticación y administración ─────────────────────────────────
from app.routers import auth as auth_router
from app.routers.users_admin import router as users_admin_router
from app.routers.roles_admin import router as roles_admin_router
from app.routers.audit_admin import router as audit_admin_router
from app.routers.admin_dashboard import router as admin_dashboard_router
from app.routers.invitations import router as invitations_router
from app.routers.data_file import router as data_file_router
from app.routers.climate_history import router as climate_history_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("VERCEL") == "1":
        yield
        return

    # 1. Crear tablas y sembrar datos geográficos del Perú
    init_db_and_seed()
    # 2. Sembrar roles, permisos y super admin
    db = SessionLocal()
    try:
        seed_auth(db)
        # 3. Sembrar datos históricos del clima (Big Data)
        from app.seed.seed_climate_history import seed_climate_history
        seed_climate_history(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "API REST para el Sistema Web de Clima y Datos Meteorológicos del Perú. "
        "Integra Open-Meteo, catálogos geográficos del Perú, pronósticos, comparador, "
        "análisis histórico, alertas climáticas, autenticación JWT y panel de administración RBAC."
    ),
    lifespan=lifespan,
)

# ─── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers meteorológicos (doble prefijo para compatibilidad serverless) ─────
for prefix in [settings.API_V1_STR, ""]:
    app.include_router(weather.router, prefix=prefix)
    app.include_router(cities.router, prefix=prefix)
    app.include_router(departments.router, prefix=prefix)
    app.include_router(alerts.router, prefix=prefix)
    app.include_router(compare.router, prefix=prefix)
    app.include_router(history.router, prefix=prefix)
    app.include_router(rankings.router, prefix=prefix)
    app.include_router(export.router, prefix=prefix)
    app.include_router(favorites.router, prefix=prefix)

# ─── Routers de autenticación y administración ─────────────────────────────────
for prefix in [settings.API_V1_STR, ""]:
    app.include_router(auth_router.router, prefix=prefix)
    app.include_router(users_admin_router, prefix=prefix)
    app.include_router(roles_admin_router, prefix=prefix)
    app.include_router(audit_admin_router, prefix=prefix)
    app.include_router(admin_dashboard_router, prefix=prefix)
    app.include_router(invitations_router, prefix=prefix)
    app.include_router(data_file_router, prefix=prefix)
    app.include_router(climate_history_router, prefix=prefix)


# ─── Rutas base ────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "system": "Sistema Meteorológico del Perú",
        "status": "Online",
        "docs": "/docs",
        "version": settings.VERSION,
    }


@app.get("/api/health")
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "clima-peru-api"}
