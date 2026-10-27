from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import sys
import os

# Add ml directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ml'))

from clustering.customer_segmentation import segment_customers


async def get_sales_analytics(db, user_id: str, start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None) -> dict:
    match = {"user_id": user_id}
    if start_date or end_date:
        match["created_at"] = {}
        if start_date:
            match["created_at"]["$gte"] = start_date
        if end_date:
            match["created_at"]["$lte"] = end_date

    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$total"},
            "total_orders": {"$sum": 1},
            "total_cost": {"$sum": "$cost_total"},
            "total_gross_profit": {"$sum": "$gross_profit"},
            "total_discount": {"$sum": "$discount"},
        }}
    ]
    result = await db.sales.aggregate(pipeline).to_list(1)
    if not result:
        return {
            "total_revenue": 0.0,
            "total_orders": 0,
            "total_cost": 0.0,
            "gross_profit": 0.0,
            "profit_margin": 0.0,
            "average_order_value": 0.0,
            "total_discount": 0.0,
        }
    r = result[0]
    revenue = r.get("total_revenue", 0.0)
    orders = r.get("total_orders", 0)
    profit = r.get("total_gross_profit", 0.0)
    return {
        "total_revenue": round(revenue, 2),
        "total_orders": orders,
        "total_cost": round(r.get("total_cost", 0.0), 2),
        "gross_profit": round(profit, 2),
        "profit_margin": round((profit / revenue * 100) if revenue > 0 else 0, 2),
        "average_order_value": round(revenue / orders if orders > 0 else 0, 2),
        "total_discount": round(r.get("total_discount", 0.0), 2),
    }


async def get_sales_trend(db, user_id: str, days: int = 30) -> list:
    start = datetime.now(timezone.utc) - timedelta(days=days)
    pipeline = [
        {"$match": {"user_id": user_id, "created_at": {"$gte": start}}},
        {"$group": {
            "_id": {
                "year": {"$year": "$created_at"},
                "month": {"$month": "$created_at"},
                "day": {"$dayOfMonth": "$created_at"},
            },
            "revenue": {"$sum": "$total"},
            "orders": {"$sum": 1},
            "profit": {"$sum": "$gross_profit"},
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}}
    ]
    raw = await db.sales.aggregate(pipeline).to_list(None)
    result = []
    for r in raw:
        d = r["_id"]
        result.append({
            "date": f"{d['year']}-{str(d['month']).zfill(2)}-{str(d['day']).zfill(2)}",
            "revenue": round(r["revenue"], 2),
            "orders": r["orders"],
            "profit": round(r["profit"], 2),
        })
    return result


async def get_top_products(db, user_id: str, limit: int = 10) -> list:
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.product_id",
            "product_name": {"$first": "$items.product_name"},
            "total_qty": {"$sum": "$items.quantity"},
            "total_revenue": {"$sum": "$items.subtotal"},
        }},
        {"$sort": {"total_revenue": -1}},
        {"$limit": limit}
    ]
    raw = await db.sales.aggregate(pipeline).to_list(None)
    return [
        {
            "product_id": str(r["_id"]) if r["_id"] else None,
            "product_name": r["product_name"],
            "total_qty": r["total_qty"],
            "total_revenue": round(r["total_revenue"], 2),
        }
        for r in raw
    ]


async def get_category_performance(db, user_id: str) -> list:
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$unwind": "$items"},
        {"$lookup": {
            "from": "products",
            "let": {"pid": {"$toObjectId": "$items.product_id"}},
            "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", "$$pid"]}}}],
            "as": "product_info"
        }},
        {"$unwind": {"path": "$product_info", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": "$product_info.category_name",
            "total_revenue": {"$sum": "$items.subtotal"},
            "total_qty": {"$sum": "$items.quantity"},
            "orders": {"$sum": 1},
        }},
        {"$sort": {"total_revenue": -1}}
    ]
    raw = await db.sales.aggregate(pipeline).to_list(None)
    return [
        {
            "category": r["_id"] or "Uncategorized",
            "total_revenue": round(r["total_revenue"], 2),
            "total_qty": r["total_qty"],
            "orders": r["orders"],
        }
        for r in raw
    ]


async def get_customer_analytics(db, user_id: str) -> dict:
    total = await db.customers.count_documents({"user_id": user_id})
    repeat_pipeline = [
        {"$match": {"user_id": user_id, "total_orders": {"$gt": 1}}},
        {"$count": "count"}
    ]
    repeat_result = await db.customers.aggregate(repeat_pipeline).to_list(1)
    repeat = repeat_result[0]["count"] if repeat_result else 0

    top_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$sort": {"total_purchases": -1}},
        {"$limit": 5},
        {"$project": {"name": 1, "total_purchases": 1, "total_orders": 1}}
    ]
    top_customers = await db.customers.aggregate(top_pipeline).to_list(None)

    return {
        "total_customers": total,
        "repeat_customers": repeat,
        "new_customers": total - repeat,
        "top_customers": [
            {"name": c["name"], "total_purchases": round(c.get("total_purchases", 0), 2),
             "total_orders": c.get("total_orders", 0)}
            for c in top_customers
        ]
    }


