import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
import pytest
import sys

sys.path.append("C:/Users/hp/Desktop/RetailMind/backend")

from app.services import ml_service
from ml.prediction.restock_service import RestockIntelligence


class AsyncCursor:
    def __init__(self, items):
        self._items = items

    async def to_list(self, _):
        return self._items


@pytest.mark.asyncio
async def test_low_volume_forecast_and_restock():
    """
    Test:
    1. Actual sales of 3 units/day for 28 days -> forecast ~3 units/day.
    2. Low-volume products never revert to inflated ML predictions during 7-day forecast.
    3. Reorder quantity and stock coverage are consistent with real RestockIntelligence:
       reorder_quantity == max(0, required_stock - current_stock)
    """
    now = datetime.now(timezone.utc)

    # Low-volume product: current_stock=20, minimum_stock=5
    products = [
        {
            "_id": "prod_low_vol",
            "user_id": "test_user",
            "name": "Low Volume Item",
            "sku": "SKU-LOW",
            "status": "active",
            "current_stock": 20,
            "minimum_stock": 5,
            "selling_price": 50.0,
            "cost_price": 40.0,
            "category_name": "Grocery",
        },
        {
            "_id": "prod_low_vol_need_restock",
            "user_id": "test_user",
            "name": "Low Volume Item Need Restock",
            "sku": "SKU-LOW-RESTOCK",
            "status": "active",
            "current_stock": 2,
            "minimum_stock": 5,
            "selling_price": 50.0,
            "cost_price": 40.0,
            "category_name": "Grocery",
        },
    ]

    # 28 days of sales at 3 units/day for both products
    sales = []
    for day_offset in range(1, 29):
        sale_dt = now - timedelta(days=day_offset)
        sales.append({
            "user_id": "test_user",
            "sale_date": sale_dt,
            "items": [
                {"product_id": "prod_low_vol", "quantity": 3},
                {"product_id": "prod_low_vol_need_restock", "quantity": 3},
            ],
        })

    mock_db = MagicMock()
    mock_db.products.find.return_value = AsyncCursor(products)
    mock_db.sales.find.return_value = AsyncCursor(sales)
    mock_db.predictions.insert_one = AsyncMock()

    # Ensure real RestockIntelligence is used
    ml_service._restock_intelligence = RestockIntelligence()

    results = await ml_service.get_products_restock_status(mock_db, "test_user")

    assert len(results) == 2

    prod1 = next(r for r in results if r["product_id"] == "prod_low_vol")
    assert prod1["history_quality"] == "full"
    # Predicted demand should be ~3 units/day
    assert abs(prod1["predicted_demand"] - 3.0) < 0.1

    # 7-day forecast should all be ~3 units/day, never inflated
    assert len(prod1["forecast_7d"]) == 7
    for f in prod1["forecast_7d"]:
        assert abs(f["predicted_demand"] - 3.0) < 0.1, f"Forecast inflated: {f}"

    # Real RestockIntelligence checks:
    # avg_daily = 3.0, safety_stock = round(3.0 * 0.15) = 0, required_stock = 3
    # reorder_quantity = max(0, 3 - 20) = 0
    assert prod1["required_stock"] == 3
    assert prod1["reorder_quantity"] == 0
    assert prod1["reorder_quantity"] == max(0, prod1["required_stock"] - prod1["current_stock"])
    assert round(prod1["coverage_ratio"], 2) == round(20 / 3.0, 2)

    # Second product: current_stock=2, minimum_stock=5
    prod2 = next(r for r in results if r["product_id"] == "prod_low_vol_need_restock")
    assert prod2["history_quality"] == "full"
    assert abs(prod2["predicted_demand"] - 3.0) < 0.1
    for f in prod2["forecast_7d"]:
        assert abs(f["predicted_demand"] - 3.0) < 0.1
    # required_stock = 3, reorder_quantity = max(0, 3 - 2) = 1
    assert prod2["required_stock"] == 3
    assert prod2["reorder_quantity"] == 1
    assert prod2["reorder_quantity"] == max(0, prod2["required_stock"] - prod2["current_stock"])
    assert prod2["status"] == "RESTOCK"


@pytest.mark.asyncio
async def test_normal_volume_uses_model():
    """
    Normal-volume products (rolling average >= 5 units/day) must continue
    to use the ML model pipeline.
    """
    now = datetime.now(timezone.utc)
    products = [
        {
            "_id": "prod_normal_vol",
            "user_id": "test_user",
            "name": "Normal Volume Item",
            "sku": "SKU-NORM",
            "status": "active",
            "current_stock": 50,
            "minimum_stock": 10,
            "selling_price": 50.0,
            "cost_price": 40.0,
            "category_name": "Grocery",
        }
    ]

    # 28 days of sales at 25 units/day (well above 5 units/day threshold)
    sales = []
    for day_offset in range(1, 29):
        sale_dt = now - timedelta(days=day_offset)
        sales.append({
            "user_id": "test_user",
            "sale_date": sale_dt,
            "items": [
                {"product_id": "prod_normal_vol", "quantity": 25},
            ],
        })

    mock_db = MagicMock()
    mock_db.products.find.return_value = AsyncCursor(products)
    mock_db.sales.find.return_value = AsyncCursor(sales)
    mock_db.predictions.insert_one = AsyncMock()

    # Track that model predictor is called
    mock_predictor = MagicMock()
    mock_predictor.predict.return_value = [35.0]
    ml_service._prediction_service = mock_predictor
    ml_service._restock_intelligence = RestockIntelligence()

    results = await ml_service.get_products_restock_status(mock_db, "test_user")

    assert len(results) == 1
    res = results[0]
    assert res["history_quality"] == "full"
    # Verify mock_predictor.predict was called for normal volume
    assert mock_predictor.predict.called
    assert res["predicted_demand"] == 35.0
    assert len(res["forecast_7d"]) == 7


