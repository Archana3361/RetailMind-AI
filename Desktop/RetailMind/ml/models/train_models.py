import pandas as pd
import numpy as np
import joblib

from pathlib import Path

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import HistGradientBoostingRegressor

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "models"

# --------------------------------------------------
# 2. Load preprocessed data
# --------------------------------------------------

X_train = joblib.load(MODEL_DIR / "X_train.pkl")
X_validation = joblib.load(
    MODEL_DIR / "X_validation.pkl"
)

X_test = joblib.load(
    MODEL_DIR / "X_test.pkl"
)

y_train = joblib.load(
    MODEL_DIR / "y_train.pkl"
)

y_validation = joblib.load(
    MODEL_DIR / "y_validation.pkl"
)

y_test = joblib.load(
    MODEL_DIR / "y_test.pkl"
)


print("Data loaded successfully")

print("X_train:", X_train.shape)
print("X_validation:", X_validation.shape)
print("X_test:", X_test.shape)


# --------------------------------------------------
# 3. Define models
# --------------------------------------------------

models = {

    "Linear Regression": LinearRegression(),

    "Random Forest": RandomForestRegressor(
        n_estimators=150,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    ),

    "HistGradientBoosting": HistGradientBoostingRegressor(
        max_iter=300,
        learning_rate=0.05,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        random_state=42
    )
}


# --------------------------------------------------
# 4. Evaluation function
# --------------------------------------------------

def evaluate_model(model, X, y):

    predictions = model.predict(X)

    mae = mean_absolute_error(
        y,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            y,
            predictions
        )
    )

    r2 = r2_score(
        y,
        predictions
    )

    return mae, rmse, r2


# --------------------------------------------------
# 5. Train models
# --------------------------------------------------

results = []

trained_models = {}


for name, model in models.items():

    print("\n" + "=" * 60)
    print("Training:", name)
    print("=" * 60)

    model.fit(
        X_train,
        y_train
    )

    # Validation evaluation
    val_mae, val_rmse, val_r2 = evaluate_model(
        model,
        X_validation,
        y_validation
    )

    print("\nValidation Results")

    print(
        f"MAE  : {val_mae:.2f}"
    )

    print(
        f"RMSE : {val_rmse:.2f}"
    )

    print(
        f"R²   : {val_r2:.4f}"
    )

    # Test evaluation
    test_mae, test_rmse, test_r2 = evaluate_model(
        model,
        X_test,
        y_test
    )

    print("\nTest Results")

    print(
        f"MAE  : {test_mae:.2f}"
    )

    print(
        f"RMSE : {test_rmse:.2f}"
    )

    print(
        f"R²   : {test_r2:.4f}"
    )

    results.append({
        "Model": name,

        "Validation_MAE": val_mae,
        "Validation_RMSE": val_rmse,
        "Validation_R2": val_r2,

        "Test_MAE": test_mae,
        "Test_RMSE": test_rmse,
        "Test_R2": test_r2
    })

    trained_models[name] = model


# --------------------------------------------------
# 6. Create results table
# --------------------------------------------------

results_df = pd.DataFrame(results)

print("\n\nMODEL COMPARISON")
print("=" * 80)

print(
    results_df.to_string(
        index=False
    )
)


# --------------------------------------------------
# 7. Select best model
# --------------------------------------------------
# Lower MAE is better.

best_model_name = results_df.loc[
    results_df["Validation_MAE"].idxmin(),
    "Model"
]

best_model = trained_models[
    best_model_name
]


print("\n" + "=" * 80)

print(
    "Selected Model:",
    best_model_name
)

print("=" * 80)


# --------------------------------------------------
# 8. Save model comparison
# --------------------------------------------------

results_df.to_csv(
    MODEL_DIR / "model_comparison.csv",
    index=False
)


# --------------------------------------------------
# 9. Save selected model
# --------------------------------------------------

joblib.dump(
    best_model,
    MODEL_DIR / "best_model.pkl"
)


# --------------------------------------------------
# 10. Save model name
# --------------------------------------------------

with open(
    MODEL_DIR / "best_model_name.txt",
    "w"
) as file:

    file.write(
        best_model_name
    )


print("\nSaved:")

print(
    MODEL_DIR / "model_comparison.csv"
)

print(
    MODEL_DIR / "best_model.pkl"
)

print(
    MODEL_DIR / "best_model_name.txt"
)