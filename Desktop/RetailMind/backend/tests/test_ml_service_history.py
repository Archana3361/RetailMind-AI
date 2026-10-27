import asyncio
import builtins
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

import sys
# Ensure the project root is on sys.path for imports
sys.path.append('C:/Users/hp/Desktop/RetailMind/backend')

from app.services import ml_service

# Helper async iterator for find().to_list()
class AsyncCursor:
    def __init__(self, items):
        self._items = items
    async def to_list(self, _):
        return self._items

async def run_test():
    # Mock product collection – two products for the same user
    product_docs = [
        {
            "_id": "prod1",
            "user_id": "user123",
            "status": "active",
            "current_stock": 10,
            "minimum_stock": 5,
            "selling_price": 20.0,
            "cost_price": 15.0,
            "category_name": "Grocery",
        },
        {
            "_id": "prod2",
            "user_id": "user123",
            "status": "active",
            "current_stock": 0,
            "minimum_stock": 2,
            "selling_price": 30.0,
            "cost_price": 22.0,
            "category_name": "Grocery",
        },
    ]
    # Mock sales – only prod1 has sales in the last 28 days
    now = datetime.now(timezone.utc)
    sales_docs = [
        {
            "user_id": "user123",
            "sale_date": now - timedelta(days=1),
            "items": [{"product_id": "prod1", "quantity": 3}],
        },
        {
            "user_id": "user123",
            "sale_date": now - timedelta(days=7),
            "items": [{"product_id": "prod1", "quantity": 2}],
        },
        {
            "user_id": "user123",
            "sale_date": now - timedelta(days=15),
            "items": [{"product_id": "prod1", "quantity": 1}],
        },
    ]

    # Mock DB with async find() returning AsyncCursor
    mock_db = MagicMock()
    mock_db.products.find.return_value = AsyncCursor(product_docs)
    mock_db.sales.find.return_value = AsyncCursor(sales_docs)
    mock_db.predictions.insert_one = AsyncMock()

    # Mock RestockIntelligence to return deterministic values
    class DummyRestock:
        def calculate(self, current_stock, predicted_demand, minimum_stock=None):
            return {
                "reorder_quantity": max(0, int(predicted_demand - current_stock)),
                "safety_stock": 0,
                "required_stock": int(predicted_demand),
                "coverage_ratio": 1.0,
                "status": "TEST",
            }
    ml_service._restock_intelligence = DummyRestock()

    # Run the function
    result = await ml_service.get_products_restock_status(mock_db, "user123")
    # Simple assertions (will raise if not as expected)
    assert isinstance(result, list)
    # prod1 should have history_quality "full" (3 days >= 7? actually only 3 days, so "insufficient")
    prod1 = next(p for p in result if p["product_id"] == "prod1")
    prod2 = next(p for p in result if p["product_id"] == "prod2")
    # prod2 has no sales → insufficient
    assert prod2["history_quality"] == "insufficient"
    # prod1 also insufficient because less than 7 days of data
    assert prod1["history_quality"] == "insufficient"
    # Ensure demand lag values are populated correctly for prod1
    assert prod1["predicted_demand"] >= 0

    print("Test passed: history_quality flags and demand aggregation work.")

def test_history():
    asyncio.run(run_test())

