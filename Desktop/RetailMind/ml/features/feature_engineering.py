import pandas as pd
from pathlib import Path

# ----------------------------------------
# 1. Define project paths
# ----------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "processed" / "demand_preprocessed.csv"
OUTPUT_DIR = BASE_DIR / "features"
OUTPUT_FILE = OUTPUT_DIR / "demand_features.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------
# 2. Load preprocessed dataset
# ----------------------------------------

df = pd.read_csv(INPUT_FILE)

df["Date"] = pd.to_datetime(df["Date"])

# Sort data chronologically within each
# store-product combination
df = df.sort_values(
    ["Store_ID", "Product_ID", "Date"]
).reset_index(drop=True)

print("Dataset loaded:", df.shape)


# ----------------------------------------
# 3. Create demand lag features
# ----------------------------------------

grouped_demand = df.groupby(
    ["Store_ID", "Product_ID"]
)["Demand"]

df["Demand_lag_1"] = grouped_demand.shift(1)
df["Demand_lag_7"] = grouped_demand.shift(7)
df["Demand_lag_14"] = grouped_demand.shift(14)
df["Demand_lag_28"] = grouped_demand.shift(28)


# ----------------------------------------
# 4. Create rolling mean features
# ----------------------------------------

# Shift by one day first so that the
# current day's demand is never included.

df["Demand_rolling_mean_7"] = (
    df.groupby(["Store_ID", "Product_ID"])["Demand"]
    .transform(
        lambda series: series.shift(1).rolling(
            window=7,
            min_periods=7
        ).mean()
    )
)

df["Demand_rolling_mean_14"] = (
    df.groupby(["Store_ID", "Product_ID"])["Demand"]
    .transform(
        lambda series: series.shift(1).rolling(
            window=14,
            min_periods=14
        ).mean()
    )
)

df["Demand_rolling_mean_28"] = (
    df.groupby(["Store_ID", "Product_ID"])["Demand"]
    .transform(
        lambda series: series.shift(1).rolling(
            window=28,
            min_periods=28
        ).mean()
    )
)


# ----------------------------------------
# 5. Remove rows without enough history
# ----------------------------------------

feature_columns = [
    "Demand_lag_1",
    "Demand_lag_7",
    "Demand_lag_14",
    "Demand_lag_28",
    "Demand_rolling_mean_7",
    "Demand_rolling_mean_14",
    "Demand_rolling_mean_28"
]

df = df.dropna(subset=feature_columns).copy()

# Save the result
df.to_csv(OUTPUT_FILE, index=False)


# ----------------------------------------
# 6. Verify the output
# ----------------------------------------

print("\nFeature engineering completed.")
print("Final dataset shape:", df.shape)

print("\nNew features:")
for column in feature_columns:
    print(column)

print("\nMissing values in new features:")
print(df[feature_columns].isnull().sum())

print("\nDate range:")
print(df["Date"].min(), "to", df["Date"].max())

print("\nSaved file:")
print(OUTPUT_FILE)