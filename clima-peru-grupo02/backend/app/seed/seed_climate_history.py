"""
Seed de datos históricos del clima del Perú (Big Data).
Genera datos sintéticos realistas para 5 ciudades principales.
2020-2025 (6 años × 365 días = ~2,190 registros por ciudad)
"""
from __future__ import annotations
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy.orm import Session

from app.models.peru_geo import City
from app.models.climate_history import ClimateHistory


# Definición de ciudades con perfiles climáticos
CITY_PROFILES = {
    "Lima": {
        "region": "Costa",
        "base_temp": 21.0,
        "temp_var": 3.0,
        "humidity": 78,
        "humidity_var": 10,
        "rain_days": 5,  # días con lluvia al año
        "uv_base": 7.0,
        "wind_base": 14.0,
    },
    "Cusco": {
        "region": "Sierra",
        "base_temp": 13.5,
        "temp_var": 12.0,  # grande diferencia día/noche
        "humidity": 58,
        "humidity_var": 15,
        "rain_days": 45,
        "uv_base": 10.0,  # más UV por altitud
        "wind_base": 11.0,
    },
    "Arequipa": {
        "region": "Sierra",
        "base_temp": 15.0,
        "temp_var": 10.0,
        "humidity": 45,
        "humidity_var": 12,
        "rain_days": 15,
        "uv_base": 9.5,
        "wind_base": 12.0,
    },
    "Iquitos": {
        "region": "Selva",
        "base_temp": 28.0,
        "temp_var": 3.0,
        "humidity": 88,
        "humidity_var": 8,
        "rain_days": 120,  # mucha lluvia en selva
        "uv_base": 8.5,
        "wind_base": 9.0,
    },
    "Trujillo": {
        "region": "Costa",
        "base_temp": 23.0,
        "temp_var": 4.0,
        "humidity": 75,
        "humidity_var": 12,
        "rain_days": 3,
        "uv_base": 8.0,
        "wind_base": 16.0,
    },
}

WMO_CODES = {
    "despejado": 0,
    "parcialmente_nublado": 1,
    "nublado": 3,
    "lluvia_ligera": 61,
    "lluvia_moderada": 63,
    "lluvia_fuerte": 65,
    "tormenta": 95,
    "neblina": 45,
}


def get_weather_icon(code: int, is_day: bool) -> str:
    icons = {
        0: "Sun" if is_day else "Moon",
        1: "SunMedium" if is_day else "Moon",
        2: "CloudSun" if is_day else "CloudMoon",
        3: "Cloud",
        45: "CloudFog",
        61: "CloudRain",
        63: "CloudRain",
        65: "CloudRainWind",
        95: "CloudLightning",
    }
    return icons.get(code, "Sun" if is_day else "Moon")


def get_weather_desc(code: int) -> str:
    desc = {
        0: "Cielo despejado",
        1: "Mayormente despejado",
        2: "Parcialmente nublado",
        3: "Nublado",
        45: "Neblina",
        61: "Lluvia ligera",
        63: "Lluvia moderada",
        65: "Lluvia fuerte",
        95: "Tormenta eléctrica",
    }
    return desc.get(code, "Cielo despejado")


def get_uv_category(uv: float) -> str:
    if uv < 3.0:
        return "Bajo"
    elif uv < 6.0:
        return "Moderado"
    elif uv < 8.0:
        return "Alto"
    elif uv < 11.0:
        return "Muy Alto"
    return "Extremo"


