import json
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ----------------------------------
# 1. LOAD TSUNAMI DATASET (ONLY)
# ----------------------------------
with open(
    r"D:\Codesprint2k25\detection_engine\tsunami_synthetic_dataset.json",
    "r"
) as f:
    data = json.load(f)

df = pd.DataFrame(data)

# ----------------------------------
# 2. ENCODE LABELS
# no_tsunami -> 0
# tsunami_risk -> 1
# ----------------------------------
df = df[df["label"].isin(["no_tsunami", "tsunami_risk"])]

df["label_encoded"] = df["label"].map({
    "no_tsunami": 0,
    "tsunami_risk": 1
})

print("Label distribution:")
print(df["label_encoded"].value_counts())

# ----------------------------------
# 3. ENCODE FAULT TYPE
# ----------------------------------
df["fault_type_encoded"] = df["fault_type"].map({
    "normal": 0,
    "strike-slip": 1,
    "reverse": 2
})

# ----------------------------------
# 4. FEATURES & TARGET
# ----------------------------------
FEATURES = [
    "magnitude",
    "depth_km",
    "ocean_depth_m",
    "fault_type_encoded",
    "vertical_displacement_m",
    "distance_to_coast_km"
]

X = df[FEATURES]
y = df["label_encoded"]

# ----------------------------------
# 5. TRAIN / TEST SPLIT
# ----------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# ----------------------------------
# 6. TRAIN MODEL
# ----------------------------------
tsunami_model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)
tsunami_model.fit(X_train, y_train)

# ----------------------------------
# 7. EVALUATION
# ----------------------------------
y_pred = tsunami_model.predict(X_test)
print("Tsunami Model Accuracy:",
      round(accuracy_score(y_test, y_pred), 3))

# ----------------------------------
# 8. TSUNAMI EVALUATION FUNCTION
# ----------------------------------
def evaluate_tsunami(sample):
    """
    sample = {
        magnitude,
        depth_km,
        ocean_depth_m,
        fault_type,
        vertical_displacement_m,
        distance_to_coast_km
    }
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

    tsunami_prob = tsunami_model.predict_proba(input_df)[0][1]

    # PHYSICAL SAFETY RULES (FINAL DECISION)
    tsunami_alert = (
        sample["magnitude"] >= 6.5 and
        sample["depth_km"] <= 70 and
        sample["fault_type"] == "reverse" and
        sample["vertical_displacement_m"] >= 0.5 and
        tsunami_prob >= 0.75
    )

    return {
        "tsunami_probability": round(float(tsunami_prob), 3),
        "tsunami_alert": tsunami_alert
    }

# ----------------------------------
# 9. TEST CASES
# ----------------------------------
if __name__ == "__main__":

    no_tsunami_case = {
        "magnitude": 5.07,
        "depth_km": 75.1,
        "ocean_depth_m": 2924.0,
        "fault_type": "normal",
        "vertical_displacement_m": 0.02,
        "distance_to_coast_km": 778.5
    }

    tsunami_case = {
        "magnitude": 9.02,
        "depth_km": 18.3,
        "ocean_depth_m": 4002.0,
        "fault_type": "reverse",
        "vertical_displacement_m": 7.91,
        "distance_to_coast_km": 79.4
    }

    print("No Tsunami:", evaluate_tsunami(no_tsunami_case))
    print("Tsunami Risk:", evaluate_tsunami(tsunami_case))
