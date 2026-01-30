import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score

# -------------------------------
# 1. LOAD DATA
# -------------------------------
with open(r"D:\Codesprint2k25\detection_engine\earthquake_synthetic_dataset.json", "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# -------------------------------
# 2. KEEP ONLY EARTHQUAKE EVENTS
# -------------------------------
df = df[df["label"] == "abnormal"].reset_index(drop=True)

# -------------------------------
# 3. FEATURE SELECTION
# -------------------------------
FEATURES = [
    "p_wave_amplitude",
    "s_wave_amplitude",
    "ps_time_diff_sec",
    "frequency_hz"
]

X = df[FEATURES]

# -------------------------------
# 4. CREATE SYNTHETIC TARGETS
# -------------------------------

# 4.1 Magnitude (synthetic but realistic)
df["magnitude"] = (
    df["p_wave_amplitude"] + df["s_wave_amplitude"]
) * 2.5

# 4.2 Depth (already exists in dataset)
y_depth = df["depth_km"]

# 4.3 Epicenter (synthetic land / ocean)
# Even longitude → ocean, Odd → land
df["epicenter"] = df["longitude"].apply(
    lambda x: 1 if int(abs(x)) % 2 == 0 else 0
)  # 1 = ocean, 0 = land

# Targets
y_mag = df["magnitude"]
y_epi = df["epicenter"]

# -------------------------------
# 5. TRAIN / TEST SPLIT
# -------------------------------
X_train, X_test, y_mag_train, y_mag_test = train_test_split(
    X, y_mag, test_size=0.2, random_state=42
)

_, _, y_depth_train, y_depth_test = train_test_split(
    X, y_depth, test_size=0.2, random_state=42
)

_, _, y_epi_train, y_epi_test = train_test_split(
    X, y_epi, test_size=0.2, random_state=42
)

# -------------------------------
# 6. TRAIN MODELS
# -------------------------------
mag_model = RandomForestRegressor(n_estimators=100, random_state=42)
depth_model = RandomForestRegressor(n_estimators=100, random_state=42)
epi_model = RandomForestClassifier(n_estimators=100, random_state=42)

mag_model.fit(X_train, y_mag_train)
depth_model.fit(X_train, y_depth_train)
epi_model.fit(X_train, y_epi_train)

# -------------------------------
# 7. EVALUATION
# -------------------------------
print("Magnitude MAE:",
      round(mean_absolute_error(y_mag_test, mag_model.predict(X_test)), 2))

print("Depth MAE:",
      round(mean_absolute_error(y_depth_test, depth_model.predict(X_test)), 2))

print("Epicenter Accuracy:",
      round(accuracy_score(y_epi_test, epi_model.predict(X_test)), 2))

# -------------------------------
# 8. PREDICTION FUNCTION
# -------------------------------
def predict_earthquake(features):
    """
    Input: dict of seismic features
    Output:
      magnitude
      depth_km
      epicenter (land / ocean)
    """

    input_df = pd.DataFrame([features])

    magnitude = mag_model.predict(input_df)[0]
    depth = depth_model.predict(input_df)[0]
    epicenter = epi_model.predict(input_df)[0]

    return {
        "magnitude": round(float(magnitude), 2),
        "depth_km": round(float(depth), 2),
        "epicenter": "ocean" if epicenter == 1 else "land"
    }

# -------------------------------
# 9. TEST SAMPLE
# -------------------------------
if __name__ == "__main__":
    test_sample = {
        "p_wave_amplitude": 2.6,
        "s_wave_amplitude": 3.1,
        "ps_time_diff_sec": 8.9,
        "frequency_hz": 1.6
    }

    result = predict_earthquake(test_sample)
    print("Earthquake Prediction:", result)
