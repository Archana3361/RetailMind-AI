from datetime import datetime, timezone


def sale_helper(s) -> dict:
    total = s.get("total", 0.0)
    payment_status = s.get("payment_status", "paid")
    amount_paid = s.get("amount_paid")
    if amount_paid is None:
        amount_paid = total if payment_status == "paid" else 0.0
    balance_due = s.get("balance_due")
    if balance_due is None:
        balance_due = 0.0 if payment_status == "paid" else max(0.0, round(total - amount_paid, 2))

    return {
        "id": str(s["_id"]),
        "user_id": str(s["user_id"]),
        "sale_number": s.get("sale_number", ""),
        "sale_date": s.get("sale_date") or s.get("created_at"),
        "customer_id": str(s["customer_id"]) if s.get("customer_id") else None,
        "customer_name": s.get("customer_name", "Walk-in Customer"),
        "items": s.get("items", []),
        "subtotal": s.get("subtotal", 0.0),
        "discount": s.get("discount", 0.0),
        "discount_type": s.get("discount_type", "amount"),
        "tax": s.get("tax", 0.0),
        "total": total,
        "cost_total": s.get("cost_total", 0.0),
        "gross_profit": s.get("gross_profit", 0.0),
        "payment_method": s.get("payment_method", "cash"),
        "payment_status": payment_status,
        "amount_paid": round(float(amount_paid), 2),
        "balance_due": round(float(balance_due), 2),
        "notes": s.get("notes", ""),
        "created_at": s.get("created_at"),
    }


def sale_item_helper(item: dict) -> dict:
    return {
        "product_id": str(item["product_id"]) if item.get("product_id") else None,
        "product_name": item.get("product_name", ""),
        "sku": item.get("sku", ""),
        "quantity": item.get("quantity", 0),
        "unit_price": item.get("unit_price", 0.0),
        "cost_price": item.get("cost_price", 0.0),
        "subtotal": item.get("subtotal", 0.0),
    }