def generate_climate_data(
    city_id: int,
    city_name: str,
    profile: Dict[str, Any],
    start_year: int = 2020,
    end_year: int = 2025,
) -> List[ClimateHistory]:
    """Genera datos climáticos históricos sintéticos."""
    records = []
    
    base_temp = profile["base_temp"]
    temp_var = profile["temp_var"]
    base_humidity = profile["humidity"]
    base_uv = profile["uv_base"]
    base_wind = profile["wind_base"]
    
    # Generar datos por año y día
    for year in range(start_year, end_year + 1):
        for day_of_year in range(1, 366):
            # Calcular fecha
            try:
                date = datetime(year, 1, 1) + timedelta(days=day_of_year - 1)
            except ValueError:
                continue  # saltar 29 de feb en años no bisiestos
            
            date_str = date.strftime("%Y-%m-%d")
            
            # Variación estacional (sinusoidal)
            day_num = day_of_year
            seasonal_var = math.sin(day_num * 2 * math.pi / 365) * (temp_var / 2)
            
            # Variación diaria
            diurnal_var = math.sin(day_num * 0.01) * (temp_var / 3)
            
            # Temperature
            temp_mean = base_temp + seasonal_var + (random.gauss(0, 0.5))
            temp_max = temp_mean + temp_var / 2 + random.gauss(0, 0.3)
            temp_min = temp_mean - temp_var / 2 - random.gauss(0, 0.3)
            
            # Humedad
            humidity = base_humidity + seasonal_var * 2 + random.randint(-5, 5)
            humidity = max(20, min(98, int(humidity)))
            
            # Viento
            wind = base_wind + random.gauss(0, 2)
            wind = max(2, round(wind, 1))
            
            # UV
            uv = base_uv + seasonal_var * 0.5 + random.gauss(0, 0.3)
            uv = max(1.0, min(12.0, round(uv, 1)))
            
            # Precipitación (solo en ciertos días)
            if city_name == "Iquitos":
                # En selva, lluvia más frecuente
                is_rainy = random.random() < 0.3
            elif city_name == "Cusco":
                # En sierra, temporada de lluvias dic-mar
                is_rainy = day_of_year in range(335, 367) or day_of_year in range(1, 60)
                is_rainy = is_rainy and random.random() < 0.4
            else:
                # En costa, muy poco lluvia
                is_rainy = random.random() < (profile["rain_days"] / 365)
            
            if is_rainy:
                precipitation = round(random.uniform(1.0, 15.0), 1)
                rain_prob = random.randint(70, 95)
                cloud_cover = random.randint(60, 95)
                weather_code = random.choice([61, 63, 65, 95])
            else:
                precipitation = round(random.uniform(0.0, 0.5), 1)
                rain_prob = random.randint(5, 25)
                cloud_cover = random.randint(0, 30)
                weather_code = 0 if cloud_cover < 15 else (1 if cloud_cover < 40 else 2)
            
            # Otras variables
            surface_pressure = round(1013 + random.gauss(0, 3), 1)
            wind_direction = random.randint(0, 359)
            wind_gusts = round(wind + random.uniform(0, 5), 1) if random.random() > 0.5 else None
            is_day = 1
            sunrise = "06:15" if day_num < 180 else "06:30"
            sunset = "18:30" if day_num < 180 else "18:15"
            
            # Dew point
            dew_point = round(temp_mean - (100 - humidity) / 5, 1)
            
            record = ClimateHistory(
                city_id=city_id,
                date=date_str,
                temperature=round(temp_mean, 1),
                apparent_temperature=round(temp_mean + random.gauss(0, 1), 1),
                relative_humidity=humidity,
                wind_speed=wind,
                wind_direction=wind_direction,
                wind_gusts=wind_gusts,
                surface_pressure=surface_pressure,
                precipitation=precipitation,
                precipitation_probability=rain_prob,
                cloud_cover=cloud_cover,
                uv_index=uv,
                uv_category=get_uv_category(uv),
                weather_code=weather_code,
                weather_description=get_weather_desc(weather_code),
                weather_icon=get_weather_icon(weather_code, is_day),
                is_day=is_day,
                temp_max=round(temp_max, 1),
                temp_min=round(temp_min, 1),
                sunrise=sunrise,
                sunset=sunset,
                dew_point=dew_point,
                visibility=round(random.uniform(8.0, 20.0), 1),
                epv=round(random.uniform(500, 1200), 0),
                source="simulado",
            )
            records.append(record)
    
    return records


def seed_climate_history(db: Session) -> None:
    """Sembrar datos históricos del clima para las ciudades principales."""
    
    # Obtener ciudades
    cities = db.query(City).filter(City.name.in_(CITY_PROFILES.keys())).all()
    
    if not cities:
        print("❌ No se encontraron ciudades para generar datos históricos.")
        return

    existing_records = db.query(ClimateHistory).count()
    if existing_records > 0:
        print(f"✔ Historial climático ya disponible ({existing_records} registros).")
        return
    
    total_created = 0
    
    for city in cities:
        profile = CITY_PROFILES.get(city.name)
        if not profile:
            continue
        
        print(f"🌱 Generando datos históricos para {city.name}...")
        
        # Eliminar datos existentes para esta ciudad
        db.query(ClimateHistory).filter(ClimateHistory.city_id == city.id).delete()
        
        # Generar datos
        records = generate_climate_data(city.id, city.name, profile)
        
        # Insertar en lotes
        batch_size = 500
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            db.bulk_save_objects(batch)
            db.commit()
        
        total_created += len(records)
        print(f"   ✅ {len(records)} registros generados para {city.name}")
    
    print(f"\n✅ Total: {total_created} registros de clima histórico generados")
    print(f"   Período: 2020-2025")
    print(f"   Ciudades: {len(cities)}")
