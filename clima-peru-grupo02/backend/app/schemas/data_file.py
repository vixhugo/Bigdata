"""
Schemas Pydantic para el sistema de archivo de datos (Big Data).
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FILE REQUESTS  ──────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class DataFileCreate(BaseModel):
    """Solicitud para crear un nuevo registro de archivo de datos."""
    filename: str
    label: str
    file_path: Optional[str] = None
    detected_city: Optional[str] = None
    department_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_records: int = 0


class DataFileUpdate(BaseModel):
    """Actualización parcial de un archivo de datos."""
    label: Optional[str] = None
    detected_city: Optional[str] = None
    department_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FILE RESPONSES  ─────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class DataFileResponse(BaseModel):
    """Respuesta con los detalles de un archivo de datos."""
    id: int
    filename: str
    label: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_type: str
    detected_city: Optional[str] = None
    department_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_records: int
    records_processed: int
    records_failed: int
    temp_average: Optional[float] = None
    temp_max: Optional[float] = None
    temp_min: Optional[float] = None
    precipitation_total: Optional[float] = None
    precipitation_max_single_day: Optional[float] = None
    rainy_days: Optional[int] = None
    wind_average: Optional[float] = None
    wind_max: Optional[float] = None
    uv_average: Optional[float] = None
    uv_max: Optional[float] = None
    status: str
    uploaded_by_email: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class DataFileListResponse(BaseModel):
    items: List[DataFileResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DataFileStatsResponse(BaseModel):
    """Estadísticas globales de archivos de datos."""
    total_files: int
    total_records: int
    total_size_bytes: int
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    cities_count: int
    departments_count: int
    completed_files: int
    pending_files: int
    failed_files: int


class DataFileRecordResponse(BaseModel):
    """Respuesta con los detalles de un registro de archivo de datos."""
    id: int
    data_file_id: int
    date: str
    temperature: Optional[float] = None
    temp_max: Optional[float] = None
    temp_min: Optional[float] = None
    humidity: Optional[float] = None
    precipitation: Optional[float] = None
    wind_speed: Optional[float] = None
    uv_index: Optional[float] = None
    weather_code: Optional[int] = None
    weather_description: Optional[str] = None
    city_name: Optional[str] = None
    department_name: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ImportResult(BaseModel):
    """Resultado de una importación de archivo."""
    success: bool
    message: str
    data_file_id: int
    total_records: int
    records_processed: int
    records_failed: int
    stats: Optional[dict] = None
