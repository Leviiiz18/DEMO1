import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# -------------------------------
# 1. LOAD DATA
# -------------------------------
with open("D:\Codesprint2k25\detection_engine\earthquake_synthetic_dataset.json", "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# -------------------------------
# 2. LABEL ENCODING
# normal -> 0
# earthquake -> 1
# -------------------------------
df["label_encoded"] = df["label"].map({
    "normal": 0,
    "abnormal": 1
})

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
y = df["label_encoded"]

# -------------------------------
# 4. TRAIN / TEST SPLIT
# -------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -------------------------------
# 5. TRAIN MODEL
# -------------------------------
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)
model.fit(X_train, y_train)

# -------------------------------
# 6. EVALUATION
# -------------------------------
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print("Event Classifier Accuracy:", round(accuracy, 3))

# -------------------------------
# 7. PREDICTION FUNCTION
# -------------------------------
def is_earthquake_event(sample):
    """
    sample: dict with seismic features
    returns:
        is_event (True / False)
        confidence (0–1)
    """

    input_data = np.array([[
        sample["p_wave_amplitude"],
        sample["s_wave_amplitude"],
        sample["ps_time_diff_sec"],
        sample["frequency_hz"]
    ]])

    prob = model.predict_proba(input_data)[0][1]

    is_event = prob >= 0.9

    return {
        "is_earthquake": is_event,
        "confidence": round(float(prob), 3)
    }


# -------------------------------
# 8. TEST WITH ONE SAMPLE
# -------------------------------
if __name__ == "__main__":
    test_sample = {
        "p_wave_amplitude": 0.94,
        "s_wave_amplitude": 1.26,
        "ps_time_diff_sec": 6.22,
        "frequency_hz": 3.62
    }

    result = is_earthquake_event(test_sample)
    print("Test Result:", result)
