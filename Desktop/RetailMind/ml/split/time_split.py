import pandas as pd
from pathlib import Path

# --------------------------------------------------
# 1. Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "features" / "demand_features.csv"
OUTPUT_DIR = BASE_DIR / "split"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# 2. Load feature-engineered dataset
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE)

df["Date"] = pd.to_datetime(df["Date"])

df = df.sort_values("Date").reset_index(drop=True)

print("Dataset loaded:", df.shape)

print(
    "Date range:",
    df["Date"].min().date(),
    "to",
    df["Date"].max().date()
)

# --------------------------------------------------
# 3. Define split dates
# --------------------------------------------------

train_end = pd.Timestamp("2023-11-30")
validation_start = pd.Timestamp("2023-12-01")
validation_end = pd.Timestamp("2023-12-31")
test_start = pd.Timestamp("2024-01-01")

# --------------------------------------------------
# 4. Create datasets
# --------------------------------------------------

train_df = df[df["Date"] <= train_end].copy()

validation_df = df[
    (df["Date"] >= validation_start)
    & (df["Date"] <= validation_end)
].copy()

test_df = df[
    df["Date"] >= test_start
].copy()

# --------------------------------------------------
# 5. Reset indexes
# --------------------------------------------------

train_df.reset_index(drop=True, inplace=True)
validation_df.reset_index(drop=True, inplace=True)
test_df.reset_index(drop=True, inplace=True)

# --------------------------------------------------
# 6. Display split information
# --------------------------------------------------

print("\nDataset Split")
print("-" * 50)

print(
    f"Training   : {train_df.shape[0]:,} rows | "
    f"{train_df['Date'].min().date()} → "
    f"{train_df['Date'].max().date()}"
)

print(
    f"Validation : {validation_df.shape[0]:,} rows | "
    f"{validation_df['Date'].min().date()} → "
    f"{validation_df['Date'].max().date()}"
)

print(
    f"Test       : {test_df.shape[0]:,} rows | "
    f"{test_df['Date'].min().date()} → "
    f"{test_df['Date'].max().date()}"
)

# --------------------------------------------------
# 7. Leakage checks
# --------------------------------------------------

print("\nLeakage Check")
print("-" * 50)

print(
    "Training maximum date:",
    train_df["Date"].max().date()
)

print(
    "Validation minimum date:",
    validation_df["Date"].min().date()
)

print(
    "Validation maximum date:",
    validation_df["Date"].max().date()
)

print(
    "Test minimum date:",
    test_df["Date"].min().date()
)

if train_df["Date"].max() < validation_df["Date"].min():
    print("PASS: Training ends before validation begins.")
else:
    print("FAIL: Training/validation overlap detected.")

if validation_df["Date"].max() < test_df["Date"].min():
    print("PASS: Validation ends before test begins.")
else:
    print("FAIL: Validation/test overlap detected.")

# --------------------------------------------------
# 8. Save datasets
# --------------------------------------------------

train_df.to_csv(
    OUTPUT_DIR / "train.csv",
    index=False
)

validation_df.to_csv(
    OUTPUT_DIR / "validation.csv",
    index=False
)

test_df.to_csv(
    OUTPUT_DIR / "test.csv",
    index=False
)

print("\nFiles saved:")
print(OUTPUT_DIR / "train.csv")
print(OUTPUT_DIR / "validation.csv")
print(OUTPUT_DIR / "test.csv")