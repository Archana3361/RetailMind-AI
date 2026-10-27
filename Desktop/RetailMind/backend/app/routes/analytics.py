from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone
from typing import Optional
from app.core.database import get_database
from app.dependencies.auth import get_current_user_id
from app.services.analytics_service import (
    get_sales_analytics, get_sales_trend, get_top_products,
    get_category_performance, get_customer_analytics,
    get_inventory_analytics, get_customer_segmentation
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    except Exception:
        return None


@router.get("/sales")
async def sales_analytics(
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    return await get_sales_analytics(db, user_id, _parse_date(start_date), _parse_date(end_date))


@router.get("/trend")
async def sales_trend(
    days: int = Query(default=30, ge=7, le=365),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    return await get_sales_trend(db, user_id, days)


@router.get("/products/top")
async def top_products(
    limit: int = Query(default=10, ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    return await get_top_products(db, user_id, limit)


@router.get("/products/categories")
async def category_performance(
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    return await get_category_performance(db, user_id)


@router.get("/customers")
async def customer_analytics(
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    return await get_customer_analytics(db, user_id)


@router.get("/customer-segments")
async def customer_segments(
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    """
    Get customer segmentation based on RFM analysis.
    Segments customers into groups like Loyal, Regular, Occasional, At-Risk.
    """
    return await get_customer_segmentation(db, user_id)


@router.get("/inventory")
async def inventory_analytics(
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    from app.services.inventory_service import get_inventory_summary

    summary = await get_inventory_summary(db, user_id)

    # Stock movement last 30 days
    from datetime import timedelta
    start = datetime.now(timezone.utc) - timedelta(days=30)
    pipeline = [
        {"$match": {"user_id": user_id, "created_at": {"$gte": start}}},
        {"$group": {
            "_id": "$transaction_type",
            "total_qty": {"$sum": {"$abs": "$quantity_change"}},
            "count": {"$sum": 1}
        }}
    ]
    movement = await db.inventory_transactions.aggregate(pipeline).to_list(None)

    return {
        "summary": summary,
        "stock_movement": [
            {"type": m["_id"], "total_qty": m["total_qty"], "count": m["count"]}
            for m in movement
        ]
    }
