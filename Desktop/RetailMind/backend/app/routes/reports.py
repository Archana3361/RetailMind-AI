import csv
import io
from fastapi import APIRouter, Depends, Query, Response
from datetime import datetime, timezone, timedelta
from typing import Optional
from app.core.database import get_database
from app.dependencies.auth import get_current_user_id

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    except Exception:
        return None


@router.get("/sales")
async def sales_report(
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    format: str = Query(default="json"),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    match = {"user_id": user_id}
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if start or end:
        match["created_at"] = {}
        if start:
            match["created_at"]["$gte"] = start
        if end:
            match["created_at"]["$lte"] = end

    sales = await db.sales.find(match).sort("created_at", -1).to_list(None)

    rows = []
    for s in sales:
        rows.append({
            "Sale Number": s.get("sale_number", ""),
            "Date": s.get("created_at", "").strftime("%Y-%m-%d %H:%M") if s.get("created_at") else "",
            "Customer": s.get("customer_name", ""),
            "Items": len(s.get("items", [])),
            "Subtotal": s.get("subtotal", 0),
            "Discount": s.get("discount", 0),
            "Total": s.get("total", 0),
            "Gross Profit": s.get("gross_profit", 0),
            "Payment": s.get("payment_method", ""),
        })

    if format == "csv":
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=sales_report.csv"}
        )
    return {"data": rows, "total": len(rows)}


@router.get("/purchases")
async def purchases_report(
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    format: str = Query(default="json"),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    match = {"user_id": user_id}
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if start or end:
        match["created_at"] = {}
        if start:
            match["created_at"]["$gte"] = start
        if end:
            match["created_at"]["$lte"] = end

    purchases = await db.purchases.find(match).sort("created_at", -1).to_list(None)

    rows = []
    for p in purchases:
        rows.append({
            "Purchase Number": p.get("purchase_number", ""),
            "Date": p.get("created_at", "").strftime("%Y-%m-%d %H:%M") if p.get("created_at") else "",
            "Supplier": p.get("supplier_name", ""),
            "Items": len(p.get("items", [])),
            "Subtotal": p.get("subtotal", 0),
            "Discount": p.get("discount", 0),
            "Total": p.get("total", 0),
            "Payment": p.get("payment_method", ""),
        })

    if format == "csv":
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=purchases_report.csv"}
        )
    return {"data": rows, "total": len(rows)}


@router.get("/inventory")
async def inventory_report(
    format: str = Query(default="json"),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    products = await db.products.find({"user_id": user_id, "status": "active"}).sort("name", 1).to_list(None)

    from app.models.product import _get_stock_status
    rows = []
    for p in products:
        ss = _get_stock_status(p.get("current_stock", 0), p.get("minimum_stock", 0))
        rows.append({
            "Product": p.get("name", ""),
            "SKU": p.get("sku", ""),
            "Category": p.get("category_name", ""),
            "Current Stock": p.get("current_stock", 0),
            "Minimum Stock": p.get("minimum_stock", 0),
            "Unit": p.get("unit", "pcs"),
            "Cost Price": p.get("cost_price", 0),
            "Selling Price": p.get("selling_price", 0),
            "Stock Value": round(p.get("current_stock", 0) * p.get("cost_price", 0), 2),
            "Status": ss.replace("_", " ").title(),
        })

    if format == "csv":
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=inventory_report.csv"}
        )
    return {"data": rows, "total": len(rows)}


@router.get("/product-performance")
async def product_performance_report(
    format: str = Query(default="json"),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.product_id",
            "product_name": {"$first": "$items.product_name"},
            "sku": {"$first": "$items.sku"},
            "total_qty_sold": {"$sum": "$items.quantity"},
            "total_revenue": {"$sum": "$items.subtotal"},
            "total_cost": {"$sum": {"$multiply": ["$items.quantity", "$items.cost_price"]}},
            "orders": {"$sum": 1},
        }},
        {"$sort": {"total_revenue": -1}}
    ]
    raw = await db.sales.aggregate(pipeline).to_list(None)

    rows = []
    for r in raw:
        revenue = r.get("total_revenue", 0)
        cost = r.get("total_cost", 0)
        profit = revenue - cost
        rows.append({
            "Product": r.get("product_name", ""),
            "SKU": r.get("sku", ""),
            "Qty Sold": r.get("total_qty_sold", 0),
            "Orders": r.get("orders", 0),
            "Revenue": round(revenue, 2),
            "Cost": round(cost, 2),
            "Gross Profit": round(profit, 2),
            "Margin %": round((profit / revenue * 100) if revenue > 0 else 0, 2),
        })

    if format == "csv":
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=product_performance.csv"}
        )
    return {"data": rows, "total": len(rows)}