@pytest.mark.asyncio
async def test_insufficient_history_fallback():
    """
    Insufficient history (<7 days) must remain flagged as 'insufficient'
    and retain category fallback.
    """
    now = datetime.now(timezone.utc)
    products = [
        {
            "_id": "prod_sparse",
            "user_id": "test_user",
            "name": "Sparse Item",
            "sku": "SKU-SPARSE",
            "status": "active",
            "current_stock": 10,
            "minimum_stock": 5,
            "selling_price": 50.0,
            "cost_price": 40.0,
            "category_name": "Grocery",
        }
    ]

    # Only 2 days of sales in the last 28 days
    sales = [
        {
            "user_id": "test_user",
            "sale_date": now - timedelta(days=2),
            "items": [{"product_id": "prod_sparse", "quantity": 2}],
        },
        {
            "user_id": "test_user",
            "sale_date": now - timedelta(days=5),
            "items": [{"product_id": "prod_sparse", "quantity": 1}],
        },
    ]

    mock_db = MagicMock()
    mock_db.products.find.return_value = AsyncCursor(products)
    mock_db.sales.find.return_value = AsyncCursor(sales)
    mock_db.predictions.insert_one = AsyncMock()

    ml_service._restock_intelligence = RestockIntelligence()

    results = await ml_service.get_products_restock_status(mock_db, "test_user")
    assert len(results) == 1
    assert results[0]["history_quality"] == "insufficient"


@pytest.mark.asyncio
async def test_mid_volume_27_to_30_units():
    """
    Regression test for sequence [27, 29, 30, 28, 27, 30, 29]:
    A product with ~28.5 units/day historical sales must predict ~28-29 units/day,
    NOT the inflated ~110 units from the synthetic public training dataset.
    """
    now = datetime.now(timezone.utc)
    products = [
        {
            "_id": "prod_mid_vol",
            "user_id": "test_user",
            "name": "Mid Volume Item",
            "sku": "SKU-MID",
            "status": "active",
            "current_stock": 30,
            "minimum_stock": 10,
            "selling_price": 100.0,
            "cost_price": 80.0,
            "category_name": "Grocery",
        }
    ]

    # Historical demand sequence: [27, 29, 30, 28, 27, 30, 29] repeated across 28 days
    seq = [27, 29, 30, 28, 27, 30, 29]
    sales = []
    for day_offset in range(1, 29):
        sale_dt = now - timedelta(days=day_offset)
        qty = seq[(day_offset - 1) % len(seq)]
        sales.append({
            "user_id": "test_user",
            "sale_date": sale_dt,
            "items": [{"product_id": "prod_mid_vol", "quantity": qty}],
        })

    mock_db = MagicMock()
    mock_db.products.find.return_value = AsyncCursor(products)
    mock_db.sales.find.return_value = AsyncCursor(sales)
    mock_db.predictions.insert_one = AsyncMock()

    # Load real ML service predictor and restock intelligence
    ml_service._prediction_service = None  # Force reload singleton
    ml_service._restock_intelligence = RestockIntelligence()

    results = await ml_service.get_products_restock_status(mock_db, "test_user")

    assert len(results) == 1
    res = results[0]
    assert res["history_quality"] == "full"

    # Baseline 7d mean is 200/7 = 28.57
    expected_baseline = sum(seq) / len(seq)
    assert abs(res["predicted_demand"] - round(expected_baseline, 0)) <= 1.0, (
        f"Predicted demand {res['predicted_demand']} is inflated! Expected ~{expected_baseline:.2f}"
    )

    # 7-day forecast must all be around ~28.6, never inflated to ~110
    assert len(res["forecast_7d"]) == 7
    for f in res["forecast_7d"]:
        assert abs(f["predicted_demand"] - expected_baseline) <= 2.0, (
            f"Forecast day inflated: {f}"
        )

    # Required stock = round(28.57 + round(28.57 * 0.15)) = 33
    # Current stock = 30 -> reorder_quantity = max(0, 33 - 30) = 3
    assert res["required_stock"] == 33
    assert res["reorder_quantity"] == 3
    assert res["reorder_quantity"] == max(0, res["required_stock"] - res["current_stock"])


@pytest.mark.asyncio
async def test_predict_demand_api_form_inputs():
    """
    Test the Demand Prediction screen input form:
    yesterday (lag 1) = 30, lag 7 = 28, lag 14 = 29, lag 28 = 27,
    7-day rolling mean = 29, 14-day = 28.5, 28-day = 28.
    Must return ~29 units, NOT ~110 units.
    """
    mock_db = MagicMock()
    mock_db.predictions.insert_one = AsyncMock()

    ml_service._prediction_service = None  # Reload real service

    form_inputs = {
        "category": "Grocery",
        "region": "North",
        "weather_condition": "Sunny",
        "seasonality": "Regular",
        "price": 100.0,
        "discount": 0.0,
        "promotion": 0,
        "competitor_pricing": 105.0,
        "inventory_level": 50.0,
        "demand_lag_1": 30.0,
        "demand_lag_7": 28.0,
        "demand_lag_14": 29.0,
        "demand_lag_28": 27.0,
        "demand_rolling_mean_7": 29.0,
        "demand_rolling_mean_14": 28.5,
        "demand_rolling_mean_28": 28.0,
    }

    result = await ml_service.predict_demand(mock_db, "user_test", form_inputs)

    assert "predicted_demand" in result
    pred = result["predicted_demand"]

    # Verify prediction is calibrated to ~29 units, not 110
    assert abs(pred - 29.0) <= 1.0, f"Demand prediction inflated: {pred}, expected ~29.0"

