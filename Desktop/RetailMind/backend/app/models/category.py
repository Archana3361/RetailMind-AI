from datetime import datetime, timezone


def category_helper(cat) -> dict:
    return {
        "id": str(cat["_id"]),
        "name": cat["name"],
        "description": cat.get("description", ""),
        "created_at": cat.get("created_at"),
    }


def new_category_document(user_id: str, name: str, description: str = "") -> dict:
    return {
        "user_id": user_id,
        "name": name.strip(),
        "description": description,
        "created_at": datetime.now(timezone.utc),
    }
