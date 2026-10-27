from fastapi import APIRouter, Depends, Query
from app.core.database import get_database
from app.models.product import product_helper, _get_stock_status
from app.dependencies.auth import get_current_user_id
from app.services.inventory_service import get_inventory_summary

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("/")
async def get_inventory(
    search: str = Query(default=""),
    stock_status: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    query = {"user_id": user_id, "status": "active"}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
        ]
    
    # Apply stock_status filter in database query for accurate pagination
    if stock_status:
        if stock_status == "low_stock":
            query["$expr"] = {"$lte": ["$current_stock", "$minimum_stock"]}
        elif stock_status == "out_of_stock":
            query["current_stock"] = 0
        elif stock_status == "in_stock":
            query["$expr"] = {"$gt": ["$current_stock", "$minimum_stock"]}

    total = await db.products.count_documents(query)
    skip = (page - 1) * per_page
    products = await db.products.find(query).sort("name", 1).skip(skip).limit(per_page).to_list(None)

    items = []
    for p in products:
        stock_s = _get_stock_status(p.get("current_stock", 0), p.get("minimum_stock", 0))
        items.append({
            "product_id": str(p["_id"]),
            "name": p["name"],
            "sku": p.get("sku", ""),
            "category": p.get("category_name", ""),
            "current_stock": p.get("current_stock", 0),
            "minimum_stock": p.get("minimum_stock", 0),
            "unit": p.get("unit", "pcs"),
            "cost_price": p.get("cost_price", 0.0),
            "selling_price": p.get("selling_price", 0.0),
            "stock_value": round(p.get("current_stock", 0) * p.get("cost_price", 0.0), 2),
            "stock_status": stock_s,
            "supplier_name": p.get("supplier_name", ""),
            "updated_at": p.get("updated_at"),
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/summary")
async def get_summary(
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    return await get_inventory_summary(db, user_id)


@router.get("/transactions")
async def get_transactions(
    product_id: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=30, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    query = {"user_id": user_id}
    if product_id:
        query["product_id"] = product_id

    total = await db.inventory_transactions.count_documents(query)
    skip = (page - 1) * per_page
    txns = await db.inventory_transactions.find(query).sort("created_at", -1).skip(skip).limit(per_page).to_list(None)

    items = []
    for t in txns:
        items.append({
            "id": str(t["_id"]),
            "product_id": t.get("product_id"),
            "product_name": t.get("product_name", ""),
            "sku": t.get("sku", ""),
            "transaction_type": t.get("transaction_type"),
            "quantity_change": t.get("quantity_change"),
            "stock_before": t.get("stock_before"),
            "stock_after": t.get("stock_after"),
            "notes": t.get("notes", ""),
            "created_at": t.get("created_at"),
        })

    return {"items": items, "total": total, "page": page, "per_page": per_page}
