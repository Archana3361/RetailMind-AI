from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.core.database import get_database
from app.dependencies.auth import get_current_user_id
from app.services import ml_service

router = APIRouter(prefix="/api/ml", tags=["ML / AI Intelligence"])


class DemandPredictRequest(BaseModel):
    store_id: int = Field(default=1, ge=1)
    product_id: int = Field(default=1, ge=1)
    category: str = Field(default="Grocery")
    region: str = Field(default="North")
    weather_condition: str = Field(default="Sunny")
    seasonality: str = Field(default="Regular")
    inventory_level: float = Field(default=50.0, ge=0)
    price: float = Field(default=100.0, ge=0)
    discount: float = Field(default=0.0, ge=0)
    promotion: int = Field(default=0, ge=0, le=1)
    competitor_pricing: float = Field(default=105.0, ge=0)
    epidemic: int = Field(default=0, ge=0, le=1)
    demand_lag_1: float = Field(default=30.0, ge=0)
    demand_lag_7: float = Field(default=28.0, ge=0)
    demand_lag_14: float = Field(default=29.0, ge=0)
    demand_lag_28: float = Field(default=27.0, ge=0)
    demand_rolling_mean_7: float = Field(default=29.0, ge=0)
    demand_rolling_mean_14: float = Field(default=28.5, ge=0)
    demand_rolling_mean_28: float = Field(default=28.0, ge=0)


class RestockRequest(BaseModel):
    product_id: str
    current_stock: float = Field(..., ge=0)
    store_id: int = Field(default=1)
    category: str = Field(default="Grocery")
    price: float = Field(default=100.0, ge=0)
    discount: float = Field(default=0.0, ge=0)
    promotion: int = Field(default=0)
    demand_lag_1: float = Field(default=30.0, ge=0)
    demand_lag_7: float = Field(default=28.0, ge=0)
    demand_lag_14: float = Field(default=29.0, ge=0)
    demand_lag_28: float = Field(default=27.0, ge=0)
    demand_rolling_mean_7: float = Field(default=29.0, ge=0)
    demand_rolling_mean_14: float = Field(default=28.5, ge=0)
    demand_rolling_mean_28: float = Field(default=28.0, ge=0)


@router.get("/model-info")
async def model_info(user_id: str = Depends(get_current_user_id)):
    return ml_service.get_model_info()


@router.post("/predict-demand")
async def predict_demand(
    data: DemandPredictRequest,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    try:
        result = await ml_service.predict_demand(db, user_id, data.model_dump())
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/restock-recommendation")
async def restock_recommendation(
    data: RestockRequest,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    try:
        result = await ml_service.get_restock_recommendation(
            db, user_id, data.product_id, data.current_stock, data.model_dump()
        )
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/stock-intelligence")
async def stock_intelligence(
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    """
    Run restock intelligence across all active products.
    Returns RESTOCK / MONITOR / NO IMMEDIATE ACTION for each product.
    """
    try:
        results = await ml_service.get_products_restock_status(db, user_id)
        summary = {
            "restock_count": sum(1 for r in results if r["status"] == "RESTOCK"),
            "monitor_count": sum(1 for r in results if r["status"] == "MONITOR"),
            "safe_count": sum(1 for r in results if r["status"] == "NO IMMEDIATE ACTION"),
            "total_products": len(results),
        }
        return {"summary": summary, "products": results}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
