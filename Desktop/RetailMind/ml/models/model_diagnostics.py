import pandas as pd
import numpy as np
import joblib

from pathlib import Path

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

import matplotlib.pyplot as plt


# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "models"
SPLIT_DIR = BASE_DIR / "split"

OUTPUT_DIR = MODEL_DIR / "diagnostics"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. Load model and test data
# --------------------------------------------------

model = joblib.load(
    MODEL_DIR / "best_model.pkl"
)

X_test = joblib.load(
    MODEL_DIR / "X_test.pkl"
)

y_test = joblib.load(
    MODEL_DIR / "y_test.pkl"
)

test_df = pd.read_csv(
    SPLIT_DIR / "test.csv"
)

test_df["Date"] = pd.to_datetime(
    test_df["Date"]
)


print("Model loaded successfully")

print(
    "Test features:",
    X_test.shape
)

print(
    "Test target:",
    y_test.shape
)


# --------------------------------------------------
# 3. Generate predictions
# --------------------------------------------------

predictions = model.predict(X_test)

predictions = np.maximum(
    predictions,
    0
)


# --------------------------------------------------
# 4. Calculate metrics
# --------------------------------------------------

mae = mean_absolute_error(
    y_test,
    predictions
)

rmse = np.sqrt(
    mean_squared_error(
        y_test,
        predictions
    )
)

r2 = r2_score(
    y_test,
    predictions
)


print("\nModel Performance")
print("=" * 50)

print(
    f"MAE  : {mae:.2f}"
)

print(
    f"RMSE : {rmse:.2f}"
)

print(
    f"R²   : {r2:.4f}"
)


# --------------------------------------------------
# 5. Prediction error
# --------------------------------------------------

errors = y_test - predictions

print("\nPrediction Error")
print("=" * 50)

print(
    f"Mean Error       : {errors.mean():.2f}"
)

print(
    f"Mean Absolute Error: {np.abs(errors).mean():.2f}"
)

print(
    f"Minimum Error    : {errors.min():.2f}"
)

print(
    f"Maximum Error    : {errors.max():.2f}"
)


# --------------------------------------------------
# 6. Create prediction results table
# --------------------------------------------------

results = test_df[
    [
        "Date",
        "Store_ID",
        "Product_ID",
        "Category",
        "Demand"
    ]
].copy()

results["Predicted_Demand"] = predictions

results["Prediction_Error"] = (
    results["Demand"]
    - results["Predicted_Demand"]
)

results["Absolute_Error"] = (
    results["Prediction_Error"]
    .abs()
)


# --------------------------------------------------
# 7. Save predictions
# --------------------------------------------------

prediction_file = (
    OUTPUT_DIR /
    "test_predictions.csv"
)

results.to_csv(
    prediction_file,
    index=False
)


# --------------------------------------------------
# 8. Display sample predictions
# --------------------------------------------------

print("\nSample Predictions")
print("=" * 80)

print(
    results[
        [
            "Date",
            "Store_ID",
            "Product_ID",
            "Demand",
            "Predicted_Demand",
            "Prediction_Error"
        ]
    ].head(15).to_string(
        index=False
    )
)


# --------------------------------------------------
# 9. Actual vs Predicted plot
# --------------------------------------------------

plt.figure(figsize=(10, 6))

sample_size = min(
    500,
    len(results)
)

plot_data = results.head(
    sample_size
)

plt.plot(
    plot_data["Demand"].values,
    label="Actual Demand"
)

plt.plot(
    plot_data["Predicted_Demand"].values,
    label="Predicted Demand"
)

plt.title(
    "Actual vs Predicted Demand"
)

plt.xlabel(
    "Test Records"
)

plt.ylabel(
    "Demand"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR /
    "actual_vs_predicted.png",
    dpi=150
)

plt.close()


# --------------------------------------------------
# 10. Error distribution
# --------------------------------------------------

plt.figure(figsize=(10, 6))

plt.hist(
    errors,
    bins=40
)

plt.title(
    "Prediction Error Distribution"
)

plt.xlabel(
    "Prediction Error"
)

plt.ylabel(
    "Frequency"
)

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR /
    "prediction_error_distribution.png",
    dpi=150
)

plt.close()


# --------------------------------------------------
# 11. Feature importance
# --------------------------------------------------

if hasattr(model, "feature_importances_"):

    preprocessor = joblib.load(
        MODEL_DIR /
        "preprocessor.pkl"
    )

    feature_names = (
        preprocessor
        .get_feature_names_out()
    )

    importance = model.feature_importances_

    importance_df = pd.DataFrame({
        "Feature": feature_names,
        "Importance": importance
    })

    importance_df = (
        importance_df
        .sort_values(
            "Importance",
            ascending=False
        )
        .reset_index(drop=True)
    )

    importance_df.to_csv(
        OUTPUT_DIR /
        "feature_importance.csv",
        index=False
    )

    print("\nTop 15 Important Features")
    print("=" * 50)

    print(
        importance_df.head(15).to_string(
            index=False
        )
    )


# --------------------------------------------------
# 12. Final output
# --------------------------------------------------

print("\nDiagnostics completed successfully.")

print("\nSaved files:")

print(
    OUTPUT_DIR /
    "test_predictions.csv"
)

print(
    OUTPUT_DIR /
    "actual_vs_predicted.png"
)

print(
    OUTPUT_DIR /
    "prediction_error_distribution.png"
)

if hasattr(model, "feature_importances_"):

    print(
        OUTPUT_DIR /
        "feature_importance.csv"
    )