import os
import joblib
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
tsunami_model = joblib.load(os.path.join(BASE_DIR, "Models", "tsunami_model.pkl"))

def evaluate_tsunami(sample):
    """
    Tsunami evaluation with fault-type–aware severity scaling.
    Reverse  -> strong
    Normal   -> weak
    Strike   -> very weak / rare
    """

    fault_map = {
        "normal": 0,
        "strike-slip": 1,
        "reverse": 2
    }

    input_df = pd.DataFrame([{
        "magnitude": sample["magnitude"],
        "depth_km": sample["depth_km"],
        "ocean_depth_m": sample["ocean_depth_m"],
        "fault_type_encoded": fault_map[sample["fault_type"]],
        "vertical_displacement_m": sample["vertical_displacement_m"],
        "distance_to_coast_km": sample["distance_to_coast_km"]
    }])

    # ML probability
    tsunami_prob = float(tsunami_model.predict_proba(input_df)[0][1])

    # -----------------------------
    # PHYSICAL SCALING (KEY FIX)
    # -----------------------------
    fault = sample["fault_type"]

    vertical_factor = {
        "reverse": 1.0,       # strong uplift
        "normal": 0.45,       # weaker downdrop
        "strike-slip": 0.15   # almost none
    }[fault]

    scaled_prob = tsunami_prob * vertical_factor

    # -----------------------------
    # BASE PHYSICAL REQUIREMENTS
    # -----------------------------
    basic_conditions = (
        sample["magnitude"] >= 6.5 and
        sample["depth_km"] <= 70 and
        sample["ocean_depth_m"] > 50 and
        sample["vertical_displacement_m"] >= 0.3
    )

    tsunami_alert = False
    severity = None

    if basic_conditions:
        if scaled_prob >= 0.6:
            severity = "high"
            tsunami_alert = True
        elif scaled_prob >= 0.4:
            severity = "medium"
            tsunami_alert = True
        elif scaled_prob >= 0.25 and fault == "normal":
            severity = "low"
            tsunami_alert = True

    return {
        "tsunami_probability": round(tsunami_prob, 3),
        "scaled_probability": round(scaled_prob, 3),
        "fault_type": fault,
        "severity": severity,
        "tsunami_alert": tsunami_alert
    }
