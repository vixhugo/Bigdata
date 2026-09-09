"""
Router para consultas de datos climáticos históricos (Big Data).
 Sin uso de API externa - solo datos cargados localmente.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.peru_geo import City
from app.models.climate_history import ClimateHistory
from app.schemas.climate_history import (
    ClimateHistoryResponse, ClimateHistoryListResponse, 
    ClimateHistoryStatsResponse, ClimateHistoryCompareResponse
)

router = APIRouter(prefix="/api/climate", tags=["Big Data Climático"])


# ─── Endpoint: Obtener historial de una ciudad ────────────────────────────────

@router.get("/{city_id}", response_model=ClimateHistoryListResponse)
async def get_climate_history(
    city_id: int,
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """
    Obtiene el historial climático de una ciudad.
    """
    # Verificar ciudad
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ciudad con ID {city_id} no encontrada.",
        )
    
    # Construir query
    query = db.query(ClimateHistory).filter(ClimateHistory.city_id == city_id)
    
    if start_date:
        query = query.filter(ClimateHistory.date >= start_date)
    
    if end_date:
        query = query.filter(ClimateHistory.date <= end_date)
    
    # Total
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    
    # Obtener registros
    records = (
        query.order_by(ClimateHistory.date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    return ClimateHistoryListResponse(
        items=records,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ─── Endpoint: Estadísticas de clima histórico ────────────────────────────────

@router.get("/{city_id}/stats", response_model=ClimateHistoryStatsResponse)
async def get_climate_stats(
    city_id: int,
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    Obtiene estadísticas completas del historial climático de una ciudad.
    """
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ciudad con ID {city_id} no encontrada.",
        )
    
    query = db.query(ClimateHistory).filter(ClimateHistory.city_id == city_id)
    
    if start_date:
        query = query.filter(ClimateHistory.date >= start_date)
    
    if end_date:
        query = query.filter(ClimateHistory.date <= end_date)
    
    records = query.all()
    
    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron datos para la ciudad en el período especificado.",
        )
    
    # Calcular estadísticas
    temps = [r.temperature for r in records]
    max_temps = [r.temp_max for r in records]
    min_temps = [r.temp_min for r in records]
    precip = [r.precipitation for r in records]
    winds = [r.wind_speed for r in records]
    uvs = [r.uv_index for r in records]
    
    temp_avg = sum(temps) / len(temps)
    temp_max_val = max(max_temps)
    temp_min_val = min(min_temps)
    temp_range = temp_max_val - temp_min_val
    
    precip_total = sum(precip)
    precip_days = sum(1 for p in precip if p > 0.1)
    precip_avg = precip_total / len(precip) if precip else 0
    
    wind_avg = sum(winds) / len(winds) if winds else 0
    wind_max_val = max(winds) if winds else 0
    
    uv_avg = sum(uvs) / len(uvs) if uvs else 0
    uv_max_val = max(uvs) if uvs else 0
    
    # Distribución por condiciones
    sunny = sum(1 for r in records if r.weather_code == 0 and r.cloud_cover < 20)
    cloudy = sum(1 for r in records if r.cloud_cover > 60)
    rainy = sum(1 for r in records if r.precipitation > 0.5)
    
    # Rangos térmicos
    hot = sum(1 for t in temps if t > 30)
    warm = sum(1 for t in temps if 25 <= t <= 30)
    mild = sum(1 for t in temps if 15 <= t < 25)
    cool = sum(1 for t in temps if 10 <= t < 15)
    cold = sum(1 for t in temps if t < 10)
    
    return ClimateHistoryStatsResponse(
        city_id=city.id,
        city_name=city.name,
        period_start=min(r.date for r in records),
        period_end=max(r.date for r in records),
        days_count=len(records),
        temp_avg=round(temp_avg, 2),
        temp_max=round(temp_max_val, 2),
        temp_min=round(temp_min_val, 2),
        temp_range=round(temp_range, 2),
        precipitation_total=round(precip_total, 2),
        precipitation_days=precip_days,
        precipitation_avg=round(precip_avg, 2),
        wind_avg=round(wind_avg, 2),
        wind_max=round(wind_max_val, 2),
        uv_avg=round(uv_avg, 2),
        uv_max=round(uv_max_val, 2),
        sunny_days=sunny,
        cloudy_days=cloudy,
        rainy_days=rainy,
        hot_days=hot,
        warm_days=warm,
        mild_days=mild,
        cool_days=cool,
        cold_days=cold,
    )


# ─── Endpoint: Comparar clima entre ciudades ──────────────────────────────────

