from sqlalchemy import Column, Integer, String, Float, Enum, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum('citizen', 'authority'), default='citizen', nullable=False)
    phone_number = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class Telemetry(Base):
    __tablename__ = "environmental_telemetry"
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    rainfall_mm_hr = Column(Float, nullable=False)
    soil_moisture_pct = Column(Float, nullable=False)
    slope_angle_deg = Column(Float, nullable=False)
    ground_displacement_mm = Column(Float, nullable=False)
    land_cover_code = Column(Integer, default=2)
    river_proximity_m = Column(Float, default=250.0)
    recorded_at = Column(DateTime, server_default=func.now())

class RiskZone(Base):
    __tablename__ = "risk_zones"
    id = Column(Integer, primary_key=True, index=True)
    zone_name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_meters = Column(Integer, default=650)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(Enum('Low', 'Medium', 'High', 'Critical'), nullable=False)
    ml_confidence = Column(Float, default=0.95)
    factor_breakdown = Column(JSON, nullable=True)
    last_evaluated = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Shelter(Base):
    __tablename__ = "shelters"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    total_capacity = Column(Integer, nullable=False)
    current_occupancy = Column(Integer, default=0)
    contact_number = Column(String(20))
    ration_kits_available = Column(Integer, default=500)
    medical_kits_available = Column(Integer, default=120)
    is_operational = Column(Boolean, default=True)

class ResponseTeam(Base):
    __tablename__ = "response_teams"
    id = Column(Integer, primary_key=True, index=True)
    team_code = Column(String(50), nullable=False)
    unit_name = Column(String(100), nullable=False)
    current_lat = Column(Float, nullable=False)
    current_lng = Column(Float, nullable=False)
    personnel_count = Column(Integer, nullable=False)
    status = Column(Enum('Stationed', 'Deployed', 'In Transit', 'Resting'), default='Stationed')
    assigned_zone = Column(String(100), nullable=True)

class Incident(Base):
    __tablename__ = "citizen_incidents"
    id = Column(Integer, primary_key=True, index=True)
    incident_type = Column(String(50), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_name = Column(String(255), nullable=False)
    description = Column(Text)
    severity = Column(Enum('Low', 'Medium', 'High', 'Critical'), default='Medium')
    status = Column(Enum('Pending', 'Verified', 'Resolved', 'Rejected'), default='Pending')
    photo_url = Column(Text, nullable=True)
    reported_at = Column(DateTime, server_default=func.now())

class BroadcastLog(Base):
    __tablename__ = "alert_broadcast_logs"
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False)
    target_sector = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    dispatched_channels = Column(JSON, nullable=False)
    recipients_count = Column(Integer, default=0)
    sent_at = Column(DateTime, server_default=func.now())