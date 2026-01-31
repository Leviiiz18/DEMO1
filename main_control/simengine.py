import random

class SimulationEngine:
    def __init__(self):
        # ---------------- CORE STATE ----------------
        self.tectonic_stress = random.uniform(45, 60)
        self.strain_rate = random.uniform(3.5, 6.0)
        self.system_phase = "BUILDUP"

        # ---------------- ZONE ----------------
        self.zone_type = random.choice(["OFFSHORE", "COASTAL", "INLAND"])
        self.set_geography()

        # ---------------- TERRAIN ----------------
        self.rainfall_mm = random.uniform(20, 80)
        self.soil_moisture = random.uniform(0.35, 0.65)
        self.slope_angle_deg = random.uniform(15, 40)
        self.vegetation_index = random.uniform(0.3, 0.8)
        self.soil_type = random.randint(0, 3)

        # ---------------- DYNAMICS ----------------
        self.ground_vibration = 0
        self.post_quake_instability = 0

    # ------------------------------------------------
    # 🌍 GEOGRAPHY
    # ------------------------------------------------
    def set_geography(self):
        if self.zone_type == "OFFSHORE":
            self.ocean_depth_m = random.uniform(2000, 5000)
            self.distance_to_coast_km = random.uniform(80, 350)

        elif self.zone_type == "COASTAL":
            self.ocean_depth_m = random.uniform(50, 500)
            self.distance_to_coast_km = random.uniform(5, 60)

        else:  # INLAND
            self.ocean_depth_m = 0
            self.distance_to_coast_km = random.uniform(120, 900)

    # ------------------------------------------------
    # 🔁 PHASE CONTROL
    # ------------------------------------------------
    def update_phase(self):
        if self.system_phase == "BUILDUP" and self.tectonic_stress > 55:
            self.system_phase = "EVENT"

        elif self.system_phase == "EVENT":
            self.system_phase = "RECOVERY"

        elif self.system_phase == "RECOVERY" and self.tectonic_stress < 38:
            self.system_phase = "BUILDUP"

    # ------------------------------------------------
    # 🌋 TECTONICS
    # ------------------------------------------------
    def evolve_tectonics(self):
        if self.system_phase == "BUILDUP":
            self.tectonic_stress += self.strain_rate * random.uniform(1.0, 1.4)

        elif self.system_phase == "EVENT":
            self.tectonic_stress *= random.uniform(0.25, 0.4)
            self.ground_vibration = random.uniform(0.8, 1.4)
            self.post_quake_instability = random.randint(4, 7)

            # Zone migration (plate boundary shift)
            if random.random() < 0.2:
                self.zone_type = random.choice(["OFFSHORE", "COASTAL", "INLAND"])
                self.set_geography()

        else:  # RECOVERY
            self.tectonic_stress *= random.uniform(0.85, 0.93)
            self.ground_vibration *= 0.6

    # ------------------------------------------------
    # 🌧️ TERRAIN EVOLUTION
    # ------------------------------------------------
    def evolve_terrain(self):
        self.rainfall_mm = max(0, min(self.rainfall_mm + random.uniform(-10, 15), 300))
        self.soil_moisture += self.rainfall_mm / 850 + random.uniform(-0.04, 0.04)

        if self.post_quake_instability > 0:
            self.post_quake_instability -= 1
            self.soil_moisture += random.uniform(0.06, 0.12)
            self.slope_angle_deg += random.uniform(1.2, 2.5)
            self.ground_vibration = max(self.ground_vibration, random.uniform(0.5, 1.0))

        self.soil_moisture = min(self.soil_moisture, 1.0)
        self.slope_angle_deg = min(self.slope_angle_deg, 55)

    # ------------------------------------------------
    # 📤 SCENARIO OUTPUT
    # ------------------------------------------------
    def build_scenario(self):
        # --- Magnitude ---
        if self.system_phase == "EVENT":
            if random.random() < 0.15:
                magnitude = random.uniform(7.8, 9.2)   # mega event
            else:
                magnitude = random.uniform(6.8, 7.8)
        else:
            magnitude = random.uniform(4.8, 6.6)

        # --- Depth ---
        depth_km = random.uniform(5, 45)

        # --- Fault mechanics ---
        if self.zone_type in ["OFFSHORE", "COASTAL"] and random.random() < 0.6:
            fault_type = random.choice(["reverse", "normal"])
        else:
            fault_type = random.choice(["normal", "strike-slip"])

        # --- Vertical displacement ---
        if fault_type == "reverse":
            vertical_displacement = random.uniform(0.8, 6.0)
        elif fault_type == "normal":
            vertical_displacement = random.uniform(0.3, 2.0)
        else:
            vertical_displacement = random.uniform(0.05, 0.6)

        return {
            "magnitude": round(magnitude, 2),
            "depth_km": round(depth_km, 1),
            "ocean_depth_m": self.ocean_depth_m,
            "fault_type": fault_type,
            "vertical_displacement_m": round(vertical_displacement, 2),
            "distance_to_coast_km": round(self.distance_to_coast_km, 1),
            "rainfall_mm": round(self.rainfall_mm, 1),
            "soil_moisture": round(self.soil_moisture, 2),
            "slope_angle_deg": round(self.slope_angle_deg, 1),
            "vegetation_index": round(self.vegetation_index, 2),
            "soil_type": self.soil_type,
            "ground_vibration": round(self.ground_vibration, 2),
            "phase": self.system_phase
        }

    # ------------------------------------------------
    # 🔄 STEP
    # ------------------------------------------------
    def get_next_state(self):
        self.evolve_tectonics()
        self.evolve_terrain()
        self.update_phase()
        return self.build_scenario()


# ----------------------------------------------------
# 🔌 ENGINE ACCESS
# ----------------------------------------------------
engine = SimulationEngine()

def generate_scenario():
    return engine.get_next_state()
