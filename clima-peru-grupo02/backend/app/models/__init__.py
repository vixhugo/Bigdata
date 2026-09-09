from app.models.peru_geo import Department, City
from app.models.weather_cache import WeatherCache
from app.models.favorite import FavoriteCity
from app.models.auth import Permission, Role, User, AuditLog
from app.models.invitation import Invitation
from app.models.data_file import DataFile, DataFileRecord, define_data_file_relationships
from app.models.climate_history import ClimateHistory, define_climate_history_relationships

# ─── Relaciones cruzadas (después de definir todas las clases) ───────────────
# Resuelven importaciones circulares definidas en clases
define_data_file_relationships()
define_climate_history_relationships()

# User → sent_invitations (resuelto en invitation.py con remote_side)
# User → uploaded_data_files (quitar para evitar circularidad)

# DataFile → uploaded_by (quitar para evitar circularidad)

__all__ = [
    "Department", "City", "WeatherCache", "FavoriteCity",
    "Permission", "Role", "User", "AuditLog", "Invitation",
    "DataFile", "DataFileRecord", "ClimateHistory",
]
