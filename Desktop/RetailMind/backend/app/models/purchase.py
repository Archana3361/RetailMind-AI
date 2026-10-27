from datetime import datetime, timezone


def purchase_helper(p) -> dict:
    total = p.get("total", 0.0)
    payment_status = p.get("payment_status", "paid")
    amount_paid = p.get("amount_paid")
    if amount_paid is None:
        amount_paid = total if payment_status == "paid" else 0.0
    balance_due = p.get("balance_due")
    if balance_due is None:
        balance_due = 0.0 if payment_status == "paid" else max(0.0, round(total - amount_paid, 2))

    return {
        "id": str(p["_id"]),
        "user_id": str(p["user_id"]),
        "purchase_number": p.get("purchase_number", ""),
        "purchase_date": p.get("purchase_date") or p.get("created_at"),
        "supplier_id": str(p["supplier_id"]) if p.get("supplier_id") else None,
        "supplier_name": p.get("supplier_name", ""),
        "supplier_invoice_number": p.get("supplier_invoice_number", ""),
        "items": p.get("items", []),
        "subtotal": p.get("subtotal", 0.0),
        "discount": p.get("discount", 0.0),
        "total": total,
        "payment_method": p.get("payment_method", "cash"),
        "payment_status": payment_status,
        "amount_paid": round(float(amount_paid), 2),
        "balance_due": round(float(balance_due), 2),
        "notes": p.get("notes", ""),
        "created_at": p.get("created_at"),
    }

