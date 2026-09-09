"""
Modelos ORM para el sistema de archivo de datos (Big Data).
Tablas: data_files, data_file_records
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class DataFile(Base):
    """Representa un archivo CSV importado con datos históricos del clima."""
    __tablename__ = "data_files"

    id = Column(Integer, primary_key=True, index=True)
    # Nombre original del archivo
    filename = Column(String(255), nullable=False)
    # Nombre descriptivo asignado por el usuario
    label = Column(String(255), nullable=False)
    
    # Archivo procesado
    file_path = Column(String(500), nullable=True)  # Ruta relativa al archivo
    file_size = Column(Integer, nullable=True)  # Tamaño en bytes
    file_type = Column(String(50), nullable=False, default="csv")
    
    # Ciudad/ubicación detectada
    detected_city = Column(String(100), nullable=True)
    department_name = Column(String(100), nullable=True)
    
    # Rango temporal
    start_date = Column(String(10), nullable=True)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=True)    # YYYY-MM-DD
    
    # Estadísticas de procesamiento
    total_records = Column(Integer, nullable=False, default=0)
    records_processed = Column(Integer, nullable=False, default=0)
    records_failed = Column(Integer, nullable=False, default=0)
    
    # Estadísticas de temperatura
    temp_average = Column(Float, nullable=True)
    temp_max = Column(Float, nullable=True)
    temp_min = Column(Float, nullable=True)
    
    # Estadísticas de precipitación
    precipitation_total = Column(Float, nullable=True)
    precipitation_max_single_day = Column(Float, nullable=True)
    rainy_days = Column(Integer, nullable=True)
    
    # Estadísticas de viento
    wind_average = Column(Float, nullable=True)
    wind_max = Column(Float, nullable=True)
    
    # Estadísticas de UV
    uv_average = Column(Float, nullable=True)
    uv_max = Column(Float, nullable=True)
    
    # Estado del procesamiento
    status = Column(String(20), nullable=False, default="pending")  # pending, processing, completed, failed
    
    # Metadatos
    uploaded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_by_email = Column(String(255), nullable=True)  # snapshot
    
    # Mensaje de error (si hubo fallo)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    # uploaded_by = relationship("User", foreign_keys=[uploaded_by_id], remote_side="User.id", back_populates="uploaded_data_files")
    records = relationship("DataFileRecord", back_populates="data_file", cascade="all, delete-orphan")

    # ── Helpers ──────────────────────────────────────────────────────────────
    def is_completed(self) -> bool:
        return self.status == "completed"
    
    def is_failed(self) -> bool:
        return self.status == "failed"
    
    def progress(self) -> float:
        if self.total_records == 0:
            return 100.0
        return (self.records_processed / self.total_records) * 100


class DataFileRecord(Base):
    """Un registro individual dentro de un archivo CSV importado."""
    __tablename__ = "data_file_records"

    id = Column(Integer, primary_key=True, index=True)
    data_file_id = Column(Integer, ForeignKey("data_files.id", ondelete="CASCADE"), nullable=False)
    
    # Datos meteorológicos
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    temperature = Column(Float, nullable=True)
    temp_max = Column(Float, nullable=True)
    temp_min = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    precipitation = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    uv_index = Column(Float, nullable=True)
    weather_code = Column(Integer, nullable=True)
    weather_description = Column(String(200), nullable=True)
    
    # metadata
    city_name = Column(String(100), nullable=True)
    department_name = Column(String(100), nullable=True)
    
    # Estado del procesamiento de este registro
    status = Column(String(20), nullable=False, default="pending")  # pending, processed, skipped, error
    
    # Mensaje de error (si hubo)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    data_file = relationship("DataFile", back_populates="records")


# ─── Definición de relaciones cruzadas (después de cargar todos los modelos) ─────
def define_data_file_relationships():
    """Define la relación con ClimateHistory después de que se cargue el modelo."""
    from app.models.climate_history import ClimateHistory
    if not hasattr(DataFile, 'climate_records'):
        DataFile.climate_records = relationship(
            "ClimateHistory",
            back_populates="data_file"
        )