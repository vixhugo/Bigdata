"""
Schemas Pydantic para el sistema de Big Data del clima.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# ═══════════════════════════════════════════════════════════════════════════════
# CLIMATE HISTORY SCHEMAS  ─────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class ClimateHistoryBase(BaseModel):
    """Base para ClimateHistory."""
    date: str
    temperature: float
    apparent_temperature: float
    relative_humidity: int
    wind_speed: float
    wind_direction: int
    wind_gusts: Optional[float] = None
    surface_pressure: float
    precipitation: float
    precipitation_probability: int
    cloud_cover: int
    uv_index: float
    uv_category: str
    weather_code: int
    weather_description: str
    weather_icon: str
    is_day: int
    temp_max: float
    temp_min: float
    sunrise: Optional[str] = None
    sunset: Optional[str] = None


class ClimateHistoryResponse(ClimateHistoryBase):
    """Respuesta con los detalles de un registro de clima histórico."""
    id: int
    city_id: int
    city_name: Optional[str] = None
    source: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ClimateHistoryListResponse(BaseModel):
    items: List[ClimateHistoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ClimateHistoryStatsResponse(BaseModel):
    """Estadísticas de clima histórico."""
    city_id: int
    city_name: str
    period_start: str
    period_end: str
    days_count: int
    
    # Estadísticas
    temp_avg: float
    temp_max: float
    temp_min: float
    temp_range: float
    
    precipitation_total: float
    precipitation_days: int
    precipitation_avg: float
    
    wind_avg: float
    wind_max: float
    
    uv_avg: float
    uv_max: float
    
    # Distribución
    sunny_days: int
    cloudy_days: int
    rainy_days: int
    
    # Rangos térmicos
    hot_days: int  # > 30°C
    warm_days: int  # 25-30°C
    mild_days: int  # 15-25°C
    cool_days: int  # 10-15°C
    cold_days: int  # < 10°C


class ClimateHistoryCompareResponse(BaseModel):
    """Comparación de clima histórico entre ciudades."""
    city1_name: str
    city2_name: str
    comparison_date: str
    temp_diff: float
    humidity_diff: float
    uv_diff: float
    wind_diff: float
    summary: str
