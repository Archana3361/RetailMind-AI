import pandas as pd

from prediction_service import (
    DemandPredictionService
)


# --------------------------------------------------
# Load service
# --------------------------------------------------

service = DemandPredictionService()

print("Prediction service loaded successfully.")


# --------------------------------------------------
# Load one test record
# --------------------------------------------------

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

test_file = (
    BASE_DIR
    / "split"
    / "test.csv"
)

test_df = pd.read_csv(
    test_file
)


# --------------------------------------------------
# Select one record
# --------------------------------------------------

sample = test_df.iloc[0]


# --------------------------------------------------
# Prepare input
# --------------------------------------------------

input_data = [
    sample.to_dict()
]


# --------------------------------------------------
# Predict
# --------------------------------------------------

prediction = service.predict(
    input_data
)


# --------------------------------------------------
# Display result
# --------------------------------------------------

print("\nPrediction Test")
print("=" * 50)

print(
    "Store:",
    sample["Store_ID"]
)

print(
    "Product:",
    sample["Product_ID"]
)

print(
    "Actual Demand:",
    sample["Demand"]
)

print(
    "Predicted Demand:",
    round(
        float(prediction[0]),
        2
    )
)