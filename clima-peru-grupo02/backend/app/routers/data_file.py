"""
Router para gestión de archivos de datos (Big Data).
Endpoints para importar, consultar y analizar datos históricos del clima.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

from app.database import get_db
from app.models.auth import User
from app.models.data_file import DataFile, DataFileRecord
from app.schemas.data_file import (
    DataFileCreate, DataFileResponse, DataFileListResponse, DataFileStatsResponse, ImportResult
)
from app.schemas.auth import MessageResponse
from app.routers.auth_deps import require_any_admin, get_current_user

router = APIRouter(prefix="/api/data-files", tags=["data-files"])


# ─── Endpoint: Subir archivo CSV (admin) ──────────────────────────────────────

@router.post("", response_model=ImportResult)
async def upload_data_file(
    file: UploadFile = File(..., description="Archivo CSV con datos meteorológicos"),
    label: str = Form(..., description="Nombre descriptivo para el archivo"),
    current_user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """
    Sube un archivo CSV con datos históricos del clima.
    El archivo debe tener las columnas: date, temperature, temp_max, temp_min, 
    humidity, precipitation, wind_speed, uv_index, weather_code, city, department.
    """
    import csv
    import io
    
    # Validar que sea un archivo CSV
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Por favor selecciona un archivo con formato .CSV",
        )
    
    # Leer el contenido del archivo
    try:
        contents = await file.read()
        decoded = contents.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe estar en formato UTF-8",
        )
    
    # Crear registro inicial del archivo
    data_file = DataFile(
        filename=file.filename,
        label=label,
        file_type="csv",
        uploaded_by_id=current_user.id,
        uploaded_by_email=current_user.email,
        total_records=0,
        records_processed=0,
        records_failed=0,
        status="pending",
    )
    db.add(data_file)
    db.commit()
    db.refresh(data_file)
    
    # Procesar el archivo CSV
    lines = decoded.splitlines()
    if len(lines) < 2:
        data_file.status = "failed"
        data_file.error_message = "El archivo CSV no contiene suficientes registros."
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo CSV no contiene suficientes registros.",
        )
    
    # Detectar delimitador
    first_line = lines[0]
    delimiter = ';' if ';' in first_line else ','
    
    # Procesar registros
    records_processed = 0
    records_failed = 0
    temps = []
    precipips = []
    winds = []
    uvs = []
    cities = set()
    departments = set()
    
    reader = csv.DictReader(lines, delimiter=delimiter)
    for row in reader:
        try:
            # Extraer datos
            temp = float(row.get('temperature', row.get('temp', '0')) or 0)
            temp_max = float(row.get('temp_max', row.get('max_temp', row.get('temperature_max', '0'))) or 0)
            temp_min = float(row.get('temp_min', row.get('min_temp', row.get('temperature_min', '0'))) or 0)
            humidity = float(row.get('humidity', '0') or 0)
            precipitation = float(row.get('precipitation', row.get('rain', '0')) or 0)
            wind_speed = float(row.get('wind_speed', row.get('wind', '0')) or 0)
            uv_index = float(row.get('uv_index', row.get('uv', '0')) or 0)
            
            # Guardar registro
            record = DataFileRecord(
                data_file_id=data_file.id,
                date=row.get('date', ''),
                temperature=temp,
                temp_max=temp_max,
                temp_min=temp_min,
                humidity=humidity,
                precipitation=precipitation,
                wind_speed=wind_speed,
                uv_index=uv_index,
                weather_code=int(row.get('weather_code', '0') or 0),
                weather_description=row.get('weather_description', row.get('condition', '')),
                city_name=row.get('city', row.get('city_name', '')),
                department_name=row.get('department', row.get('department_name', '')),
                status="processed",
            )
            db.add(record)
            records_processed += 1
            
            # Acumular estadísticas
            temps.append(temp)
            precipips.append(precipitation)
            winds.append(wind_speed)
            uvs.append(uv_index)
            
            city = row.get('city', row.get('city_name', ''))
            dept = row.get('department', row.get('department_name', ''))
            if city:
                cities.add(city)
            if dept:
                departments.add(dept)
            
        except (ValueError, KeyError) as e:
            records_failed += 1
            continue
    
    # Calcular estadísticas
    temp_avg = sum(temps) / len(temps) if temps else None
    temp_max_val = max(temps) if temps else None
    temp_min_val = min(temps) if temps else None
    precip_total = sum(precipips) if precipips else None
    precip_max = max(precipips) if precipips else None
    rainy_days = sum(1 for p in precipips if p > 0.1) if precipips else None
    wind_avg = sum(winds) / len(winds) if winds else None
    wind_max_val = max(winds) if winds else None
    uv_avg = sum(uvs) / len(uvs) if uvs else None
    uv_max_val = max(uvs) if uvs else None
    
    # Detectar ciudad y departamento principales
    detected_city = list(cities)[0] if cities else None
    detected_dept = list(departments)[0] if departments else None
    
    # Actualizar registro del archivo
    data_file.records_processed = records_processed
    data_file.records_failed = records_failed
    data_file.total_records = records_processed + records_failed
    data_file.temp_average = round(temp_avg, 2) if temp_avg else None
    data_file.temp_max = round(temp_max_val, 2) if temp_max_val else None
    data_file.temp_min = round(temp_min_val, 2) if temp_min_val else None
    data_file.precipitation_total = round(precip_total, 2) if precip_total else None
    data_file.precipitation_max_single_day = round(precip_max, 2) if precip_max else None
    data_file.rainy_days = rainy_days
    data_file.wind_average = round(wind_avg, 2) if wind_avg else None
    data_file.wind_max = round(wind_max_val, 2) if wind_max_val else None
    data_file.uv_average = round(uv_avg, 2) if uv_avg else None
    data_file.uv_max = round(uv_max_val, 2) if uv_max_val else None
    data_file.detected_city = detected_city
    data_file.department_name = detected_dept
    data_file.status = "completed"
    data_file.processed_at = datetime.now()
    db.commit()
    
    return ImportResult(
        success=True,
        message=f"Archivo procesado con éxito: {records_processed} registros importados",
        data_file_id=data_file.id,
        total_records=data_file.total_records,
        records_processed=records_processed,
        records_failed=records_failed,
        stats={
            "cities": list(cities),
            "departments": list(departments),
            "date_range": {
                "start": min((r.date for r in data_file.records), default=None),
                "end": max((r.date for r in data_file.records), default=None),
            },
        },
    )


# ─── Endpoint: Listar archivos de datos (admin) ───────────────────────────────

@router.get("", response_model=DataFileListResponse)
async def list_data_files(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """
    Lista todos los archivos de datos importados.
    """
    query = db.query(DataFile)
    
    if status_filter:
        query = query.filter(DataFile.status == status_filter)
    
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    
    data_files = (
        query.order_by(DataFile.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    return DataFileListResponse(
        items=data_files,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ─── Endpoint: Detalle de archivo de datos ────────────────────────────────────

@router.get("/{data_file_id}", response_model=DataFileResponse)
async def get_data_file(
    data_file_id: int,
    current_user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """
    Obtiene los detalles de un archivo de datos específico.
    """
    data_file = (
        db.query(DataFile)
        .filter(DataFile.id == data_file_id)
        .first()
    )
    
    if not data_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo de datos no encontrado.",
        )
    
    return data_file


# ─── Endpoint: Eliminar archivo de datos (admin) ──────────────────────────────

@router.delete("/{data_file_id}", response_model=MessageResponse)
async def delete_data_file(
    data_file_id: int,
    current_user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """
    Elimina un archivo de datos y todos sus registros asociados.
    """
    data_file = (
        db.query(DataFile)
        .filter(DataFile.id == data_file_id)
        .first()
    )
    
    if not data_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo de datos no encontrado.",
        )
    
    try:
        db.delete(data_file)
        db.commit()
        
        return MessageResponse(
            message="Archivo de datos eliminado con éxito."
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar el archivo: {str(e)}",
        )


# ─── Endpoint: Estadísticas globales ──────────────────────────────────────────

@router.get("/stats", response_model=DataFileStatsResponse)
async def get_data_file_stats(
    current_user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """
    Obtiene estadísticas globales de todos los archivos de datos.
    """
    total_files = db.query(DataFile).count()
    total_records = db.query(DataFile).with_entities(func.sum(DataFile.records_processed)).scalar() or 0
    total_size_bytes = db.query(DataFile).with_entities(func.sum(DataFile.file_size)).scalar() or 0
    
    cities_count = db.query(DataFile).with_entities(DataFile.detected_city).distinct().count()
    departments_count = db.query(DataFile).with_entities(DataFile.department_name).distinct().count()
    
    completed_files = db.query(DataFile).filter(DataFile.status == "completed").count()
    pending_files = db.query(DataFile).filter(DataFile.status == "pending").count()
    failed_files = db.query(DataFile).filter(DataFile.status == "failed").count()
    
    # Date range
    result = db.query(
        func.min(DataFile.start_date),
        func.max(DataFile.end_date)
    ).filter(DataFile.start_date.isnot(None)).first()
    
    return DataFileStatsResponse(
        total_files=total_files,
        total_records=total_records,
        total_size_bytes=total_size_bytes,
        date_range_start=result[0] if result else None,
        date_range_end=result[1] if result else None,
        cities_count=cities_count,
        departments_count=departments_count,
        completed_files=completed_files,
        pending_files=pending_files,
        failed_files=failed_files,
    )


# ─── Endpoint: Obtener registros de un archivo ────────────────────────────────

@router.get("/{data_file_id}/records", response_model=DataFileListResponse)
async def get_data_file_records(
    data_file_id: int,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(require_any_admin),
    db: Session = Depends(get_db),
):
    """
    Obtiene los registros de un archivo de datos específico.
    """
    data_file = (
        db.query(DataFile)
        .filter(DataFile.id == data_file_id)
        .first()
    )
    
    if not data_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo de datos no encontrado.",
        )
    
    query = db.query(DataFileRecord).filter(DataFileRecord.data_file_id == data_file_id)
    
    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    
    records = (
        query.order_by(DataFileRecord.date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    
    return DataFileListResponse(
        items=records,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
