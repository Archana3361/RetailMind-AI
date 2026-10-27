from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from datetime import datetime, timezone
from app.core.database import get_database
from app.schemas.product import ProductCreate, ProductUpdate
from app.models.product import product_helper, new_product_document, _get_stock_status
from app.dependencies.auth import get_current_user_id

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("/")
async def list_products(
    search: str = Query(default=""),
    category_id: str = Query(default=""),
    stock_status: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    query = {"user_id": user_id, "status": "active"}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"brand": {"$regex": search, "$options": "i"}},
        ]
    if category_id:
        query["category_id"] = category_id
    
    # Apply stock_status filter in database query for accurate pagination
    if stock_status:
        if stock_status == "low_stock":
            query["$expr"] = {"$lte": ["$current_stock", "$minimum_stock"]}
        elif stock_status == "out_of_stock":
            query["current_stock"] = 0
        elif stock_status == "in_stock":
            query["$expr"] = {"$gt": ["$current_stock", "$minimum_stock"]}

    total = await db.products.count_documents(query)
    skip = (page - 1) * per_page
    products = await db.products.find(query).sort("name", 1).skip(skip).limit(per_page).to_list(None)

    result = [product_helper(p) for p in products]

    return {
        "items": result,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.post("/", status_code=201)
async def create_product(
    data: ProductCreate,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    existing = await db.products.find_one({"user_id": user_id, "sku": data.sku})
    if existing:
        raise HTTPException(status_code=409, detail=f"SKU '{data.sku}' already exists.")

    doc = new_product_document(user_id, data.model_dump())

    # Resolve category name
    if data.category_id:
        try:
            cat = await db.categories.find_one({"_id": ObjectId(data.category_id), "user_id": user_id})
            if cat:
                doc["category_name"] = cat["name"]
        except Exception:
            pass

    # Resolve supplier name
    if data.supplier_id:
        try:
            sup = await db.suppliers.find_one({"_id": ObjectId(data.supplier_id), "user_id": user_id})
            if sup:
                doc["supplier_name"] = sup["name"]
        except Exception:
            pass

    result = await db.products.insert_one(doc)
    created = await db.products.find_one({"_id": result.inserted_id})
    return product_helper(created)


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    product = await db.products.find_one({"_id": ObjectId(product_id), "user_id": user_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product_helper(product)


@router.put("/{product_id}")
async def update_product(
    product_id: str,
    data: ProductUpdate,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    product = await db.products.find_one({"_id": ObjectId(product_id), "user_id": user_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    update = {k: v for k, v in data.model_dump().items() if v is not None}

    # Resolve names on update
    if "category_id" in update and update["category_id"]:
        try:
            cat = await db.categories.find_one({"_id": ObjectId(update["category_id"]), "user_id": user_id})
            if cat:
                update["category_name"] = cat["name"]
        except Exception:
            pass

    if "supplier_id" in update and update["supplier_id"]:
        try:
            sup = await db.suppliers.find_one({"_id": ObjectId(update["supplier_id"]), "user_id": user_id})
            if sup:
                update["supplier_name"] = sup["name"]
        except Exception:
            pass

    update["updated_at"] = datetime.now(timezone.utc)
    await db.products.update_one({"_id": ObjectId(product_id)}, {"$set": update})
    updated = await db.products.find_one({"_id": ObjectId(product_id)})
    return product_helper(updated)


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    product = await db.products.find_one({"_id": ObjectId(product_id), "user_id": user_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    # Soft delete
    await db.products.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"status": "deleted", "updated_at": datetime.now(timezone.utc)}}
    )
    return {"message": "Product deleted."}
