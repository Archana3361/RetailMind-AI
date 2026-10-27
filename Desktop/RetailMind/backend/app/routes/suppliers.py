from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from app.core.database import get_database
from app.schemas.supplier import SupplierCreate, SupplierUpdate
from app.models.supplier import supplier_helper, new_supplier_document
from app.dependencies.auth import get_current_user_id
from datetime import datetime, timezone

router = APIRouter(prefix="/api/suppliers", tags=["Suppliers"])


@router.get("/")
async def list_suppliers(
    search: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    query = {"user_id": user_id}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]
    total = await db.suppliers.count_documents(query)
    skip = (page - 1) * per_page
    suppliers = await db.suppliers.find(query).sort("name", 1).skip(skip).limit(per_page).to_list(None)
    return {
        "items": [supplier_helper(s) for s in suppliers],
        "total": total, "page": page, "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.post("/", status_code=201)
async def create_supplier(
    data: SupplierCreate,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    doc = new_supplier_document(user_id, data.model_dump())
    result = await db.suppliers.insert_one(doc)
    created = await db.suppliers.find_one({"_id": result.inserted_id})
    return supplier_helper(created)


@router.get("/{supplier_id}")
async def get_supplier(
    supplier_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    supplier = await db.suppliers.find_one({"_id": ObjectId(supplier_id), "user_id": user_id})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found.")

    purchases = await db.purchases.find(
        {"user_id": user_id, "supplier_id": supplier_id}
    ).sort("created_at", -1).limit(10).to_list(None)

    from app.models.purchase import purchase_helper
    return {
        **supplier_helper(supplier),
        "recent_purchases": [purchase_helper(p) for p in purchases]
    }


@router.put("/{supplier_id}")
async def update_supplier(
    supplier_id: str,
    data: SupplierUpdate,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    supplier = await db.suppliers.find_one({"_id": ObjectId(supplier_id), "user_id": user_id})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    update = {k: v for k, v in data.model_dump().items() if v is not None}
    update["updated_at"] = datetime.now(timezone.utc)
    await db.suppliers.update_one({"_id": ObjectId(supplier_id)}, {"$set": update})
    updated = await db.suppliers.find_one({"_id": ObjectId(supplier_id)})
    return supplier_helper(updated)


@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    supplier = await db.suppliers.find_one({"_id": ObjectId(supplier_id), "user_id": user_id})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    await db.suppliers.delete_one({"_id": ObjectId(supplier_id)})
    return {"message": "Supplier deleted."}
