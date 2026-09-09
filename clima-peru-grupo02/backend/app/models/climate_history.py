"""
Modelos ORM para el sistema de Big Data del clima.
Tablas: climate_history
Almacena años de datos históricos del clima del Perú (sin necesidad de API).
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.peru_geo import City


class ClimateHistory(Base):
    """
    Datos históricos del clima por ciudad.
    Un registro por ciudad y día.
    
    Estructura:
    - 5 ciudades principales: Lima, Cusco, Arequipa, Iquitos, Trujillo
    - 365 días por año
    - 5+ años de datos (2020-2025)
    - Total: ~9,000 registros por ciudad
    """
    __tablename__ = "climate_history"

    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    
    # Fecha
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    
    # Clima actual (simil a CurrentWeather)
    temperature = Column(Float, nullable=False)
    apparent_temperature = Column(Float, nullable=False)
    relative_humidity = Column(Integer, nullable=False)
    wind_speed = Column(Float, nullable=False)
    wind_direction = Column(Integer, nullable=False)
    wind_gusts = Column(Float, nullable=True)
    surface_pressure = Column(Float, nullable=False)
    precipitation = Column(Float, nullable=False)
    precipitation_probability = Column(Integer, nullable=False)
    cloud_cover = Column(Integer, nullable=False)
    uv_index = Column(Float, nullable=False)
    uv_category = Column(String(20), nullable=False)
    weather_code = Column(Integer, nullable=False)
    weather_description = Column(String(100), nullable=False)
    weather_icon = Column(String(50), nullable=False)
    is_day = Column(Integer, nullable=False, default=1)
    
    # Rango diario
    temp_max = Column(Float, nullable=False)
    temp_min = Column(Float, nullable=False)
    sunrise = Column(String(8), nullable=True)
    sunset = Column(String(8), nullable=True)
    
    # Variables adicionales
    dew_point = Column(Float, nullable=True)
    visibility = Column(Float, nullable=True)
    epv = Column(Float, nullable=True)
    
    # Metadata
    source = Column(String(50), nullable=False, default="simulado")  # simulated, senami, historical
    data_file_id = Column(Integer, ForeignKey("data_files.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    city = relationship("City", back_populates="climate_history")


# ─── Definición de relaciones cruzadas (después de cargar todos los modelos) ─────
def define_climate_history_relationships():
    """Define la relación con DataFile después de que se cargue el modelo."""
    from app.models.data_file import DataFile
    if not hasattr(ClimateHistory, 'data_file'):
        ClimateHistory.data_file = relationship(
            "DataFile",
            back_populates="climate_records"
        )

