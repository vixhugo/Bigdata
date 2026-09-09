from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    code = Column(String(10), unique=True, nullable=False)
    capital = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    region_natural = Column(String(50), nullable=False) # Costa, Sierra, Selva
    description = Column(Text, nullable=True)

    cities = relationship("City", back_populates="department", cascade="all, delete-orphan")


class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    province = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Integer, nullable=False, default=0) # metros sobre el nivel del mar
    is_featured = Column(Boolean, default=False)
    is_capital = Column(Boolean, default=False)

    department = relationship("Department", back_populates="cities")
    climate_history = relationship("ClimateHistory", back_populates="city", cascade="all, delete-orphan")
