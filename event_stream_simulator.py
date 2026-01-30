import time
from random_scenario_generator import generate_scenario

# -------------------------------------------------
# EVENT STREAM (GLOBAL STATE)
# -------------------------------------------------
EVENT_STREAM = []

# -------------------------------------------------
# HELPER: ADD EVENT TO STREAM
# -------------------------------------------------
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

    # For demo visibility
    print(f"[{event_type.upper()} | {severity.upper()}] {message}")

# -------------------------------------------------
# SCENARIO EXECUTION LOGIC
# -------------------------------------------------
def run_scenario():
    scenario = generate_scenario()

    print("\n🌍 NEW SCENARIO STARTED")
    for k, v in scenario.items():
        print(f"{k}: {v}")

    # -------------------------------
    # T = 0s → CALM
    # -------------------------------
    time.sleep(1)

    # -------------------------------
    # T = 2s → EARTHQUAKE DETECTED
    # -------------------------------
    emit_event(
        event_type="earthquake",
        severity="medium",
        message="Earthquake detected offshore",
        extra={
            "magnitude": scenario["magnitude"],
            "depth_km": scenario["depth_km"]
        }
    )

    time.sleep(1)

    # -------------------------------
    # T = 3s → EARTHQUAKE ANALYSIS
    # -------------------------------
    emit_event(
        event_type="analysis",
        severity="info",
        message="Seismic analysis in progress"
    )

    time.sleep(2)

    # -------------------------------
    # T = 5s → TSUNAMI EVALUATION
    # -------------------------------
    tsunami_possible = (
        scenario["fault_type"] == "reverse" and
        scenario["depth_km"] <= 70 and
        scenario["magnitude"] >= 6.5 and
        scenario["vertical_displacement_m"] >= 0.5 and
        scenario["distance_to_coast_km"] <= 300
    )

    if tsunami_possible:
        emit_event(
            event_type="tsunami",
            severity="high",
            message="TSUNAMI ALERT: Coastal regions at risk",
            extra={
                "distance_to_coast_km": scenario["distance_to_coast_km"]
            }
        )
    else:
        emit_event(
            event_type="status",
            severity="low",
            message="No tsunami threat detected"
        )

    return EVENT_STREAM

# -------------------------------------------------
# DEMO RUN
# -------------------------------------------------
if __name__ == "__main__":
    print("\n🖥️ DISASTER CONTROL STREAM SIMULATION\n")

    events = run_scenario()

    print("\n📡 FINAL EVENT STREAM:")
    for e in events:
        print(e)
