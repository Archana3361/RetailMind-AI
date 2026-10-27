from fastapi import APIRouter, Depends
from app.core.database import get_database
from app.dependencies.auth import get_current_user_id
from app.services.analytics_service import get_today_summary, get_sales_trend
from app.services.inventory_service import get_inventory_summary
from app.services.ml_service import get_products_restock_status

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/")
async def get_dashboard(
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    # Run all queries in parallel via separate awaits (motor is async)
    today = await get_today_summary(db, user_id)
    inventory = await get_inventory_summary(db, user_id)
    trend = await get_sales_trend(db, user_id, days=14)

    # Recent sales
    recent_sales_raw = await db.sales.find({"user_id": user_id}).sort("created_at", -1).limit(5).to_list(None)
    from app.models.sale import sale_helper
    recent_sales = [sale_helper(s) for s in recent_sales_raw]

    # Stock alerts (products at or below minimum)
    low_stock_raw = await db.products.find({
        "user_id": user_id,
        "status": "active",
        "$expr": {"$lte": ["$current_stock", "$minimum_stock"]}
    }).sort("current_stock", 1).limit(5).to_list(None)

    low_stock = [
        {
            "product_id": str(p["_id"]),
            "name": p["name"],
            "sku": p.get("sku", ""),
            "current_stock": p.get("current_stock", 0),
            "minimum_stock": p.get("minimum_stock", 0),
        }
        for p in low_stock_raw
    ]

    # AI restock preview (top 8)
    restock_data = await get_products_restock_status(db, user_id)
    restock_preview = restock_data[:8]

    return {
        "today": today,
        "inventory": inventory,
        "sales_trend": trend,
        "recent_sales": recent_sales,
        "low_stock_alerts": low_stock,
        "restock_preview": restock_preview,
    }
