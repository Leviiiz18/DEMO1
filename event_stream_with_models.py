import time
from random_scenario_generator import generate_scenario

# IMPORT YOUR MODELS
from event_classifier import is_earthquake_event
from earthquake_detector import predict_earthquake
from tsunami_evaluator import evaluate_tsunami

# -------------------------------------------------
# EVENT STREAM (SHARED WITH UI)
# -------------------------------------------------
EVENT_STREAM = []

def emit_event(event_type, severity, message, extra=None):
    event = {
        "timestamp": round(time.time(), 2),
        "type": event_type,
        "severity": severity,
        "message": message
    }
    if extra:
        event.update(extra)

    EVENT_STREAM.append(event)
    print(f"[{event_type.upper()} | {severity.upper()}] {message}")

# -------------------------------------------------
# CONTINUOUS SCENARIO EXECUTION (WITH ML)
# -------------------------------------------------
def run_scenario_with_models():
    while True:
        scenario = generate_scenario()

        print("\n🌍 NEW RANDOM SCENARIO (ML CONNECTED)")
        for k, v in scenario.items():
            print(f"{k}: {v}")

        # -------------------------------
        # T = 1s → SENSOR INPUT (FAKE)
        # -------------------------------
        time.sleep(1)

        seismic_sample = {
            "p_wave_amplitude": scenario["magnitude"] / 3,
            "s_wave_amplitude": scenario["magnitude"] / 2,
            "ps_time_diff_sec": max(1, 10 - scenario["depth_km"] / 15),
            "frequency_hz": max(0.5, 5 - scenario["magnitude"] / 2)
        }

        # -------------------------------
        # STEP A — EARTHQUAKE VALIDATION
        # -------------------------------
        eq_check = is_earthquake_event(seismic_sample)

        if not eq_check["is_earthquake"]:
            emit_event(
                "status",
                "low",
                "Seismic noise detected — no earthquake"
            )
            time.sleep(4)
            continue

        emit_event(
            "earthquake",
            "medium",
            "Earthquake detected by seismic network"
        )

        time.sleep(1)

        # -------------------------------
        # STEP B — EARTHQUAKE PREDICTION
        # -------------------------------
        eq_prediction = predict_earthquake(seismic_sample)

        emit_event(
            "analysis",
            "info",
            f"Magnitude {eq_prediction['magnitude']} | Depth {eq_prediction['depth_km']} km"
        )

        time.sleep(2)

        # -------------------------------
        # STEP C — TSUNAMI EVALUATION (REAL MODEL)
        # -------------------------------
        tsunami_input = {
            "magnitude": eq_prediction["magnitude"],
            "depth_km": eq_prediction["depth_km"],
            "ocean_depth_m": scenario["ocean_depth_m"],
            "fault_type": scenario["fault_type"],
            "vertical_displacement_m": scenario["vertical_displacement_m"],
            "distance_to_coast_km": scenario["distance_to_coast_km"]
        }

        tsunami_result = evaluate_tsunami(tsunami_input)

        if tsunami_result["tsunami_alert"]:
            emit_event(
                "tsunami",
                "high",
                "TSUNAMI ALERT — Coastal regions at risk",
                tsunami_result
            )
        else:
            emit_event(
                "status",
                "low",
                "No tsunami threat detected",
                tsunami_result
            )

        # -------------------------------
        # COOLDOWN BEFORE NEXT SCENARIO
        # -------------------------------
        emit_event(
            "status",
            "info",
            "System monitoring... awaiting next event"
        )

        time.sleep(6)  # ⏱️ pause before next random scenario

# -------------------------------------------------
# STANDALONE RUN (OPTIONAL)
# -------------------------------------------------
if __name__ == "__main__":
    print("\n🧠 DISASTER SIMULATION WITH REAL ML MODELS (CONTINUOUS)\n")
    run_scenario_with_models()
