from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from typing import Optional
import time
import math
import asyncio

app = FastAPI()

# ---------------- CONFIG
CIVILIAN_THRESHOLD = 0.6
AUTHORITY_THRESHOLD = 0.3
CIVILIAN_DELAY_SEC = 10

# ---------------- STATE
authorities = []
civilians = []
monitors = []

fake_loop_task = None

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

# ---------------- MODEL (UPDATED)
class DisasterInput(BaseModel):
    latitude: float
    longitude: float
    affected_people: int

    # optional – provided by map / ML backend
    disaster_type: Optional[str] = None
    severity: Optional[str] = None
    place: Optional[str] = None

    # fallback (legacy)
    intensity: Optional[float] = None

# ---------------- HELPERS
def impact_density(intensity, affected_people):
    return min(1.0, (intensity * affected_people) / 1000)

def classify_disaster_from_intensity(intensity):
    if intensity >= 0.85:
        return "Tsunami", "HIGH"
    elif intensity >= 0.6:
        return "Cyclone", "HIGH"
    elif intensity >= 0.4:
        return "Cyclone", "MODERATE"
    else:
        return "Earthquake", "LOW"

def recommend_forces(disaster_type, severity):
    if disaster_type == "Cyclone":
        if severity == "HIGH":
            return [
                "NDRF",
                "State Disaster Response Force (SDRF)",
                "Indian Coast Guard",
                "Home Guards",
                "Electricity & PWD Departments"
            ]
        return ["SDRF", "Local Police", "Municipal Emergency Teams"]

    if disaster_type == "Tsunami":
        return [
            "NDRF",
            "Indian Navy",
            "Indian Coast Guard",
            "Coastal Police",
            "District Administration"
        ]

    if disaster_type == "Earthquake":
        return [
            "NDRF",
            "Fire & Rescue Services",
            "Medical Emergency Teams",
            "Local Police"
        ]

    return ["Local Administration"]

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
    return round(distance_km / speed_kmh, 1)

def nearest_coastal_zone(lat, lon):
    return min(COASTAL_ZONES, key=lambda z: distance_to_zone(lat, lon, z))

def advance_cyclone(lat, lon, speed_kmh):
    delta = (speed_kmh * (10 / 60)) / 111
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

# ---------------- INGEST
@app.post("/ingest")
async def ingest(data: DisasterInput):
    now = time.time()

    # ---- DISASTER DECISION SOURCE
    if data.disaster_type and data.severity:
        disaster_type = data.disaster_type
        severity = data.severity
        intensity = 0.9 if severity == "HIGH" else 0.6 if severity == "MODERATE" else 0.3
    else:
        intensity = data.intensity or 0.5
        disaster_type, severity = classify_disaster_from_intensity(intensity)

    density = impact_density(intensity, data.affected_people)

    # ---- TRACK
    if not cyclone_state["active"]:
        cyclone_state["active"] = True
        cyclone_state["track"].append((data.latitude, data.longitude, now))
    else:
        lat, lon, _ = cyclone_state["track"][-1]
        cyclone_state["track"].append((*advance_cyclone(lat, lon, cyclone_state["speed_kmh"]), now))

    current_lat, current_lon, _ = cyclone_state["track"][-1]
    affected_states = get_affected_states(current_lat, current_lon, density)

    # ---- ETA
    eta_hours = None
    if disaster_type in ["Cyclone", "Tsunami"]:
        distance_km = min(distance_to_zone(current_lat, current_lon, z) for z in COASTAL_ZONES)
        eta_hours = compute_eta_hours(distance_km, cyclone_state["speed_kmh"])

    # ---- MONITOR PAYLOAD
    monitor_payload = {
        "latitude": current_lat,
        "longitude": current_lon,
        "place": data.place,
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
        await notify(authorities, {
            **monitor_payload,
            "role": "authority",
            "eta_hours": eta_hours,
            "recommended_forces": recommend_forces(disaster_type, severity)
        })

    # ---- CIVILIAN ALERT (DELAYED)
    if density >= CIVILIAN_THRESHOLD and affected_states:
        async def delayed():
            await asyncio.sleep(CIVILIAN_DELAY_SEC)
            await notify(civilians, {
                "role": "civilian",
                "message": f"⚠️ {disaster_type} expected in {', '.join(affected_states)}",
                "severity": severity,
                "eta": f"~{eta_hours} hours" if eta_hours else None,
                "timestamp": time.time()
            })
        asyncio.create_task(delayed())

    return {"status": "processed"}

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
# ----------------