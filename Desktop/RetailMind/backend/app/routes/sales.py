from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from datetime import datetime, timezone
from app.core.database import get_database
from app.schemas.sale import SaleCreate
from app.models.sale import sale_helper
from app.dependencies.auth import get_current_user_id
from app.services.inventory_service import adjust_stock

router = APIRouter(prefix="/api/sales", tags=["Sales"])


async def _generate_sale_number(db, user_id: str) -> str:
    count = await db.sales.count_documents({"user_id": user_id})
    return f"SL-{str(count + 1).zfill(5)}"


@router.get("/")
async def list_sales(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    query = {"user_id": user_id}
    total = await db.sales.count_documents(query)
    skip = (page - 1) * per_page
    sales = await db.sales.find(query).sort("created_at", -1).skip(skip).limit(per_page).to_list(None)
    return {
        "items": [sale_helper(s) for s in sales],
        "total": total, "page": page, "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.post("/", status_code=201)
async def create_sale(
    data: SaleCreate,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    items = []
    subtotal = 0.0
    cost_total = 0.0

    for item in data.items:
        product = await db.products.find_one({
            "_id": ObjectId(item.product_id), "user_id": user_id, "status": "active"
        })
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found.")
        if product.get("current_stock", 0) < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{product['name']}'. Available: {product.get('current_stock', 0)}"
            )
        line_total = item.quantity * item.unit_price
        line_cost = item.quantity * product.get("cost_price", 0.0)
        subtotal += line_total
        cost_total += line_cost
        items.append({
            "product_id": item.product_id,
            "product_name": product["name"],
            "sku": product.get("sku", ""),
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "cost_price": product.get("cost_price", 0.0),
            "subtotal": round(line_total, 2),
        })

    # Apply discount
    discount_amount = data.discount
    if data.discount_type == "percent":
        discount_amount = round(subtotal * data.discount / 100, 2)

    total = max(0.0, subtotal - discount_amount + data.tax)
    gross_profit = total - cost_total

    # Resolve customer
    customer_name = "Walk-in Customer"
    if data.customer_id:
        customer = await db.customers.find_one({"_id": ObjectId(data.customer_id), "user_id": user_id})
        if customer:
            customer_name = customer["name"]

    # Resolve sale number
    sale_number = (data.sale_number or "").strip()
    if sale_number:
        existing = await db.sales.find_one({"user_id": user_id, "sale_number": sale_number})
        if existing:
            sale_number = await _generate_sale_number(db, user_id)
    else:
        sale_number = await _generate_sale_number(db, user_id)

    # Resolve sale date
    now = datetime.now(timezone.utc)
    sale_date = now
    if data.sale_date:
        try:
            if len(data.sale_date) == 10:
                sale_date = datetime.strptime(data.sale_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            else:
                sale_date = datetime.fromisoformat(data.sale_date.replace("Z", "+00:00"))
        except Exception:
            sale_date = now

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

    sale_doc = {
        "user_id": user_id,
        "sale_number": sale_number,
        "sale_date": sale_date,
        "customer_id": data.customer_id,
        "customer_name": customer_name,
        "items": items,
        "subtotal": round(subtotal, 2),
        "discount": round(discount_amount, 2),
        "discount_type": data.discount_type,
        "tax": data.tax,
        "total": round(total, 2),
        "cost_total": round(cost_total, 2),
        "gross_profit": round(gross_profit, 2),
        "payment_method": data.payment_method,
        "payment_status": payment_status,
        "amount_paid": amount_paid,
        "balance_due": balance_due,
        "notes": data.notes or "",
        "created_at": sale_date,
    }

    result = await db.sales.insert_one(sale_doc)
    sale_id = str(result.inserted_id)

    # Decrease inventory
    for item in items:
        await adjust_stock(
            db, user_id, item["product_id"], -item["quantity"],
            "sale", sale_id, "sale",
            f"Sale {sale_number}"
        )

    # Update customer stats
    if data.customer_id:
        await db.customers.update_one(
            {"_id": ObjectId(data.customer_id)},
            {
                "$inc": {"total_purchases": round(total, 2), "total_orders": 1},
                "$set": {"last_purchase_date": sale_date, "updated_at": now}
            }
        )

    created = await db.sales.find_one({"_id": result.inserted_id})
    return sale_helper(created)


@router.get("/next-number")
async def get_next_sale_number(
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    next_num = await _generate_sale_number(db, user_id)
    return {"sale_number": next_num}


@router.get("/{sale_id}")
async def get_sale(
    sale_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    sale = await db.sales.find_one({"_id": ObjectId(sale_id), "user_id": user_id})
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found.")
    return sale_helper(sale)

