from datetime import datetime, timezone


def product_helper(product) -> dict:
    return {
        "id": str(product["_id"]),
        "user_id": str(product["user_id"]),
        "name": product["name"],
        "sku": product["sku"],
        "category_id": str(product["category_id"]) if product.get("category_id") else None,
        "category_name": product.get("category_name", ""),
        "brand": product.get("brand", ""),
        "unit": product.get("unit", "pcs"),
        "cost_price": product.get("cost_price", 0.0),
        "selling_price": product.get("selling_price", 0.0),
        "current_stock": product.get("current_stock", 0),
        "minimum_stock": product.get("minimum_stock", 0),
        "supplier_id": str(product["supplier_id"]) if product.get("supplier_id") else None,
        "supplier_name": product.get("supplier_name", ""),
        "description": product.get("description", ""),
        "status": product.get("status", "active"),
        "stock_status": _get_stock_status(
            product.get("current_stock", 0),
            product.get("minimum_stock", 0)
        ),
        "created_at": product.get("created_at"),
        "updated_at": product.get("updated_at"),
    }


def _get_stock_status(current_stock: int, minimum_stock: int) -> str:
    if current_stock <= 0:
        return "out_of_stock"
    elif current_stock <= minimum_stock:
        return "low_stock"
    return "in_stock"


def new_product_document(user_id: str, data: dict) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "name": data["name"],
        "sku": data["sku"],
        "category_id": data.get("category_id"),
        "category_name": data.get("category_name", ""),
        "brand": data.get("brand", ""),
        "unit": data.get("unit", "pcs"),
        "cost_price": float(data.get("cost_price", 0)),
        "selling_price": float(data.get("selling_price", 0)),
        "current_stock": int(data.get("current_stock", 0)),
        "minimum_stock": int(data.get("minimum_stock", 0)),
        "supplier_id": data.get("supplier_id"),
        "supplier_name": data.get("supplier_name", ""),
        "description": data.get("description", ""),
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
