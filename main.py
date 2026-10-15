import os
import requests
import joblib
import bcrypt
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt

from database import engine, get_db, Base
import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DRISTI AI Core Engine", version="5.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "DRISTI_SIH_SUPER_SECRET_JWT_KEY_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

MODEL_PATH = "landslide_model.pkl"
SCALER_PATH = "scaler.pkl"

if not os.path.exists(MODEL_PATH):
    import train_model
    train_model.train_and_export()

rf_model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
LABEL_MAP = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}

# --- Schemas ---
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str
    phone_number: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str
    email: str

class TelemetryIngest(BaseModel):
    sensor_id: str
    latitude: float
    longitude: float
    rainfall_mm_hr: float
    soil_moisture_pct: float
    slope_angle_deg: float
    ground_displacement_mm: float
    land_cover_code: Optional[int] = 2
    river_proximity_m: Optional[float] = 250.0

class IncidentCreate(BaseModel):
    incident_type: str
    latitude: float
    longitude: float
    location_name: str
    description: str
    photo_url: Optional[str] = None

class RouteRequest(BaseModel):
    start_lat: float
    start_lng: float
    dest_lat: float
    dest_lng: float

class DispatchOrder(BaseModel):
    team_id: int
    target_zone: str

# --- Security Functions ---

# Replace passlib functions with pure bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # bcrypt requires bytes
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    # Hash password directly without passlib reflection
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def require_authority(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "authority":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Authority privileges required."
        )
    return current_user

# --- ML Model Predictor ---
def predict_hazard(rainfall, moisture, slope, displacement, land_cover, river_prox):
    raw_vec = np.array([[rainfall, moisture, slope, displacement, land_cover, river_prox]])
    scaled_vec = scaler.transform(raw_vec)
    pred_class = rf_model.predict(scaled_vec)[0]
    probs = rf_model.predict_proba(scaled_vec)[0]

    risk_score = round(float((probs[1] * 40 + probs[2] * 70 + probs[3] * 100)), 2)
    risk_level = LABEL_MAP[pred_class]
    confidence = round(float(np.max(probs)), 2)

    factors = {
        "rainfall_impact": round(min(rainfall / 120 * 100, 100), 1),
        "soil_saturation_pct": round(moisture, 1),
        "slope_steepness_deg": round(slope, 1),
        "ground_displacement_mm": round(displacement, 2),
        "river_proximity_m": round(river_prox, 1),
        "model_confidence": confidence
    }
    return risk_score, risk_level, confidence, factors

