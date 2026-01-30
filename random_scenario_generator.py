import random
import time

random.seed()  # different scenario every run

# -------------------------------------------------
# SCENARIO DEFINITIONS (THE WORLD RULES)
# -------------------------------------------------

SCENARIO_TYPES = [
    "deep_safe",
    "shallow_reverse_danger",
    "moderate_monitor",
    "strong_far_coast",
    "borderline_case"
]

FAULT_TYPES = ["normal", "strike-slip", "reverse"]

# -------------------------------------------------
# SCENARIO GENERATOR
# -------------------------------------------------

def generate_scenario():
    scenario_type = random.choice(SCENARIO_TYPES)

    scenario = {
        "scenario_type": scenario_type,
        "timestamp": time.time()
    }

    # -------------------------------
    # SCENARIO LOGIC
    # -------------------------------

    if scenario_type == "deep_safe":
        scenario.update({
            "magnitude": round(random.uniform(6.0, 8.5), 2),
            "depth_km": round(random.uniform(80, 120), 1),
            "fault_type": random.choice(FAULT_TYPES),
            "vertical_displacement_m": round(random.uniform(0.0, 0.3), 2),
            "distance_to_coast_km": round(random.uniform(300, 1000), 1),
            "ocean_depth_m": round(random.uniform(3000, 6000), 1)
        })

    elif scenario_type == "shallow_reverse_danger":
        scenario.update({
            "magnitude": round(random.uniform(7.2, 9.2), 2),
            "depth_km": round(random.uniform(5, 30), 1),
            "fault_type": "reverse",
            "vertical_displacement_m": round(random.uniform(1.0, 8.0), 2),
            "distance_to_coast_km": round(random.uniform(20, 150), 1),
            "ocean_depth_m": round(random.uniform(2000, 5000), 1)
        })

    elif scenario_type == "moderate_monitor":
        scenario.update({
            "magnitude": round(random.uniform(6.0, 6.8), 2),
            "depth_km": round(random.uniform(30, 70), 1),
            "fault_type": random.choice(["normal", "strike-slip"]),
            "vertical_displacement_m": round(random.uniform(0.1, 0.6), 2),
            "distance_to_coast_km": round(random.uniform(150, 400), 1),
            "ocean_depth_m": round(random.uniform(2500, 5500), 1)
        })

    elif scenario_type == "strong_far_coast":
        scenario.update({
            "magnitude": round(random.uniform(7.5, 9.0), 2),
            "depth_km": round(random.uniform(10, 40), 1),
            "fault_type": random.choice(FAULT_TYPES),
            "vertical_displacement_m": round(random.uniform(0.5, 3.0), 2),
            "distance_to_coast_km": round(random.uniform(500, 1000), 1),
            "ocean_depth_m": round(random.uniform(3500, 6000), 1)
        })

    elif scenario_type == "borderline_case":
        scenario.update({
            "magnitude": round(random.uniform(6.3, 6.7), 2),
            "depth_km": round(random.uniform(60, 75), 1),
            "fault_type": random.choice(FAULT_TYPES),
            "vertical_displacement_m": round(random.uniform(0.3, 0.8), 2),
            "distance_to_coast_km": round(random.uniform(80, 250), 1),
            "ocean_depth_m": round(random.uniform(2000, 4500), 1)
        })

    return scenario

# -------------------------------------------------
# DEMO RUN
# -------------------------------------------------

if __name__ == "__main__":
    print("\n🌍 RANDOM DISASTER SCENARIO GENERATED\n")

    scenario = generate_scenario()

    for k, v in scenario.items():
        print(f"{k}: {v}")

    print("\n(Next steps: feed this into ML → event stream → UI)")
