from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import time
import math

app = FastAPI()

# ---------------- CONFIG
CIVILIAN_THRESHOLD = 0.6
AUTHORITY_THRESHOLD = 0.3

# ---------------- STATE
authorities = []
civilians = []
monitors = []   # 🔥 NEW: monitoring clients

authority_alerts = []
civilian_alerts = []

# ---------------- COASTAL RANGES
COASTAL_ZONES = [
    {"state": "Odisha", "lat_range": (18.0, 22.5), "lon_range": (84.5, 88.8)},
    {"state": "West Bengal", "lat_range": (21.5, 26.0), "lon_range": (86.5, 91.0)},
    {"state": "Andhra Pradesh", "lat_range": (13.0, 18.5), "lon_range": (80.5, 85.5)},
    {"state": "Tamil Nadu", "lat_range": (9.0, 11.8), "lon_range": (78.5, 82.0)},
]

cyclone_state = {
    "active": False,
    "track": [],
    "speed_kmh": 18
}

# ---------------- MODEL
class DisasterInput(BaseModel):
    latitude: float
    longitude: float
    intensity: float
    affected_people: int

# ---------------- HELPERS
def impact_density(intensity, affected_people):
    return min(1.0, (intensity * affected_people) / 1000)

def classify_disaster(intensity):
    if intensity >= 0.8:
        return "Cyclone", "HIGH"
    elif intensity >= 0.5:
        return "Cyclone", "MODERATE"
    else:
        return "Cyclone", "LOW"

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

def distance_to_zone(lat, lon, zone):
    clamped_lat = min(max(lat, zone["lat_range"][0]), zone["lat_range"][1])
    clamped_lon = min(max(lon, zone["lon_range"][0]), zone["lon_range"][1])
    return haversine_km(lat, lon, clamped_lat, clamped_lon)

def compute_eta_hours(distance_km, speed_kmh):
    return round(distance_km / speed_kmh, 1) if speed_kmh else None

def nearest_coastal_zone(lat, lon):
    return min(COASTAL_ZONES, key=lambda z: distance_to_zone(lat, lon, z))

def advance_cyclone(lat, lon, speed_kmh):
    delta = (speed_kmh * (10/60)) / 111
    zone = nearest_coastal_zone(lat, lon)
    tlat = sum(zone["lat_range"]) / 2
    tlon = sum(zone["lon_range"]) / 2
    lat += delta * ((tlat - lat) / max(0.0001, abs(tlat - lat)))
    lon += delta * ((tlon - lon) / max(0.0001, abs(tlon - lon)))
    return round(lat, 4), round(lon, 4)

def get_affected_states(lat, lon, density):
    impact_km = (150 + density * 200) * 1.852
    return [z["state"] for z in COASTAL_ZONES if distance_to_zone(lat, lon, z) <= impact_km]

async def notify(group, data):
    dead = []
    for ws in group:
        try:
            await ws.send_json(data)
        except:
            dead.append(ws)
    for ws in dead:
        if ws in group:
            group.remove(ws)

# ---------------- ROOT
@app.get("/")
def root():
    return {"status": "monitoring backend running"}

# ---------------- INGEST
@app.post("/ingest")
async def ingest(data: DisasterInput):
    now = time.time()

    if not cyclone_state["active"]:
        cyclone_state["active"] = True
        cyclone_state["track"].append((data.latitude, data.longitude, now))
    else:
        lat, lon, _ = cyclone_state["track"][-1]
        new_lat, new_lon = advance_cyclone(lat, lon, cyclone_state["speed_kmh"])
        cyclone_state["track"].append((new_lat, new_lon, now))

    current_lat, current_lon, _ = cyclone_state["track"][-1]
    density = impact_density(data.intensity, data.affected_people)
    disaster_type, severity = classify_disaster(data.intensity)
    affected_states = get_affected_states(current_lat, current_lon, density)
    distance_km = min(distance_to_zone(current_lat, current_lon, z) for z in COASTAL_ZONES)
    eta_hours = compute_eta_hours(distance_km, cyclone_state["speed_kmh"])

    # 🔥 MONITORING UPDATE (ALWAYS)
    monitor_payload = {
        "latitude": current_lat,
        "longitude": current_lon,
        "disaster_type": disaster_type,
        "severity": severity,
        "density": density,
        "affected_states": affected_states,
        "status": "NORMAL" if density < 0.3 else "WATCH" if density < 0.6 else "WARNING",
        "timestamp": now
    }
    await notify(monitors, monitor_payload)

    # ---- AUTHORITY ALERT
    if density >= AUTHORITY_THRESHOLD:
        alert = {**monitor_payload, "role": "authority", "eta_hours": eta_hours}
        authority_alerts.append(alert)
        await notify(authorities, alert)

    # ---- CIVILIAN ALERT
    if density >= CIVILIAN_THRESHOLD and affected_states:
        alert = {
            "role": "civilian",
            "message": f"⚠️ {disaster_type} likely to affect {', '.join(affected_states)}",
            "severity": severity,
            "eta": f"~{eta_hours} hours",
            "timestamp": now
        }
        civilian_alerts.append(alert)
        await notify(civilians, alert)

    return {"message": "monitor update sent", "density": density}

# ---------------- WEBSOCKETS
@app.websocket("/ws/monitor")
async def monitor_ws(ws: WebSocket):
    await ws.accept()
    monitors.append(ws)
    try:
        while True:
            await ws.receive_text()
    except:
        monitors.remove(ws)

@app.websocket("/ws/authority")
async def authority_ws(ws: WebSocket):
    await ws.accept()
    authorities.append(ws)
    try:
        while True:
            await ws.receive_text()
    except:
        authorities.remove(ws)

@app.websocket("/ws/civilian")
async def civilian_ws(ws: WebSocket):
    await ws.accept()
    civilians.append(ws)
    try:
        while True:
            await ws.receive_text()
    except:
        civilians.remove(ws)