# --- Endpoints: Auth ---
@app.post("/api/auth/register", response_model=TokenResponse)
def register_user(user_in: UserRegister, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")
    
    user = models.User(
        full_name=user_in.full_name,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role if user_in.role in ['citizen', 'authority'] else 'citizen',
        phone_number=user_in.phone_number
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        data={"sub": user.email, "role": user.role, "name": user.full_name},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer", "role": user.role, "full_name": user.full_name, "email": user.email}

@app.post("/api/auth/login", response_model=TokenResponse)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    token = create_access_token(
        data={"sub": user.email, "role": user.role, "name": user.full_name},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer", "role": user.role, "full_name": user.full_name, "email": user.email}

# --- Endpoints: Domain Operations ---
@app.post("/api/telemetry/ingest")
def ingest_telemetry(data: TelemetryIngest, db: Session = Depends(get_db)):
    entry = models.Telemetry(**data.dict())
    db.add(entry)
    db.commit()

    score, level, conf, factors = predict_hazard(
        data.rainfall_mm_hr, data.soil_moisture_pct,
        data.slope_angle_deg, data.ground_displacement_mm,
        data.land_cover_code, data.river_proximity_m
    )

    zone_name = f"Sector-{data.sensor_id}"
    zone = db.query(models.RiskZone).filter(models.RiskZone.zone_name == zone_name).first()

    if not zone:
        zone = models.RiskZone(
            zone_name=zone_name, latitude=data.latitude, longitude=data.longitude,
            radius_meters=650, risk_score=score, risk_level=level,
            ml_confidence=conf, factor_breakdown=factors
        )
        db.add(zone)
    else:
        zone.latitude = data.latitude
        zone.longitude = data.longitude
        zone.risk_score = score
        zone.risk_level = level
        zone.ml_confidence = conf
        zone.factor_breakdown = factors

    db.commit()
    return {"status": "success", "zone": zone_name, "score": score, "level": level, "confidence": conf}

@app.get("/api/zones")
def get_zones(db: Session = Depends(get_db)):
    zones = db.query(models.RiskZone).all()
    if not zones:
        defaults = [
            ("Sector-DEH-01", 30.3250, 78.0400, 92.5, 91.0, 41.5, 5.8, 2, 80.0),
            ("Sector-DEH-02", 30.3320, 78.0250, 68.0, 78.0, 33.0, 2.1, 2, 220.0),
            ("Sector-DEH-03", 30.3100, 78.0200, 32.0, 48.0, 21.0, 0.3, 1, 600.0),
            ("Sector-DEH-04", 30.3050, 78.0450, 14.0, 28.0, 14.0, 0.0, 1, 950.0)
        ]
        for name, lat, lng, r, m, s, d, lc, rp in defaults:
            score, lvl, conf, factors = predict_hazard(r, m, s, d, lc, rp)
            z = models.RiskZone(
                zone_name=name, latitude=lat, longitude=lng,
                risk_score=score, risk_level=lvl, ml_confidence=conf,
                factor_breakdown=factors
            )
            db.add(z)
        db.commit()
        zones = db.query(models.RiskZone).all()
    return zones

@app.get("/api/shelters")
def get_shelters(db: Session = Depends(get_db)):
    return db.query(models.Shelter).filter(models.Shelter.is_operational == True).all()

@app.get("/api/teams")
def get_teams(db: Session = Depends(get_db)):
    return db.query(models.ResponseTeam).all()

@app.post("/api/teams/dispatch")
def dispatch_team(order: DispatchOrder, db: Session = Depends(get_db), auth: models.User = Depends(require_authority)):
    team = db.query(models.ResponseTeam).filter(models.ResponseTeam.id == order.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    team.status = "Deployed"
    team.assigned_zone = order.target_zone
    db.commit()
    return {"status": "dispatched", "unit": team.unit_name, "zone": order.target_zone}

@app.get("/api/incidents")
def get_incidents(db: Session = Depends(get_db)):
    return db.query(models.Incident).order_by(models.Incident.id.desc()).all()

@app.post("/api/incidents")
def report_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    new_inc = models.Incident(
        incident_type=incident.incident_type,
        latitude=incident.latitude,
        longitude=incident.longitude,
        location_name=incident.location_name,
        description=incident.description,
        photo_url=incident.photo_url,
        severity="Critical" if incident.incident_type == "Active Landslide" else "Medium",
        status="Pending"
    )
    db.add(new_inc)
    db.commit()
    return {"status": "reported", "incident_id": new_inc.id}

@app.put("/api/incidents/{incident_id}/verify")
def verify_incident(incident_id: int, db: Session = Depends(get_db), auth: models.User = Depends(require_authority)):
    inc = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    inc.status = "Verified"
    db.commit()
    return {"status": "verified"}

@app.post("/api/routes/safe-path")
def generate_safe_road_route(req: RouteRequest):
    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{req.start_lng},{req.start_lat};{req.dest_lng},{req.dest_lat}?overview=full&geometries=geojson"
    try:
        resp = requests.get(osrm_url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if "routes" in data and len(data["routes"]) > 0:
                coords = data["routes"][0]["geometry"]["coordinates"]
                return {
                    "success": True,
                    "coordinates": [[pt[1], pt[0]] for pt in coords],
                    "distance_km": round(data["routes"][0]["distance"] / 1000, 2),
                    "duration_min": round(data["routes"][0]["duration"] / 60, 1),
                    "status": "Safe route calculated via road network"
                }
    except Exception:
        pass
    
    return {
        "success": True,
        "coordinates": [[req.start_lat, req.start_lng], [30.3200, 78.0280], [req.dest_lat, req.dest_lng]],
        "distance_km": 2.6,
        "duration_min": 7.0,
        "status": "Evacuation corridor active (Offline fallback)"
    }

@app.post("/api/alerts/broadcast")
def broadcast_alert(db: Session = Depends(get_db), auth: models.User = Depends(require_authority)):
    channels = ["SMS (NDMA/CAP)", "WhatsApp Emergency Channel", "Civil Defense Acoustic Siren", "In-App Push"]
    msg = "DRISTI ALERT: Critical Landslide Probability > 90% in Sector DEH-01. Evacuate via Doon Safe Route immediately."
    log = models.BroadcastLog(
        alert_type="LANDSLIDE_RED_WARNING",
        target_sector="Dehradun Sector 1 & Rajpur Basin",
        message=msg,
        dispatched_channels=channels,
        recipients_count=2350
    )
    db.add(log)
    db.commit()
    return {"status": "broadcast_complete", "recipients_reached": 2350, "channels": channels, "message": msg, "timestamp": str(log.sent_at)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)