@router.get("/compare/{city_id1}/{city_id2}", response_model=ClimateHistoryCompareResponse)
async def compare_climate(
    city_id1: int,
    city_id2: int,
    comparison_date: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    Compara el clima de dos ciudades en una fecha específica.
    """
    city1 = db.query(City).filter(City.id == city_id1).first()
    city2 = db.query(City).filter(City.id == city_id2).first()
    
    if not city1 or not city2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Una o ambas ciudades no fueron encontradas.",
        )
    
    record1 = db.query(ClimateHistory).filter(
        ClimateHistory.city_id == city_id1,
        ClimateHistory.date == comparison_date
    ).first()
    
    record2 = db.query(ClimateHistory).filter(
        ClimateHistory.city_id == city_id2,
        ClimateHistory.date == comparison_date
    ).first()
    
    if not record1 or not record2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron datos para las ciudades en la fecha especificada.",
        )
    
    temp_diff = round(record1.temperature - record2.temperature, 1)
    humidity_diff = round(record1.relative_humidity - record2.relative_humidity)
    uv_diff = round(record1.uv_index - record2.uv_index, 1)
    wind_diff = round(record1.wind_speed - record2.wind_speed, 1)
    
    # Generar resumen
    if temp_diff > 5:
        summary = f"{city1.name} está {abs(temp_diff)}��C más cálido que {city2.name}"
    elif temp_diff < -5:
        summary = f"{city2.name} está {abs(temp_diff)}°C más cálido que {city1.name}"
    else:
        summary = f"Ambas ciudades tienen temperaturas similares ({temp_diff:+.1f}°C de diferencia)"
    
    return ClimateHistoryCompareResponse(
        city1_name=city1.name,
        city2_name=city2.name,
        comparison_date=comparison_date,
        temp_diff=temp_diff,
        humidity_diff=humidity_diff,
        uv_diff=uv_diff,
        wind_diff=wind_diff,
        summary=summary,
    )


# ─── Endpoint: Resumen mensual de una ciudad ──────────────────────────────────

@router.get("/{city_id}/monthly/{year}/{month}", response_model=ClimateHistoryStatsResponse)
async def get_monthly_summary(
    city_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene un resumen mensual del clima de una ciudad.
    """
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ciudad con ID {city_id} no encontrada.",
        )
    
    start_date = f"{year}-{str(month).zfill(2)}-01"
    if month == 12:
        end_date = f"{year}-12-31"
    else:
        end_date = f"{year}-{str(month + 1).zfill(2)}-01"
    
    return await get_climate_stats(city_id, start_date, end_date, db)


# ─── Endpoint: Listar ciudades con datos históricos ───────────────────────────

@router.get("/cities", response_model=ClimateHistoryListResponse)
async def list_cities_with_climate(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Lista todas las ciudades que tienen datos históricos disponibles.
    """
    # Obtener ciudades únicas con datos
    subquery = (
        db.query(ClimateHistory.city_id)
        .distinct()
        .subquery()
    )
    
    cities = db.query(City).filter(City.id.in_(subquery)).all()
    
    total = len(cities)
    total_pages = (total + page_size - 1) // page_size
    
    # Retornar ciudades con datos
    items = [
        ClimateHistoryResponse(
            id=c.id,
            city_id=c.id,
            city_name=c.name,
            date="N/A",
            temperature=0,
            apparent_temperature=0,
            relative_humidity=0,
            wind_speed=0,
            wind_direction=0,
            surface_pressure=0,
            precipitation=0,
            precipitation_probability=0,
            cloud_cover=0,
            uv_index=0,
            uv_category="",
            weather_code=0,
            weather_description="",
            weather_icon="",
            is_day=0,
            temp_max=0,
            temp_min=0,
            source="Historical Data",
        )
        for c in cities
    ]
    
    return ClimateHistoryListResponse(
        items=items[:page_size],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ─── Endpoint: Obtener datos más recientes de todas las ciudades ──────────────

@router.get("/latest", response_model=ClimateHistoryListResponse)
async def get_latest_climate_data(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Obtiene los datos climáticos más recientes de cada ciudad.
    Útil para mostrar un resumen actual del clima nacional.
    """
    # Subquery para obtener el último registro por ciudad
    from sqlalchemy import func, desc
    
    latest_subquery = (
        db.query(
            ClimateHistory.city_id,
            func.max(ClimateHistory.date).label('latest_date')
        )
        .group_by(ClimateHistory.city_id)
        .subquery()
    )
    
    records = (
        db.query(ClimateHistory)
        .join(latest_subquery, 
              (ClimateHistory.city_id == latest_subquery.c.city_id) &
              (ClimateHistory.date == latest_subquery.c.latest_date))
        .order_by(ClimateHistory.date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    total = db.query(ClimateHistory.city_id).distinct().count()
    total_pages = (total + page_size - 1) // page_size
    
    return ClimateHistoryListResponse(
        items=records,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
