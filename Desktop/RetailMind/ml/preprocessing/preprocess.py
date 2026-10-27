import pandas as pd
from pathlib import Path


# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "demand_forecasting.csv"
OUTPUT_DIR = BASE_DIR / "processed"
OUTPUT_FILE = OUTPUT_DIR / "demand_preprocessed.csv"

OUTPUT_DIR.mkdir(exist_ok=True)


# --------------------------------------------------
# 2. Load dataset
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

print("Original shape:", df.shape)


# --------------------------------------------------
# 3. Clean column names
# --------------------------------------------------

df.columns = (
    df.columns
    .str.strip()
    .str.replace(" ", "_")
)


# --------------------------------------------------
# 4. Convert Date
# --------------------------------------------------

df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
)


# --------------------------------------------------
# 5. Check invalid dates
# --------------------------------------------------

invalid_dates = df["Date"].isna().sum()

print("Invalid dates:", invalid_dates)


# Remove only invalid dates if any exist
df = df.dropna(subset=["Date"])


# --------------------------------------------------
# 6. Remove exact duplicate rows
# --------------------------------------------------

before = len(df)

df = df.drop_duplicates()

after = len(df)

print("Duplicate rows removed:", before - after)


# --------------------------------------------------
# 7. Check missing values
# --------------------------------------------------

missing = df.isnull().sum()

print("\nMissing values:")
print(missing[missing > 0])


# --------------------------------------------------
# 8. Convert numeric columns
# --------------------------------------------------

numeric_columns = [
    "Inventory_Level",
    "Units_Sold",
    "Units_Ordered",
    "Price",
    "Discount",
    "Promotion",
    "Competitor_Pricing",
    "Epidemic",
    "Demand"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# --------------------------------------------------
# 9. Remove rows with invalid numeric values
# --------------------------------------------------

df = df.dropna(
    subset=numeric_columns
)


# --------------------------------------------------
# 10. Check impossible negative values
# --------------------------------------------------

non_negative_columns = [
    "Inventory_Level",
    "Units_Sold",
    "Units_Ordered",
    "Price",
    "Discount",
    "Competitor_Pricing",
    "Demand"
]

for column in non_negative_columns:

    invalid_count = (
        df[column] < 0
    ).sum()

    print(
        f"{column} negative values:",
        invalid_count
    )

    if invalid_count > 0:
        df = df[
            df[column] >= 0
        ]


# --------------------------------------------------
# 11. Sort chronologically
# --------------------------------------------------

df = df.sort_values(
    by=[
        "Store_ID",
        "Product_ID",
        "Date"
    ]
).reset_index(drop=True)


# --------------------------------------------------
# 12. Create date features
# --------------------------------------------------

df["Day"] = df["Date"].dt.day

df["Day_of_Week"] = (
    df["Date"].dt.dayofweek
)

df["Week"] = (
    df["Date"].dt.isocalendar().week.astype(int)
)

df["Month"] = df["Date"].dt.month

df["Quarter"] = (
    df["Date"].dt.quarter
)

df["Year"] = df["Date"].dt.year

df["Is_Weekend"] = (
    df["Day_of_Week"] >= 5
).astype(int)


# --------------------------------------------------
# 13. Save preprocessed dataset
# --------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# --------------------------------------------------
# 14. Final information
# --------------------------------------------------

print("\nPreprocessing completed.")

print("Final shape:", df.shape)

print(
    "Saved to:",
    OUTPUT_FILE
)