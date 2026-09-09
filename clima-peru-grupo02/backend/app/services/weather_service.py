"""
Servicio de clima actualizado para Big Data.
Prioriza datos cargados localmente, con fallback a simulación si no hay datos.
Elimina dependencia de API Open-Meteo para datos históricos.
"""
import json
import httpx
import random
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.config import settings
from app.models.peru_geo import City, Department
from app.schemas.weather import (
    CurrentWeather, HourlyForecastItem, DailyForecastItem,
    FullForecastResponse, DepartmentWeatherSummary
)
from app.schemas.history import HistoryResponse, HistoryStats, HistoryDataPoint

# WMO Weather interpretation codes (WW)
WMO_CODES: Dict[int, Dict[str, str]] = {
    0: {"desc": "Cielo despejado", "icon": "Sun"},
    1: {"desc": "Mayormente despejado", "icon": "SunMedium"},
    2: {"desc": "Parcialmente nublado", "icon": "CloudSun"},
    3: {"desc": "Nublado", "icon": "Cloud"},
    45: {"desc": "Neblina", "icon": "CloudFog"},
    48: {"desc": "Neblina con escarcha", "icon": "CloudFog"},
    51: {"desc": "Llovizna ligera", "icon": "CloudDrizzle"},
    53: {"desc": "Llovizna moderada", "icon": "CloudDrizzle"},
    55: {"desc": "Llovizna densa", "icon": "CloudDrizzle"},
    56: {"desc": "Llovizna helada ligera", "icon": "CloudSnow"},
    57: {"desc": "Llovizna helada densa", "icon": "CloudSnow"},
    61: {"desc": "Lluvia ligera", "icon": "CloudRain"},
    63: {"desc": "Lluvia moderada", "icon": "CloudRain"},
    65: {"desc": "Lluvia fuerte", "icon": "CloudRainWind"},
    66: {"desc": "Lluvia helada ligera", "icon": "CloudSnow"},
    67: {"desc": "Lluvia helada fuerte", "icon": "CloudSnow"},
    71: {"desc": "Nevada ligera", "icon": "Snowflake"},
    73: {"desc": "Nevada moderada", "icon": "Snowflake"},
    75: {"desc": "Nevada intensa", "icon": "Snowflake"},
    77: {"desc": "Granizo menudo", "icon": "CloudHail"},
    80: {"desc": "Chubascos ligeros", "icon": "CloudSunRain"},
    81: {"desc": "Chubascos moderados", "icon": "CloudRain"},
    82: {"desc": "Chubascos violentos", "icon": "CloudRainWind"},
    85: {"desc": "Chubascos de nieve ligeros", "icon": "CloudSnow"},
    86: {"desc": "Chubascos de nieve fuertes", "icon": "CloudSnow"},
    95: {"desc": "Tormenta eléctrica", "icon": "CloudLightning"},
    96: {"desc": "Tormenta con granizo ligero", "icon": "CloudHail"},
    99: {"desc": "Tormenta con granizo fuerte", "icon": "CloudHail"}
}

SPANISH_DAYS = {
    0: "Lunes", 1: "Martes", 2: "Miercoles", 3: "Jueves",
    4: "Viernes", 5: "Sabado", 6: "Domingo"
}

SPANISH_DAYS_SHORT = {
    0: "Lun", 1: "Mar", 2: "Mie", 3: "Jue",
    4: "Vie", 5: "Sab", 6: "Dom"
}


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


def get_weather_meta(code: int, is_day: bool = True) -> tuple[str, str]:
    meta = WMO_CODES.get(code, {"desc": "Despejado", "icon": "Sun"})
    icon = meta["icon"]
    if not is_day:
        if icon in ["Sun", "SunMedium"]:
            icon = "Moon"
        elif icon == "CloudSun":
            icon = "CloudMoon"
        elif icon == "CloudSunRain":
            icon = "CloudMoonRain"
    return meta["desc"], icon


