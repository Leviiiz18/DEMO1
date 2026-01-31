import joblib
import numpy as np
import os

MODEL_PATH = os.path.join("Models", "landslide_model.pkl")

print("🌄 Loading Landslide Model...")
model = joblib.load(MODEL_PATH)
print("✅ Landslide Model Ready")


def predict_landslide_risk(sample):
    """
    sample = {
        "rainfall_mm": float,
        "soil_moisture": float,
        "slope_angle_deg": float,
        "vegetation_index": float,
        "soil_type": int,
        "ground_vibration": float
    }
    """

    features = np.array([[
        sample["rainfall_mm"],
        sample["soil_moisture"],
        sample["slope_angle_deg"],
        sample["vegetation_index"],
        sample["soil_type"],
        sample["ground_vibration"]
    ]])

    prob = model.predict_proba(features)[0][1]
    risk = model.predict(features)[0]

    return {
        "landslide_alert": bool(risk),
        "risk_score": float(prob)
    }