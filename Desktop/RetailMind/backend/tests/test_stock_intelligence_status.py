import sys
sys.path.append("C:/Users/hp/Desktop/RetailMind/backend")
sys.path.append("C:/Users/hp/Desktop/RetailMind/ml")

import pytest
from ml.prediction.restock_service import RestockIntelligence


def test_restock_intelligence_status_classification():
    """
    Verify the three canonical statuses and their threshold boundaries:
    1. RESTOCK: stock is insufficient relative to the defined replenishment requirement.
    2. MONITOR: stock is not yet critical but is approaching replenishment threshold or has low coverage.
    3. NO IMMEDIATE ACTION: stock is sufficient for the configured planning horizon.
    """
    ri = RestockIntelligence(safety_stock_ratio=0.15, monitor_threshold=0.25)

    # ----------------------------------------------------
    # Category 1: RESTOCK
    # ----------------------------------------------------
    # Case 1a: Out of stock (current_stock = 0)
    res_zero = ri.calculate(current_stock=0, predicted_demand=30, minimum_stock=5)
    assert res_zero["status"] == "RESTOCK"
    assert res_zero["reorder_quantity"] == res_zero["required_stock"]

    # Case 1b: At or below user-defined minimum stock threshold (current_stock <= minimum_stock)
    res_min = ri.calculate(current_stock=5, predicted_demand=3, minimum_stock=5)
    assert res_min["status"] == "RESTOCK"

    res_below_min = ri.calculate(current_stock=3, predicted_demand=2, minimum_stock=5)
    assert res_below_min["status"] == "RESTOCK"

    # Case 1c: Stock cannot cover expected demand (current_stock < predicted_demand)
    res_below_demand = ri.calculate(current_stock=20, predicted_demand=30, minimum_stock=0)
    assert res_below_demand["status"] == "RESTOCK"
    assert res_below_demand["coverage_ratio"] < 1.0

    # ----------------------------------------------------
    # Category 2: MONITOR
    # ----------------------------------------------------
    # Case 2a: Covers demand, but dips into safety buffer (< required_stock)
    # predicted_demand = 30, safety_stock = round(30*0.15) = 5, required_stock = 35
    # current_stock = 32 covers demand 30, but is below required_stock 35
    res_dip_safety = ri.calculate(current_stock=32, predicted_demand=30, minimum_stock=0)
    assert res_dip_safety["status"] == "MONITOR"
    assert res_dip_safety["reorder_quantity"] == 3

    # Case 2b: Within monitor threshold (+25%) of required stock
    # required_stock = 35, monitor_upper = 35 * 1.25 = 43.75
    # current_stock = 40 (between 35 and 43.75)
    res_within_req_buffer = ri.calculate(current_stock=40, predicted_demand=30, minimum_stock=0)
    assert res_within_req_buffer["status"] == "MONITOR"
    assert res_within_req_buffer["reorder_quantity"] == 0

    # Case 2c: Approaching user-defined minimum stock threshold
    # minimum_stock = 40, predicted_demand = 10, required_stock = 12
    # threshold = max(40, 12) = 40. monitor_upper = 40 * 1.25 = 50.
    # current_stock = 45 is above minimum_stock 40, but within 25% buffer
    res_within_min_buffer = ri.calculate(current_stock=45, predicted_demand=10, minimum_stock=40)
    assert res_within_min_buffer["status"] == "MONITOR"

    # Case 2d: Canonical test_restock.py Example 2
    # current_stock = 35, predicted_demand = 31, safety_stock = 5, required_stock = 36
    res_ex2 = ri.calculate(current_stock=35, predicted_demand=31, minimum_stock=0)
    assert res_ex2["status"] == "MONITOR"

    # ----------------------------------------------------
    # Category 3: NO IMMEDIATE ACTION
    # ----------------------------------------------------
    # Case 3a: Canonical test_restock.py Example 3
    # current_stock = 60, predicted_demand = 31, required_stock = 36
    # 60 > 36 * 1.25 = 45 and coverage = 1.94 > 1.25
    res_ex3 = ri.calculate(current_stock=60, predicted_demand=31, minimum_stock=0)
    assert res_ex3["status"] == "NO IMMEDIATE ACTION"
    assert res_ex3["reorder_quantity"] == 0

    # Case 3b: Ample inventory with minimum stock configured
    # current_stock = 100, predicted_demand = 10, minimum_stock = 40
    # threshold = 40, monitor_upper = 50. 100 > 50 and coverage = 10.0 > 1.25
    res_ample = ri.calculate(current_stock=100, predicted_demand=10, minimum_stock=40)
    assert res_ample["status"] == "NO IMMEDIATE ACTION"


