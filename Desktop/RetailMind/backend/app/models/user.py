from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId


def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "full_name": user["full_name"],
        "email": user["email"],
        "mobile": user["mobile"],
        "shop_name": user["shop_name"],
        "is_verified": user.get("is_verified", False),
        "is_active": user.get("is_active", True),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }


def new_user_document(
    full_name: str,
    email: str,
    mobile: str,
    shop_name: str,
    hashed_password: str,
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "full_name": full_name,
        "email": email.lower().strip(),
        "mobile": mobile,
        "shop_name": shop_name,
        "hashed_password": hashed_password,
        "is_verified": False,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
