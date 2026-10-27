from datetime import datetime, timezone
from bson import ObjectId


async def adjust_stock(db, user_id: str, product_id: str, quantity_change: int,
                       transaction_type: str, reference_id: str = None,
                       reference_type: str = None, notes: str = ""):
    """
    Adjust product stock and create an inventory transaction record.
    quantity_change: positive = increase, negative = decrease
    transaction_type: 'sale' | 'purchase' | 'adjustment' | 'return'
    """
    product = await db.products.find_one({
        "_id": ObjectId(product_id),
        "user_id": user_id
    })
    if not product:
        return None

    new_stock = product.get("current_stock", 0) + quantity_change
    if new_stock < 0:
        new_stock = 0

    await db.products.update_one(
        {"_id": ObjectId(product_id)},
        {
            "$set": {
                "current_stock": new_stock,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    transaction = {
        "user_id": user_id,
        "product_id": product_id,
        "product_name": product.get("name", ""),
        "sku": product.get("sku", ""),
        "transaction_type": transaction_type,
        "quantity_change": quantity_change,
        "stock_before": product.get("current_stock", 0),
        "stock_after": new_stock,
        "reference_id": reference_id,
        "reference_type": reference_type,
        "notes": notes,
        "created_at": datetime.now(timezone.utc),
    }
    await db.inventory_transactions.insert_one(transaction)
    return new_stock


async def get_inventory_summary(db, user_id: str) -> dict:
    pipeline = [
        {"$match": {"user_id": user_id, "status": "active"}},
        {"$group": {
            "_id": None,
            "total_products": {"$sum": 1},
            "total_stock_value": {
                "$sum": {"$multiply": ["$current_stock", "$cost_price"]}
            },
            "out_of_stock_count": {
                "$sum": {"$cond": [{"$lte": ["$current_stock", 0]}, 1, 0]}
            },
            "low_stock_count": {
                "$sum": {
                    "$cond": [
                        {"$and": [
                            {"$gt": ["$current_stock", 0]},
                            {"$lte": ["$current_stock", "$minimum_stock"]}
                        ]}, 1, 0
                    ]
                }
            }
        }}
    ]
    result = await db.products.aggregate(pipeline).to_list(1)
    if result:
        r = result[0]
        r.pop("_id", None)
        return r
    return {
        "total_products": 0,
        "total_stock_value": 0.0,
        "out_of_stock_count": 0,
        "low_stock_count": 0,
    }
