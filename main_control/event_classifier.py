import os
import joblib
import numpy as np

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "Models", "event_classifier.pkl")

model = joblib.load(MODEL_PATH)

def is_earthquake_event(sample):
    input_data = np.array([[
        sample["p_wave_amplitude"],
        sample["s_wave_amplitude"],
        sample["ps_time_diff_sec"],
        sample["frequency_hz"]
    ]])

    prob = model.predict_proba(input_data)[0][1]

    return {
        "is_earthquake": prob >= 0.6,   # 🔥 lowered threshold
        "confidence": round(float(prob), 3)
    }

def detect_earthquake(sample):
    result = is_earthquake_event(sample)
    return result["confidence"] * 10, 10
