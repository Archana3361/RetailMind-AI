from datetime import datetime, timezone


def supplier_helper(s) -> dict:
    return {
        "id": str(s["_id"]),
        "user_id": str(s["user_id"]),
        "name": s["name"],
        "phone": s.get("phone", ""),
        "email": s.get("email", ""),
        "address": s.get("address", ""),
        "contact_person": s.get("contact_person", ""),
        "total_purchase_value": s.get("total_purchase_value", 0.0),
        "total_orders": s.get("total_orders", 0),
        "last_purchase_date": s.get("last_purchase_date"),
        "created_at": s.get("created_at"),
        "updated_at": s.get("updated_at"),
    }


def new_supplier_document(user_id: str, data: dict) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "name": data["name"],
        "phone": data.get("phone", ""),
        "email": data.get("email", ""),
        "address": data.get("address", ""),
        "contact_person": data.get("contact_person", ""),
        "total_purchase_value": 0.0,
        "total_orders": 0,
        "last_purchase_date": None,
        "created_at": now,
        "updated_at": now,
    }
