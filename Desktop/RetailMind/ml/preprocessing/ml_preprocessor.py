import pandas as pd
from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib


# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

SPLIT_DIR = BASE_DIR / "split"
MODEL_DIR = BASE_DIR / "models"

MODEL_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. Load datasets
# --------------------------------------------------

train = pd.read_csv(SPLIT_DIR / "train.csv")
validation = pd.read_csv(SPLIT_DIR / "validation.csv")
test = pd.read_csv(SPLIT_DIR / "test.csv")

print("Datasets loaded")

print("Train:", train.shape)
print("Validation:", validation.shape)
print("Test:", test.shape)


# --------------------------------------------------
# 3. Convert date
# --------------------------------------------------

for df in [train, validation, test]:
    df["Date"] = pd.to_datetime(df["Date"])


# --------------------------------------------------
# 4. Define target
# --------------------------------------------------

TARGET = "Demand"


# --------------------------------------------------
# 5. Define features
# --------------------------------------------------

categorical_features = [
    "Store_ID",
    "Product_ID",
    "Category",
    "Region",
    "Weather_Condition",
    "Seasonality"
]

numerical_features = [
    "Inventory_Level",
    "Price",
    "Discount",
    "Promotion",
    "Competitor_Pricing",
    "Epidemic",
    "Day",
    "Day_of_Week",
    "Week",
    "Month",
    "Quarter",
    "Year",
    "Is_Weekend",
    "Demand_lag_1",
    "Demand_lag_7",
    "Demand_lag_14",
    "Demand_lag_28",
    "Demand_rolling_mean_7",
    "Demand_rolling_mean_14",
    "Demand_rolling_mean_28"
]

FEATURES = categorical_features + numerical_features


# --------------------------------------------------
# 6. Separate X and y
# --------------------------------------------------

X_train = train[FEATURES]
y_train = train[TARGET]

X_validation = validation[FEATURES]
y_validation = validation[TARGET]

X_test = test[FEATURES]
y_test = test[TARGET]


# --------------------------------------------------
# 7. Preprocessing pipelines
# --------------------------------------------------

categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="most_frequent")
        ),
        (
            "encoder",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False
            )
        )
    ]
)


numerical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median")
        ),
        (
            "scaler",
            StandardScaler()
        )
    ]
)


preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            categorical_pipeline,
            categorical_features
        ),
        (
            "numerical",
            numerical_pipeline,
            numerical_features
        )
    ]
)


# --------------------------------------------------
# 8. Fit ONLY on training data
# --------------------------------------------------

print("\nFitting preprocessor on training data...")

X_train_processed = preprocessor.fit_transform(X_train)

X_validation_processed = preprocessor.transform(
    X_validation
)

X_test_processed = preprocessor.transform(
    X_test
)


# --------------------------------------------------
# 9. Display results
# --------------------------------------------------

print("\nPreprocessing completed")

print(
    "Processed training shape:",
    X_train_processed.shape
)

print(
    "Processed validation shape:",
    X_validation_processed.shape
)

print(
    "Processed test shape:",
    X_test_processed.shape
)


# --------------------------------------------------
# 10. Save processed arrays
# --------------------------------------------------

joblib.dump(
    X_train_processed,
    MODEL_DIR / "X_train.pkl"
)

joblib.dump(
    X_validation_processed,
    MODEL_DIR / "X_validation.pkl"
)

joblib.dump(
    X_test_processed,
    MODEL_DIR / "X_test.pkl"
)

joblib.dump(
    y_train.to_numpy(),
    MODEL_DIR / "y_train.pkl"
)

joblib.dump(
    y_validation.to_numpy(),
    MODEL_DIR / "y_validation.pkl"
)

joblib.dump(
    y_test.to_numpy(),
    MODEL_DIR / "y_test.pkl"
)


# --------------------------------------------------
# 11. Save preprocessor
# --------------------------------------------------

joblib.dump(
    preprocessor,
    MODEL_DIR / "preprocessor.pkl"
)


# --------------------------------------------------
# 12. Save feature information
# --------------------------------------------------

joblib.dump(
    FEATURES,
    MODEL_DIR / "feature_columns.pkl"
)

print("\nSaved files:")
print(MODEL_DIR / "X_train.pkl")
print(MODEL_DIR / "X_validation.pkl")
print(MODEL_DIR / "X_test.pkl")
print(MODEL_DIR / "y_train.pkl")
print(MODEL_DIR / "y_validation.pkl")
print(MODEL_DIR / "y_test.pkl")
print(MODEL_DIR / "preprocessor.pkl")
print(MODEL_DIR / "feature_columns.pkl")