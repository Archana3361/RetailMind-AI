from datetime import datetime, timezone


def customer_helper(c) -> dict:
    return {
        "id": str(c["_id"]),
        "user_id": str(c["user_id"]),
        "name": c["name"],
        "phone": c.get("phone", ""),
        "email": c.get("email", ""),
        "address": c.get("address", ""),
        "total_purchases": c.get("total_purchases", 0.0),
        "total_orders": c.get("total_orders", 0),
        "last_purchase_date": c.get("last_purchase_date"),
        "created_at": c.get("created_at"),
        "updated_at": c.get("updated_at"),
    }


def new_customer_document(user_id: str, data: dict) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "name": data["name"],
        "phone": data.get("phone", ""),
        "email": data.get("email", ""),
        "address": data.get("address", ""),
        "total_purchases": 0.0,
        "total_orders": 0,
        "last_purchase_date": None,
        "created_at": now,
        "updated_at": now,
    }