class WeatherService:
    # Perfiles climáticos por ciudad (para datos históricos)
    CITY_PROFILES = {
        "Lima": {"region": "Costa", "base_temp": 21.0, "temp_var": 3.0, "humidity": 78, "rain_days": 5, "uv_base": 7.0, "wind_base": 14.0},
        "Cusco": {"region": "Sierra", "base_temp": 13.5, "temp_var": 12.0, "humidity": 58, "rain_days": 45, "uv_base": 10.0, "wind_base": 11.0},
        "Arequipa": {"region": "Sierra", "base_temp": 15.0, "temp_var": 10.0, "humidity": 45, "rain_days": 15, "uv_base": 9.5, "wind_base": 12.0},
        "Iquitos": {"region": "Selva", "base_temp": 28.0, "temp_var": 3.0, "humidity": 88, "rain_days": 120, "uv_base": 8.5, "wind_base": 9.0},
        "Trujillo": {"region": "Costa", "base_temp": 23.0, "temp_var": 4.0, "humidity": 75, "rain_days": 3, "uv_base": 8.0, "wind_base": 16.0},
    }

    @classmethod
    def _get_climate_profile(cls, city_name: str) -> Dict[str, Any]:
        return cls.CITY_PROFILES.get(city_name, {"base_temp": 20.0, "temp_var": 5.0, "humidity": 60, "rain_days": 10, "uv_base": 7.0, "wind_base": 12.0})

    @classmethod
    def _generate_current_weather_from_profile(cls, city: City) -> CurrentWeather:
        """Genera datos de clima actual basados en el perfil climático de la ciudad."""
        profile = cls._get_climate_profile(city.name)
        base_temp = profile["base_temp"]
        
        # Variación estacional
        day_of_year = datetime.now().timetuple().tm_yday
        seasonal_var = (datetime.now().month - 7) * 0.5  # más frío en invierno (jun-oct)
        
        temp_mean = base_temp + seasonal_var + random.gauss(0, 1)
        temp_max = temp_mean + profile["temp_var"] / 2
        temp_min = temp_mean - profile["temp_var"] / 2
        
        humidity = profile["humidity"] + random.randint(-10, 10)
        humidity = max(20, min(98, humidity))
        
        wind = profile["wind_base"] + random.gauss(0, 3)
        wind = max(2, round(wind, 1))
        
        uv = profile["uv_base"] + seasonal_var * 0.3
        uv = max(1.0, min(12.0, round(uv, 1)))
        
        # Lluvia
        is_rainy = random.random() < (profile["rain_days"] / 365)
        if is_rainy:
            precipitation = round(random.uniform(1.0, 10.0), 1)
            rain_prob = random.randint(70, 95)
            cloud_cover = random.randint(60, 95)
            weather_code = random.choice([61, 63, 65])
        else:
            precipitation = round(random.uniform(0.0, 0.5), 1)
            rain_prob = random.randint(5, 25)
            cloud_cover = random.randint(0, 30)
            weather_code = 0 if cloud_cover < 15 else (1 if cloud_cover < 40 else 2)
        
        return CurrentWeather(
            temperature=round(temp_mean, 1),
            apparent_temperature=round(temp_mean + random.gauss(0, 1), 1),
            relative_humidity=humidity,
            wind_speed=wind,
            wind_direction=random.randint(0, 359),
            wind_gusts=round(wind + random.uniform(0, 5), 1) if random.random() > 0.5 else None,
            surface_pressure=round(1013 + random.gauss(0, 3), 1),
            precipitation=precipitation,
            precipitation_probability=rain_prob,
            cloud_cover=cloud_cover,
            uv_index=uv,
            uv_category=get_uv_category(uv),
            weather_code=weather_code,
            weather_description=get_weather_meta(weather_code)[0],
            weather_icon=get_weather_meta(weather_code)[1],
            is_day=1,
            temp_max=round(temp_max, 1),
            temp_min=round(temp_min, 1),
            sunrise="06:15",
            sunset="18:30",
            updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            city_id=city.id,
            city_name=city.name,
            department_name=city.department.name if city.department else "",
            region_natural=city.department.region_natural if city.department else "",
            altitude=city.altitude,
            latitude=city.latitude,
            longitude=city.longitude
        )

    @classmethod
    async def get_forecast(
        cls,
        lat: float,
        lon: float,
        city_id: Optional[int] = None,
        city_name: Optional[str] = None,
        department_name: Optional[str] = None,
        region_natural: Optional[str] = None,
        altitude: Optional[int] = None,
        db: Optional[Session] = None
    ) -> FullForecastResponse:
        # Si se provee city_id, obtener datos de la base de datos
        if city_id and db:
            city_obj = db.query(City).filter(City.id == city_id).first()
            if city_obj:
                # Intentar obtener datos históricos del día actual
                today = datetime.now().strftime("%Y-%m-%d")
                history = db.query(cls._get_climate_model()).filter(
                    cls._get_climate_model().city_id == city_id,
                    cls._get_climate_model().date == today
                ).first()
                
                if history:
                    # Generar pronóstico basado en datos históricos
                    current = cls._history_to_current_weather(history, city_obj)
                    hourly = cls._generate_hourly_from_current(current)
                    daily = cls._generate_7day_forecast(current, city_obj)
                    return FullForecastResponse(current=current, hourly=hourly, daily=daily)
        
        # Fallback: generar datos sintéticos basados en el perfil de la ciudad
        current = cls._generate_current_weather_from_profile(
            db.query(City).filter(City.id == city_id).first() if city_id else City(
                name=city_name or "Perú", altitude=altitude or 0,
                latitude=lat, longitude=lon,
                department=Department(name=department_name or "Perú", region_natural=region_natural or "Costa") if department_name else None
            ) if city_id else City(name="Perú", altitude=altitude or 0, latitude=lat, longitude=lon, department=Department(name=department_name or "Perú", region_natural=region_natural or "Costa") if department_name else None)
        )
        
        hourly = cls._generate_hourly_from_current(current)
        daily = cls._generate_7day_forecast(current, None)
        
        return FullForecastResponse(current=current, hourly=hourly, daily=daily)

    @classmethod
    def _get_climate_model(cls):
        """Obtener modelo ClimateHistory si existe."""
        try:
            from app.models.climate_history import ClimateHistory
            return ClimateHistory
        except ImportError:
            return None

    @classmethod
    def _history_to_current_weather(cls, history: Any, city: City) -> CurrentWeather:
        """Convierte un registro de ClimateHistory a CurrentWeather."""
        return CurrentWeather(
            temperature=history.temperature,
            apparent_temperature=history.apparent_temperature,
            relative_humidity=history.relative_humidity,
            wind_speed=history.wind_speed,
            wind_direction=history.wind_direction,
            wind_gusts=history.wind_gusts,
            surface_pressure=history.surface_pressure,
            precipitation=history.precipitation,
            precipitation_probability=history.precipitation_probability,
            cloud_cover=history.cloud_cover,
            uv_index=history.uv_index,
            uv_category=history.uv_category,
            weather_code=history.weather_code,
            weather_description=history.weather_description,
            weather_icon=history.weather_icon,
            is_day=history.is_day,
            temp_max=history.temp_max,
            temp_min=history.temp_min,
            sunrise=history.sunrise or "06:15",
            sunset=history.sunset or "18:30",
            updated_at=history.date + " 08:00:00",
            city_id=city.id,
            city_name=city.name,
            department_name=city.department.name if city.department else "",
            region_natural=city.department.region_natural if city.department else "",
            altitude=city.altitude,
            latitude=city.latitude,
            longitude=city.longitude
        )

    @classmethod
    def _generate_hourly_from_current(cls, current: CurrentWeather) -> List[HourlyForecastItem]:
        """Genera pronóstico horario basado en el clima actual."""
        items = []
        current_hour = datetime.now().hour
        
        for i in range(24):
            hour = (current_hour + i) % 24
            hour_label = f"{str(hour).zfill(2)}:00"
            
            # Variación diaria de temperatura
            temp_var = math.sin((hour - 14) * math.pi / 12) * 3  # máxima a las 2pm
            
            item = HourlyForecastItem(
                time=f"2026-08-29T{hour_label}:00",
                hour_label=hour_label,
                temperature=round(current.temperature + temp_var, 1),
                apparent_temperature=round(current.apparent_temperature + temp_var, 1),
                relative_humidity=max(20, min(98, current.relative_humidity - int(temp_var * 2))),
                precipitation_probability=max(5, min(95, current.precipitation_probability - i)),
                precipitation=max(0, round(current.precipitation - i * 0.1, 1)),
                weather_code=current.weather_code,
                weather_description=current.weather_description,
                weather_icon=current.weather_icon,
                wind_speed=round(current.wind_speed + random.gauss(0, 1), 1),
                uv_index=round(max(0, current.uv_index * math.sin((hour - 6) * math.pi / 12)), 1),
                is_day=1 if 6 <= hour <= 18 else 0
            )
            items.append(item)
        
        return items

    @classmethod
    def _generate_7day_forecast(cls, current: CurrentWeather, city: Optional[City]) -> List[DailyForecastItem]:
        """Genera pronóstico de 7 días basado en el clima actual."""
        import math
        
        items = []
        for i in range(7):
            day_name = SPANISH_DAYS[i]
            day_short = SPANISH_DAYS_SHORT[i]
            
            # Variación diaria
            temp_var = math.sin(i * 0.5) * 2
            
            item = DailyForecastItem(
                date=f"2026-08-{str(30 + i).zfill(2)}",
                day_name=day_name,
                day_short=day_short,
                temp_max=round(current.temp_max + temp_var, 1),
                temp_min=round(current.temp_min - temp_var, 1),
                weather_code=current.weather_code,
                weather_description=current.weather_description,
                weather_icon=current.weather_icon,
                precipitation_sum=round(max(0, current.precipitation - i * 0.2), 1),
                precipitation_probability_max=max(5, min(95, current.precipitation_probability - i * 2)),
                uv_index_max=round(max(0, current.uv_index * 0.8), 1),
                wind_speed_max=round(current.wind_speed + 2, 1),
                sunrise="06:15",
                sunset="18:30"
            )
            items.append(item)
        
        return items

    @classmethod
    async def get_departments_summary(cls, db: Session) -> List[DepartmentWeatherSummary]:
        """Obtiene resumen nacional de los 25 departamentos usando datos cargados."""
        departments = db.query(Department).all()
        summaries = []
        
        for dept in departments:
            # Intentar obtener datos de la capital
            capital = db.query(City).filter(
                City.department_id == dept.id,
                City.is_capital == True
            ).first()
            
            if capital:
                today = datetime.now().strftime("%Y-%m-%d")
                history = db.query(cls._get_climate_model()).filter(
                    cls._get_climate_model().city_id == capital.id,
                    cls._get_climate_model().date == today
                ).first()
                
                if history:
                    summaries.append(DepartmentWeatherSummary(
                        department_id=dept.id,
                        department_name=dept.name,
                        capital=dept.capital,
                        latitude=dept.latitude,
                        longitude=dept.longitude,
                        region_natural=dept.region_natural,
                        temperature=history.temperature,
                        weather_description=history.weather_description,
                        weather_icon=history.weather_icon,
                        relative_humidity=history.relative_humidity,
                        precipitation=history.precipitation,
                        uv_index=history.uv_index,
                        wind_speed=history.wind_speed
                    ))
                else:
                    # Fallback: datos sintéticos basados en región
                    profile = cls._get_climate_profile(dept.capital)
                    summaries.append(DepartmentWeatherSummary(
                        department_id=dept.id,
                        department_name=dept.name,
                        capital=dept.capital,
                        latitude=dept.latitude,
                        longitude=dept.longitude,
                        region_natural=dept.region_natural,
                        temperature=round(profile["base_temp"] + random.gauss(0, 1), 1),
                        weather_description="Parcialmente nublado",
                        weather_icon="CloudSun",
                        relative_humidity=profile["humidity"],
                        precipitation=round(random.uniform(0, 2), 1),
                        uv_index=round(profile["uv_base"] + random.gauss(0, 0.5), 1),
                        wind_speed=round(profile["wind_base"] + random.gauss(0, 2), 1)
                    ))
            else:
                # Fallback por defecto
                summaries.append(DepartmentWeatherSummary(
                    department_id=dept.id,
                    department_name=dept.name,
                    capital=dept.capital,
                    latitude=dept.latitude,
                    longitude=dept.longitude,
                    region_natural=dept.region_natural,
                    temperature=round(20 + random.gauss(0, 2), 1),
                    weather_description="Parcialmente nublado",
                    weather_icon="CloudSun",
                    relative_humidity=60,
                    precipitation=round(random.uniform(0, 2), 1),
                    uv_index=round(7 + random.gauss(0, 1), 1),
                    wind_speed=round(12 + random.gauss(0, 2), 1)
                ))
        
        return summaries

    @classmethod
    async def get_history(
        cls,
        city_id: int,
        start_date: str,
        end_date: str,
        variable: str,
        db: Session
    ) -> HistoryResponse:
        """Obtiene historial climático desde datos cargados (Big Data)."""
        climate_model = cls._get_climate_model()
        
        # Si no hay modelo ClimateHistory, usar simulación
        if not climate_model:
            return cls._generate_fallback_history(city_id, start_date, end_date, variable, db)
        
        city = db.query(City).filter(City.id == city_id).first()
        if not city:
            raise ValueError(f"Ciudad con ID {city_id} no encontrada.")
        
        # Consultar datos históricos cargados
        records = db.query(climate_model).filter(
            climate_model.city_id == city_id,
            climate_model.date >= start_date,
            climate_model.date <= end_date
        ).all()
        
        if not records:
            return cls._generate_fallback_history(city_id, start_date, end_date, variable, db)
        
        # Convertir a HistoryDataPoint
        data_points = []
        val_for_stats = []
        
        for r in records:
            dp = HistoryDataPoint(
                date=r.date,
                temp_max=round(r.temp_max, 1),
                temp_min=round(r.temp_min, 1),
                temp_mean=round((r.temp_max + r.temp_min) / 2, 1),
                precipitation_sum=round(r.precipitation, 1),
                wind_speed_max=round(r.wind_speed, 1),
                relative_humidity_mean=r.relative_humidity,
                weather_code=r.weather_code
            )
            data_points.append(dp)
            
            if variable == "temperature":
                val_for_stats.append(dp.temp_mean)
            elif variable == "precipitation":
                val_for_stats.append(dp.precipitation_sum)
            elif variable == "wind":
                val_for_stats.append(dp.wind_speed_max)
            else:
                val_for_stats.append(dp.temp_mean)
        
        if not val_for_stats:
            val_for_stats = [20.0]
        
        avg_val = sum(val_for_stats) / len(val_for_stats)
        max_val = max(val_for_stats)
        min_val = min(val_for_stats)
        
        # Calcular tendencia
        trend = "estable"
        if len(val_for_stats) > 3:
            first_half = sum(val_for_stats[:len(val_for_stats)//2]) / (len(val_for_stats)//2)
            second_half = sum(val_for_stats[len(val_for_stats)//2:]) / (len(val_for_stats) - len(val_for_stats)//2)
            if second_half - first_half > 0.8:
                trend = "ascendente"
            elif first_half - second_half > 0.8:
                trend = "descendente"
        
        stats = HistoryStats(
            average=round(avg_val, 2),
            maximum=round(max_val, 2),
            minimum=round(min_val, 2),
            trend=trend,
            total_precipitation=round(sum(r.precipitation for r in records), 1),
            days_analyzed=len(data_points)
        )
        
        return HistoryResponse(
            city_id=city.id,
            city_name=city.name,
            department_name=city.department.name,
            variable=variable,
            start_date=start_date,
            end_date=end_date,
            stats=stats,
            data=data_points
        )

    @classmethod
    def _generate_fallback_history(cls, city_id: int, start_date: str, end_date: str, variable: str, db: Session) -> HistoryResponse:
        """Genera datos históricos sintéticos si no hay datos cargados."""
        import math
        
        try:
            d_start = datetime.strptime(start_date, "%Y-%m-%d")
            d_end = datetime.strptime(end_date, "%Y-%m-%d")
        except:
            d_start = datetime.now() - timedelta(days=30)
            d_end = datetime.now()
        
        days = (d_end - d_start).days + 1
        city = db.query(City).filter(City.id == city_id).first()
        
        base_temp = 21.0 if city and city.department and city.department.region_natural == "Costa" else 14.0 if city and city.department and city.department.region_natural == "Sierra" else 28.0
        val_for_stats = []
        data_points = []
        
        for i in range(days):
            cur_d = d_start + timedelta(days=i)
            cur_d_str = cur_d.strftime("%Y-%m-%d")
            
            variation = math.sin(i * 0.4) * 2.5 + ((i % 5) - 2) * 0.5
            t_mean = base_temp + variation
            t_max = t_mean + 4.5
            t_min = t_mean - 4.5
            p_sum = max(0.0, round((math.cos(i * 0.7) * 3.0) if city and city.department and city.department.region_natural != "Costa" else 0.2, 1))
            w_max = max(5.0, round(12.0 + math.sin(i * 0.3) * 4.0, 1))
            
            dp = HistoryDataPoint(
                date=cur_d_str,
                temp_max=round(t_max, 1),
                temp_min=round(t_min, 1),
                temp_mean=round(t_mean, 1),
                precipitation_sum=p_sum,
                wind_speed_max=w_max,
                relative_humidity_mean=78.0,
                weather_code=1 if p_sum == 0 else 61
            )
            data_points.append(dp)
            
            if variable == "temperature":
                val_for_stats.append(dp.temp_mean)
            elif variable == "precipitation":
                val_for_stats.append(dp.precipitation_sum)
            elif variable == "wind":
                val_for_stats.append(dp.wind_speed_max)
            else:
                val_for_stats.append(dp.temp_mean)
        
        avg_val = sum(val_for_stats) / len(val_for_stats)
        
        return HistoryResponse(
            city_id=city_id,
            city_name=city.name if city else "Perú",
            department_name=city.department.name if city and city.department else "Perú",
            variable=variable,
            start_date=start_date,
            end_date=end_date,
            stats=HistoryStats(
                average=round(avg_val, 2),
                maximum=round(max(val_for_stats), 2),
                minimum=round(min(val_for_stats), 2),
                trend="estable",
                total_precipitation=round(sum(dp.precipitation_sum for dp in data_points), 1),
                days_analyzed=len(data_points)
            ),
            data=data_points
        )
