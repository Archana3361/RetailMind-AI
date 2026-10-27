from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from datetime import datetime, timezone
from app.core.database import get_database
from app.schemas.purchase import PurchaseCreate
from app.models.purchase import purchase_helper
from app.dependencies.auth import get_current_user_id
from app.services.inventory_service import adjust_stock

router = APIRouter(prefix="/api/purchases", tags=["Purchases"])


async def _generate_purchase_number(db, user_id: str) -> str:
    count = await db.purchases.count_documents({"user_id": user_id})
    return f"PO-{str(count + 1).zfill(5)}"


@router.get("/")
async def list_purchases(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    query = {"user_id": user_id}
    total = await db.purchases.count_documents(query)
    skip = (page - 1) * per_page
    purchases = await db.purchases.find(query).sort("created_at", -1).skip(skip).limit(per_page).to_list(None)
    return {
        "items": [purchase_helper(p) for p in purchases],
        "total": total, "page": page, "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.post("/", status_code=201)
async def create_purchase(
    data: PurchaseCreate,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    items = []
    subtotal = 0.0

    for item in data.items:
        product = await db.products.find_one({
            "_id": ObjectId(item.product_id), "user_id": user_id
        })
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found.")
        line_total = item.quantity * item.unit_cost
        subtotal += line_total
        items.append({
            "product_id": item.product_id,
            "product_name": product["name"],
            "sku": product.get("sku", ""),
            "quantity": item.quantity,
            "unit_cost": item.unit_cost,
            "subtotal": round(line_total, 2),
        })

    total = max(0.0, subtotal - data.discount)

    supplier_name = ""
    if data.supplier_id:
        supplier = await db.suppliers.find_one({"_id": ObjectId(data.supplier_id), "user_id": user_id})
        if supplier:
            supplier_name = supplier["name"]

    # Resolve purchase number
    purchase_number = (data.purchase_number or "").strip()
    if purchase_number:
        existing = await db.purchases.find_one({"user_id": user_id, "purchase_number": purchase_number})
        if existing:
            purchase_number = await _generate_purchase_number(db, user_id)
    else:
        purchase_number = await _generate_purchase_number(db, user_id)

    # Resolve purchase date
    now = datetime.now(timezone.utc)
    purchase_date = now
    if data.purchase_date:
        try:
            if len(data.purchase_date) == 10:
                purchase_date = datetime.strptime(data.purchase_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            else:
                purchase_date = datetime.fromisoformat(data.purchase_date.replace("Z", "+00:00"))
        except Exception:
            purchase_date = now

    # Payment calculations
    payment_status = (data.payment_status or "paid").lower()
    if payment_status not in ["paid", "partial", "unpaid"]:
        payment_status = "paid"

    if data.amount_paid is not None:
        amount_paid = round(float(data.amount_paid), 2)
    elif payment_status == "paid":
        amount_paid = round(total, 2)
    elif payment_status == "unpaid":
        amount_paid = 0.0
    else:
        amount_paid = round(data.amount_paid or 0.0, 2)

    amount_paid = max(0.0, min(amount_paid, round(total, 2))) if total > 0 else 0.0
    balance_due = max(0.0, round(total - amount_paid, 2))

    if total > 0:
        if amount_paid >= total:
            payment_status = "paid"
        elif amount_paid == 0.0:
            payment_status = "unpaid"
        else:
            payment_status = "partial"
    else:
        payment_status = "paid"
        balance_due = 0.0
        amount_paid = 0.0

    purchase_doc = {
        "user_id": user_id,
        "purchase_number": purchase_number,
        "purchase_date": purchase_date,
        "supplier_id": data.supplier_id,
        "supplier_name": supplier_name,
        "supplier_invoice_number": (data.supplier_invoice_number or "").strip(),
        "items": items,
        "subtotal": round(subtotal, 2),
        "discount": round(data.discount, 2),
        "total": round(total, 2),
        "payment_method": data.payment_method,
        "payment_status": payment_status,
        "amount_paid": amount_paid,
        "balance_due": balance_due,
        "notes": data.notes or "",
        "created_at": purchase_date,
    }

    result = await db.purchases.insert_one(purchase_doc)
    purchase_id = str(result.inserted_id)

    # Increase inventory
    for item in items:
        await adjust_stock(
            db, user_id, item["product_id"], item["quantity"],
            "purchase", purchase_id, "purchase",
            f"Purchase {purchase_number}"
        )
        # Update product cost price to latest
        await db.products.update_one(
            {"_id": ObjectId(item["product_id"])},
            {"$set": {"cost_price": item["unit_cost"], "updated_at": now}}
        )

    # Update supplier stats
    if data.supplier_id:
        await db.suppliers.update_one(
            {"_id": ObjectId(data.supplier_id)},
            {
                "$inc": {"total_purchase_value": round(total, 2), "total_orders": 1},
                "$set": {"last_purchase_date": purchase_date, "updated_at": now}
            }
        )

    created = await db.purchases.find_one({"_id": result.inserted_id})
    return purchase_helper(created)


@router.get("/next-number")
async def get_next_purchase_number(
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    next_num = await _generate_purchase_number(db, user_id)
    return {"purchase_number": next_num}


@router.get("/{purchase_id}")
async def get_purchase(
    purchase_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    purchase = await db.purchases.find_one({"_id": ObjectId(purchase_id), "user_id": user_id})
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found.")
    return purchase_helper(purchase)

