from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from app.core.database import get_database
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.models.category import category_helper, new_category_document
from app.dependencies.auth import get_current_user_id

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("/")
async def list_categories(
    page: int = 1,
    per_page: int = 100,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    """
    Get user's categories (owned by user, consistent with other endpoints).
    Returns paginated response for consistency with other endpoints.
    """
    # Filter categories by user_id for consistency with create/update/delete operations
    query = {"user_id": user_id}
    total = await db.categories.count_documents(query)
    skip = (page - 1) * per_page
    cats = await db.categories.find(query).sort("name", 1).skip(skip).limit(per_page).to_list(None)
    
    return {
        "items": [category_helper(c) for c in cats],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.post("/", status_code=201)
async def create_category(
    data: CategoryCreate,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    existing = await db.categories.find_one({"user_id": user_id, "name": data.name.strip()})
    if existing:
        raise HTTPException(status_code=409, detail="Category already exists.")
    doc = new_category_document(user_id, data.name, data.description or "")
    result = await db.categories.insert_one(doc)
    created = await db.categories.find_one({"_id": result.inserted_id})
    return category_helper(created)


@router.put("/{category_id}")
async def update_category(
    category_id: str,
    data: CategoryUpdate,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    cat = await db.categories.find_one({"_id": ObjectId(category_id), "user_id": user_id})
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    update = {k: v for k, v in data.model_dump().items() if v is not None}
    await db.categories.update_one({"_id": ObjectId(category_id)}, {"$set": update})
    updated = await db.categories.find_one({"_id": ObjectId(category_id)})
    return category_helper(updated)


@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    cat = await db.categories.find_one({"_id": ObjectId(category_id), "user_id": user_id})
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found.")
    await db.categories.delete_one({"_id": ObjectId(category_id)})
    return {"message": "Category deleted."}