async def get_today_summary(db, user_id: str) -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    pipeline = [
        {"$match": {"user_id": user_id, "created_at": {"$gte": today_start}}},
        {"$group": {
            "_id": None,
            "revenue": {"$sum": "$total"},
            "orders": {"$sum": 1},
            "profit": {"$sum": "$gross_profit"},
        }}
    ]
    result = await db.sales.aggregate(pipeline).to_list(1)
    if result:
        r = result[0]
        return {
            "today_revenue": round(r.get("revenue", 0.0), 2),
            "today_orders": r.get("orders", 0),
            "today_profit": round(r.get("profit", 0.0), 2),
        }
    return {"today_revenue": 0.0, "today_orders": 0, "today_profit": 0.0}


async def get_inventory_analytics(db, user_id: str) -> dict:
    """Inventory analytics by category and stock status."""
    # By category
    category_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$category_name",
            "product_count": {"$sum": 1},
            "total_stock": {"$sum": "$stock"},
            "total_value": {"$sum": {"$multiply": ["$stock", "$cost_price"]}},
        }},
        {"$sort": {"total_value": -1}}
    ]
    by_category = await db.products.aggregate(category_pipeline).to_list(None)
    
    # Stock status
    status_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$stock_status",
            "count": {"$sum": 1},
            "total_stock": {"$sum": "$stock"},
        }}
    ]
    status_raw = await db.products.aggregate(status_pipeline).to_list(None)
    
    return {
        "by_category": [
            {
                "category": r["_id"] or "Uncategorized",
                "product_count": r["product_count"],
                "total_stock": r["total_stock"],
                "total_value": round(r["total_value"], 2)
            }
            for r in by_category
        ],
        "status": [
            {
                "stock_status": r["_id"] or "unknown",
                "count": r["count"],
                "total_stock": r["total_stock"]
            }
            for r in status_raw
        ]
    }


async def get_customer_segmentation(db, user_id: str) -> dict:
    """
    Segment customers using K-Means clustering based on RFM analysis.
    Uses actual sales records from the database.

    Returns:
        dict with:
            - total_customers_registered: count from customers collection
            - total_customers_analyzed: customers with purchase history (eligible for RFM)
            - total_clusters: number of segments identified
            - segments: per-segment summaries with unique labels
            - customer_details: per-customer data (name, segment, orders, spent, last purchase)
            - message: explanation when clustering is not meaningful (optional)
    """
    # Count total registered customers (for context in UI)
    total_registered = await db.customers.count_documents({"user_id": user_id})

    # Fetch all sales for the user
    sales_cursor = db.sales.find({"user_id": user_id})
    sales_records = await sales_cursor.to_list(None)

    if not sales_records or len(sales_records) < 2:
        return {
            "error": "Insufficient sales data for segmentation",
            "message": "Need at least 2 sales records with customer links for segmentation.",
            "total_customers_registered": total_registered,
            "total_customers_analyzed": 0,
            "total_clusters": 0,
            "segments": [],
            "customer_details": [],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    # Convert MongoDB documents to dicts for the clustering module
    sales_data = []
    for sale in sales_records:
        sales_data.append({
            "customer_id": sale.get("customer_id"),
            "total": sale.get("total", 0),
            "created_at": sale.get("created_at")
        })

    # Run segmentation
    customer_segments, summary = segment_customers(sales_data, n_clusters=4)

    if "error" in summary:
        return {
            "error": summary["error"],
            "total_customers_registered": total_registered,
            "total_customers_analyzed": summary.get("total_customers", 0),
            "total_clusters": 0,
            "segments": [],
            "customer_details": [],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    # Fetch customer names for all analyzed customers
    customer_details = summary.get("customer_details", [])
    customer_ids = [d["customer_id"] for d in customer_details]

    # Build a map of customer_id -> name (and last_purchase_date from customer record)
    from bson import ObjectId
    name_map = {}
    last_purchase_map = {}
    if customer_ids:
        object_ids = [ObjectId(cid) for cid in customer_ids]
        customers = await db.customers.find({"_id": {"$in": object_ids}}).to_list(None)
        for c in customers:
            name_map[str(c["_id"])] = c.get("name", "Unknown")
            last_purchase_map[str(c["_id"])] = c.get("last_purchase_date")

    # Enrich customer_details with names and last purchase date
    for d in customer_details:
        cid = d["customer_id"]
        d["customer_name"] = name_map.get(cid, "Unknown")
        # Use the customer record's last_purchase_date if available, else from RFM
        if cid in last_purchase_map and last_purchase_map[cid]:
            d["last_purchase"] = last_purchase_map[cid]
        # last_purchase from RFM calculation is already set by segment_customers

    # Sort customer_details by segment then by monetary (descending)
    customer_details.sort(key=lambda x: (x.get("segment", ""), -x.get("monetary", 0)))

    return {
        "total_customers_registered": total_registered,
        "total_customers_analyzed": len(customer_details),
        "total_clusters": summary.get("total_clusters", 0),
        "segments": summary.get("segments", []),
        "customer_details": customer_details,
        "message": summary.get("message"),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
