import time
import random
import math

from simengine import generate_scenario
from event_classifier import is_earthquake_event
from tsunami_evaluator import evaluate_tsunami
from landslide_predictor import predict_landslide_risk

# -------------------------------------------------
# EVENT STORE
# -------------------------------------------------
EVENT_STREAM = []

def emit_event(event_type, severity, message, extra=None):
    event = {
        "id": time.time(),
        "timestamp": time.time(),
        "type": event_type,
        "severity": severity,
        "message": message
    }
    if extra:
        event.update(extra)

    EVENT_STREAM.append(event)
    print(event)

# -------------------------------------------------
# INDIA GEO
# -------------------------------------------------
USER_LAT, USER_LON = 20.59, 78.96

CITIES = [
("Srinagar",34.08,74.79),("Shimla",31.10,77.17),("Dehradun",30.32,78.03),
("Delhi",28.61,77.20),("Jaipur",26.91,75.79),("Ahmedabad",23.02,72.57),
("Mumbai",19.07,72.87),("Bangalore",12.97,77.59),
("Hyderabad",17.38,78.48),("Chennai",13.08,80.27),
("Kochi",9.93,76.26),("Visakhapatnam",17.69,83.22),
("Kolkata",22.57,88.36)
]

HIMALAYAS = [(30,79),(32,77),(34,75)]
BAY_OF_BENGAL = [(12,88),(14,90),(16,92)]
ARABIAN_SEA = [(18,66),(14,70)]

def haversine(a,b,c,d):
    R = 6371
    dlat = math.radians(c-a)
    dlon = math.radians(d-b)
    x = math.sin(dlat/2)**2 + math.cos(math.radians(a))*math.cos(math.radians(c))*math.sin(dlon/2)**2
    return 2*R*math.atan2(math.sqrt(x), math.sqrt(1-x))

def nearest_city(lat,lon):
    return min(CITIES, key=lambda c: haversine(lat,lon,c[1],c[2]))[0]

def random_point(points, spread=0.6):
    p = random.choice(points)
    return p[0]+random.uniform(-spread,spread), p[1]+random.uniform(-spread,spread)

# -------------------------------------------------
# EVENT BALANCING (THIS IS THE KEY PART)
# -------------------------------------------------
EVENT_GAP_LIMIT = 5

cycles_without = {
    "tsunami": 0,
    "landslide": 0
}

# -------------------------------------------------
# MAIN SIM LOOP
# -------------------------------------------------
def simulation_loop():
    while True:
        s = generate_scenario()
        events_this_cycle = set()

        # ---------------- EARTHQUAKE ----------------
        seismic = {
            "p_wave_amplitude": s["magnitude"]**1.4,
            "s_wave_amplitude": s["magnitude"]**1.6,
            "ps_time_diff_sec": max(0.5, s["depth_km"]/8),
            "frequency_hz": max(0.8, 8 - s["magnitude"])
        }

        if is_earthquake_event(seismic)["is_earthquake"]:
            zone = random.choice(["HIMALAYAS","BAY","ARABIAN"])
            lat, lon = (
                random_point(HIMALAYAS) if zone=="HIMALAYAS"
                else random_point(BAY_OF_BENGAL,1.2) if zone=="BAY"
                else random_point(ARABIAN_SEA,1.2)
            )

            city = nearest_city(lat,lon)
            dist = round(haversine(USER_LAT,USER_LON,lat,lon),1)

            severity = (
                "critical" if s["magnitude"] >= 8.5 else
                "high" if s["magnitude"] >= 7.2 else
                "medium"
            )

            emit_event(
                "earthquake",
                severity,
                f"M{s['magnitude']:.1f} earthquake near {city}",
                {"lat":lat,"lon":lon,"location":city,"distance_km":dist}
            )

        # ---------------- TSUNAMI (NORMAL) ----------------
        tsunami = evaluate_tsunami(s)
        if tsunami["tsunami_alert"]:
            lat, lon = random_point(BAY_OF_BENGAL,1.5)
            city = nearest_city(lat,lon)
            dist = round(haversine(USER_LAT,USER_LON,lat,lon),1)

            emit_event(
                "tsunami",
                tsunami["severity"],
                f"{tsunami['severity']} tsunami risk near {city}",
                {"lat":lat,"lon":lon,"location":city,"distance_km":dist}
            )

            events_this_cycle.add("tsunami")

        # ---------------- LANDSLIDE (NORMAL) ----------------
        landslide_input = {
            "rainfall_mm": s["rainfall_mm"],
            "soil_moisture": s["soil_moisture"],
            "slope_angle_deg": s["slope_angle_deg"],
            "vegetation_index": s["vegetation_index"],
            "soil_type": s["soil_type"],
            "ground_vibration": s["ground_vibration"]
        }

        if (
            landslide_input["rainfall_mm"] > 80 and
            landslide_input["slope_angle_deg"] > 25 and
            predict_landslide_risk(landslide_input)["landslide_alert"]
        ):
            lat, lon = random_point(HIMALAYAS)
            city = nearest_city(lat,lon)
            dist = round(haversine(USER_LAT,USER_LON,lat,lon),1)

            emit_event(
                "landslide",
                "high",
                f"Landslide warning near {city}",
                {"lat":lat,"lon":lon,"location":city,"distance_km":dist}
            )

            events_this_cycle.add("landslide")

        # ---------------- UPDATE GAP COUNTERS ----------------
        for k in cycles_without:
            if k in events_this_cycle:
                cycles_without[k] = 0
            else:
                cycles_without[k] += 1

        # ---------------- FORCE EVENTS IF STARVED ----------------
        if cycles_without["tsunami"] >= EVENT_GAP_LIMIT:
            lat, lon = random_point(BAY_OF_BENGAL,1.3)
            city = nearest_city(lat,lon)
            dist = round(haversine(USER_LAT,USER_LON,lat,lon),1)

            emit_event(
                "tsunami",
                "low",
                "Weak tsunami triggered after prolonged seismic inactivity",
                {"lat":lat,"lon":lon,"location":city,"distance_km":dist}
            )

            cycles_without["tsunami"] = 0

        if cycles_without["landslide"] >= EVENT_GAP_LIMIT:
            lat, lon = random_point(HIMALAYAS)
            city = nearest_city(lat,lon)
            dist = round(haversine(USER_LAT,USER_LON,lat,lon),1)

            emit_event(
                "landslide",
                "low",
                "Localized landslide after prolonged instability",
                {"lat":lat,"lon":lon,"location":city,"distance_km":dist}
            )

            cycles_without["landslide"] = 0

        time.sleep(5)
