import os
import joblib
import pandas as pd
from collections import deque

BASE_DIR = os.path.dirname(__file__)

mag_model = joblib.load(os.path.join(BASE_DIR, "Models", "earthquake_magnitude.pkl"))
depth_model = joblib.load(os.path.join(BASE_DIR, "Models", "earthquake_depth.pkl"))
epi_model = joblib.load(os.path.join(BASE_DIR, "Models", "earthquake_epicenter.pkl"))

WINDOW_SIZE = 3
mag_buffer = deque(maxlen=WINDOW_SIZE)
depth_buffer = deque(maxlen=WINDOW_SIZE)

def predict_earthquake(features):
    input_df = pd.DataFrame([features])

    mag_pred = float(mag_model.predict(input_df)[0])
    depth_pred = float(depth_model.predict(input_df)[0])
    epi_pred = int(epi_model.predict(input_df)[0])

    mag_buffer.append(mag_pred)
    depth_buffer.append(depth_pred)

    avg_mag = sum(mag_buffer) / len(mag_buffer)
    avg_depth = sum(depth_buffer) / len(depth_buffer)

    return {
        "current": {
            "magnitude": round(mag_pred, 2),
            "depth_km": round(depth_pred, 1)
        },
        "stable": {
            "magnitude": round(avg_mag, 2),
            "depth_km": round(avg_depth, 1)
        },
        "epicenter": "ocean" if epi_pred == 1 else "land",
        "confidence": {
            "window_filled": len(mag_buffer) == WINDOW_SIZE,
            "buffer_size": len(mag_buffer)
        }
    }