def test_boundary_conditions_and_no_overlap():
    """
    Test strict boundary transitions:
    - At exact minimum threshold: current_stock == minimum_stock -> RESTOCK
    - 1 unit above minimum threshold (when approaching buffer): MONITOR
    - At exact monitor upper boundary: MONITOR
    - 1 unit above monitor upper boundary: NO IMMEDIATE ACTION
    """
    ri = RestockIntelligence(safety_stock_ratio=0.15, monitor_threshold=0.25)

    # Let predicted_demand = 20 -> safety_stock = 3 -> required_stock = 23
    # With minimum_stock = 0: threshold = 23. monitor_upper = 23 * 1.25 = 28.75
    # current_stock < 20 -> RESTOCK (cannot cover demand)
    assert ri.calculate(current_stock=19, predicted_demand=20)["status"] == "RESTOCK"

    # current_stock = 20 -> covers demand, but below required 23 -> MONITOR
    assert ri.calculate(current_stock=20, predicted_demand=20)["status"] == "MONITOR"

    # current_stock = 23 -> equals required 23 -> within monitor buffer (23 <= 28.75) -> MONITOR
    assert ri.calculate(current_stock=23, predicted_demand=20)["status"] == "MONITOR"

    # current_stock = 28 -> within monitor buffer (28 <= 28.75) -> MONITOR
    assert ri.calculate(current_stock=28, predicted_demand=20)["status"] == "MONITOR"

    # current_stock = 29 -> exceeds 28.75 and coverage = 29/20 = 1.45 > 1.25 -> NO IMMEDIATE ACTION
    assert ri.calculate(current_stock=29, predicted_demand=20)["status"] == "NO IMMEDIATE ACTION"


@pytest.mark.asyncio
async def test_backend_stock_intelligence_mapping():
    """
    Verify that get_products_restock_status produces all 3 statuses matching
    the frontend tab filters: ['RESTOCK', 'MONITOR', 'NO IMMEDIATE ACTION'].
    """
    from unittest.mock import AsyncMock, MagicMock
    from datetime import datetime, timezone, timedelta
    import sys
    sys.path.append("backend")
    from app.services import ml_service

    class AsyncCursor:
        def __init__(self, items):
            self._items = items
        async def to_list(self, _):
            return self._items

    now = datetime.now(timezone.utc)

    # Create 3 products targeting each status:
    # Prod A: stock = 5, demand = 30 -> RESTOCK
    # Prod B: stock = 35, demand = 30 -> MONITOR
    # Prod C: stock = 80, demand = 30 -> NO IMMEDIATE ACTION
    products = [
        {
            "_id": "prod_restock",
            "user_id": "u1",
            "name": "Product Restock",
            "sku": "SKU-R",
            "status": "active",
            "current_stock": 5,
            "minimum_stock": 0,
            "selling_price": 50.0,
            "cost_price": 40.0,
            "category_name": "Grocery",
        },
        {
            "_id": "prod_monitor",
            "user_id": "u1",
            "name": "Product Monitor",
            "sku": "SKU-M",
            "status": "active",
            "current_stock": 35,
            "minimum_stock": 0,
            "selling_price": 50.0,
            "cost_price": 40.0,
            "category_name": "Grocery",
        },
        {
            "_id": "prod_safe",
            "user_id": "u1",
            "name": "Product Safe",
            "sku": "SKU-S",
            "status": "active",
            "current_stock": 80,
            "minimum_stock": 0,
            "selling_price": 50.0,
            "cost_price": 40.0,
            "category_name": "Grocery",
        },
    ]

    # Sales history for each product: 30 units/day for 28 days
    sales = []
    for day_offset in range(1, 29):
        sale_dt = now - timedelta(days=day_offset)
        sales.append({
            "user_id": "u1",
            "sale_date": sale_dt,
            "items": [
                {"product_id": "prod_restock", "quantity": 30},
                {"product_id": "prod_monitor", "quantity": 30},
                {"product_id": "prod_safe", "quantity": 30},
            ],
        })

    mock_db = MagicMock()
    mock_db.products.find.return_value = AsyncCursor(products)
    mock_db.sales.find.return_value = AsyncCursor(sales)
    mock_db.predictions.insert_one = AsyncMock()

    ml_service._prediction_service = None
    ml_service._restock_intelligence = RestockIntelligence()

    results = await ml_service.get_products_restock_status(mock_db, "u1")

    # Verify each product gets the expected canonical status
    prod_r = next(p for p in results if p["product_id"] == "prod_restock")
    prod_m = next(p for p in results if p["product_id"] == "prod_monitor")
    prod_s = next(p for p in results if p["product_id"] == "prod_safe")

    assert prod_r["status"] == "RESTOCK"
    assert prod_m["status"] == "MONITOR"
    assert prod_s["status"] == "NO IMMEDIATE ACTION"

    # Verify route summary counts logic
    summary = {
        "restock_count": sum(1 for r in results if r["status"] == "RESTOCK"),
        "monitor_count": sum(1 for r in results if r["status"] == "MONITOR"),
        "safe_count": sum(1 for r in results if r["status"] == "NO IMMEDIATE ACTION"),
        "total_products": len(results),
    }

    assert summary["restock_count"] == 1
    assert summary["monitor_count"] == 1
    assert summary["safe_count"] == 1
    assert summary["total_products"] == 3

    # Verify all statuses are recognized by frontend tab filters
    valid_frontend_tabs = {"RESTOCK", "MONITOR", "NO IMMEDIATE ACTION"}
    for r in results:
        assert r["status"] in valid_frontend_tabs
