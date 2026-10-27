import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


# ==================================================
# 1. Paths
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = BASE_DIR / "processed" / "demand_preprocessed.csv"

df = pd.read_csv(DATA_FILE)

print("=" * 60)
print("RETAILMIND AI - EXPLORATORY DATA ANALYSIS")
print("=" * 60)


# ==================================================
# 2. Basic Information
# ==================================================

print("\nDataset Shape:")
print(df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nData Types:")
print(df.dtypes)

print("\nFirst 5 Rows:")
print(df.head())


# ==================================================
# 3. Unique Values
# ==================================================

print("\n" + "=" * 60)
print("UNIQUE VALUES")
print("=" * 60)

print("Stores:", df["Store_ID"].nunique())
print("Products:", df["Product_ID"].nunique())
print("Categories:", df["Category"].nunique())
print("Regions:", df["Region"].nunique())

print("\nCategories:")
print(df["Category"].unique())

print("\nRegions:")
print(df["Region"].unique())


# ==================================================
# 4. Demand Statistics
# ==================================================

print("\n" + "=" * 60)
print("DEMAND STATISTICS")
print("=" * 60)

print(df["Demand"].describe())


# ==================================================
# 5. Numerical Summary
# ==================================================

numeric_columns = [
    "Inventory_Level",
    "Units_Sold",
    "Units_Ordered",
    "Price",
    "Discount",
    "Competitor_Pricing",
    "Demand"
]

print("\nNumerical Summary:")
print(df[numeric_columns].describe().round(2))


# ==================================================
# 6. Demand Distribution
# ==================================================

plt.figure(figsize=(10, 6))

sns.histplot(
    df["Demand"],
    bins=40,
    kde=True
)

plt.title("Demand Distribution")
plt.xlabel("Demand")
plt.ylabel("Frequency")
plt.tight_layout()

plt.savefig(
    BASE_DIR / "eda" / "demand_distribution.png",
    dpi=150
)

plt.show()


# ==================================================
# 7. Demand Over Time
# ==================================================

daily_demand = (
    df.groupby("Date")["Demand"]
    .mean()
    .reset_index()
)

daily_demand["Date"] = pd.to_datetime(
    daily_demand["Date"]
)

plt.figure(figsize=(14, 6))

plt.plot(
    daily_demand["Date"],
    daily_demand["Demand"]
)

plt.title("Average Daily Demand Over Time")
plt.xlabel("Date")
plt.ylabel("Average Demand")
plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig(
    BASE_DIR / "eda" / "demand_over_time.png",
    dpi=150
)

plt.show()


# ==================================================
# 8. Demand by Category
# ==================================================

category_demand = (
    df.groupby("Category")["Demand"]
    .mean()
    .sort_values(ascending=False)
)

print("\nAverage Demand by Category:")
print(category_demand.round(2))

plt.figure(figsize=(10, 6))

category_demand.plot(
    kind="bar"
)

plt.title("Average Demand by Category")
plt.xlabel("Category")
plt.ylabel("Average Demand")

plt.xticks(rotation=45)

plt.tight_layout()

plt.savefig(
    BASE_DIR / "eda" / "demand_by_category.png",
    dpi=150
)

plt.show()


# ==================================================
# 9. Demand by Store
# ==================================================

store_demand = (
    df.groupby("Store_ID")["Demand"]
    .mean()
    .sort_values(ascending=False)
)

print("\nAverage Demand by Store:")
print(store_demand.round(2))

plt.figure(figsize=(10, 6))

store_demand.plot(
    kind="bar"
)

plt.title("Average Demand by Store")
plt.xlabel("Store")
plt.ylabel("Average Demand")

plt.tight_layout()

plt.savefig(
    BASE_DIR / "eda" / "demand_by_store.png",
    dpi=150
)

plt.show()


# ==================================================
# 10. Demand by Product
# ==================================================

product_demand = (
    df.groupby("Product_ID")["Demand"]
    .mean()
    .sort_values(ascending=False)
)

print("\nTop 10 Products by Average Demand:")
print(product_demand.head(10).round(2))

print("\nBottom 10 Products by Average Demand:")
print(product_demand.tail(10).round(2))


# ==================================================
# 11. Demand vs Inventory
# ==================================================

plt.figure(figsize=(10, 6))

sns.scatterplot(
    data=df,
    x="Inventory_Level",
    y="Demand",
    alpha=0.4
)

plt.title("Demand vs Inventory Level")
plt.xlabel("Inventory Level")
plt.ylabel("Demand")

plt.tight_layout()

plt.savefig(
    BASE_DIR / "eda" / "demand_vs_inventory.png",
    dpi=150
)

plt.show()


# ==================================================
# 12. Demand vs Price
# ==================================================

plt.figure(figsize=(10, 6))

sns.scatterplot(
    data=df,
    x="Price",
    y="Demand",
    alpha=0.4
)

plt.title("Demand vs Price")
plt.xlabel("Price")
plt.ylabel("Demand")

plt.tight_layout()

plt.savefig(
    BASE_DIR / "eda" / "demand_vs_price.png",
    dpi=150
)

plt.show()


# ==================================================
# 13. Demand vs Discount
# ==================================================

plt.figure(figsize=(10, 6))

sns.boxplot(
    data=df,
    x="Discount",
    y="Demand"
)

plt.title("Demand by Discount Level")
plt.xlabel("Discount (%)")
plt.ylabel("Demand")

plt.tight_layout()

plt.savefig(
    BASE_DIR / "eda" / "demand_vs_discount.png",
    dpi=150
)

plt.show()


# ==================================================
# 14. Demand with Promotion
# ==================================================

promotion_demand = (
    df.groupby("Promotion")["Demand"]
    .mean()
)

print("\nAverage Demand by Promotion:")
print(promotion_demand.round(2))

plt.figure(figsize=(8, 6))

promotion_demand.plot(
    kind="bar"
)

plt.title("Average Demand: Promotion vs No Promotion")
plt.xlabel("Promotion")
plt.ylabel("Average Demand")

plt.tight_layout()

plt.savefig(
    BASE_DIR / "eda" / "demand_promotion.png",
    dpi=150
)

plt.show()


# ==================================================
# 15. Demand by Weather
# ==================================================

weather_demand = (
    df.groupby("Weather_Condition")["Demand"]
    .mean()
    .sort_values(ascending=False)
)

print("\nAverage Demand by Weather:")
print(weather_demand.round(2))


# ==================================================
# 16. Demand by Season
# ==================================================

season_demand = (
    df.groupby("Seasonality")["Demand"]
    .mean()
    .sort_values(ascending=False)
)

print("\nAverage Demand by Season:")
print(season_demand.round(2))


# ==================================================
# 17. Correlation Analysis
# ==================================================

correlation_columns = [
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

correlation = (
    df[correlation_columns]
    .corr()
    .round(3)
)

print("\n" + "=" * 60)
print("CORRELATION WITH DEMAND")
print("=" * 60)

print(
    correlation["Demand"]
    .sort_values(ascending=False)
)


# ==================================================
# 18. Correlation Heatmap
# ==================================================

plt.figure(figsize=(12, 8))

sns.heatmap(
    correlation,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0
)

plt.title("Correlation Heatmap")

plt.tight_layout()

plt.savefig(
    BASE_DIR / "eda" / "correlation_heatmap.png",
    dpi=150
)

plt.show()


# ==================================================
# 19. Final Summary
# ==================================================

print("\n" + "=" * 60)
print("EDA COMPLETED")
print("=" * 60)

print("\nGenerated charts:")
print("1. demand_distribution.png")
print("2. demand_over_time.png")
print("3. demand_by_category.png")
print("4. demand_by_store.png")
print("5. demand_vs_inventory.png")
print("6. demand_vs_price.png")
print("7. demand_vs_discount.png")
print("8. demand_promotion.png")
print("9. correlation_heatmap.png")