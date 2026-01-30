import requests
import random
import time

INGEST_URL = "http://127.0.0.1:8000/ingest"

# Bangalore-ish bounding box (looks realistic)
LAT_RANGE = (12.90, 13.05)
LON_RANGE = (77.50, 77.70)

def generate_event():
    return {
        "latitude": round(random.uniform(*LAT_RANGE), 5),
        "longitude": round(random.uniform(*LON_RANGE), 5),
        "intensity": round(random.uniform(0.2, 1.0), 2),
        "affected_people": random.randint(50, 1200)
    }

print("🚨 Disaster simulator started (CTRL+C to stop)")

while True:
    payload = generate_event()
    r = requests.post(INGEST_URL, json=payload, timeout=2)

    if r.status_code == 200:
        try:
            data = r.json()
            print(f"📡 Sent: {payload} → Density:", data.get("impact_density"))
        except ValueError:
            print(f"📡 Sent: {payload} → Response received (non-JSON)")
    else:
        print(f"❌ Server error:", r.status_code)


    time.sleep(3)  # event every 3 seconds
