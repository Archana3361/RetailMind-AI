from restock_service import (
    RestockIntelligence
)


service = RestockIntelligence()


# --------------------------------------------------
# Example 1: Restock
# --------------------------------------------------

result = service.calculate(
    current_stock=8,
    predicted_demand=31
)

print("\nExample 1")
print("=" * 50)

for key, value in result.items():

    print(
        f"{key}: {value}"
    )


# --------------------------------------------------
# Example 2: Monitor
# --------------------------------------------------

result = service.calculate(
    current_stock=35,
    predicted_demand=31
)

print("\nExample 2")
print("=" * 50)

for key, value in result.items():

    print(
        f"{key}: {value}"
    )


# --------------------------------------------------
# Example 3: No immediate action
# --------------------------------------------------

result = service.calculate(
    current_stock=60,
    predicted_demand=31
)

print("\nExample 3")
print("=" * 50)

for key, value in result.items():

    print(
        f"{key}: {value}"
    )