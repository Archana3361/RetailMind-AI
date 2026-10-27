from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from app.core.database import get_database
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.models.customer import customer_helper, new_customer_document
from app.dependencies.auth import get_current_user_id
from datetime import datetime, timezone

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.get("/")
async def list_customers(
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
    total = await db.customers.count_documents(query)
    skip = (page - 1) * per_page
    customers = await db.customers.find(query).sort("name", 1).skip(skip).limit(per_page).to_list(None)
    return {
        "items": [customer_helper(c) for c in customers],
        "total": total, "page": page, "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.post("/", status_code=201)
async def create_customer(
    data: CustomerCreate,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    doc = new_customer_document(user_id, data.model_dump())
    result = await db.customers.insert_one(doc)
    created = await db.customers.find_one({"_id": result.inserted_id})
    return customer_helper(created)


@router.get("/{customer_id}")
async def get_customer(
    customer_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    customer = await db.customers.find_one({"_id": ObjectId(customer_id), "user_id": user_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")
    
    # Get purchase history
    sales = await db.sales.find(
        {"user_id": user_id, "customer_id": customer_id}
    ).sort("created_at", -1).limit(10).to_list(None)
    
    from app.models.sale import sale_helper
    return {
        **customer_helper(customer),
        "recent_sales": [sale_helper(s) for s in sales]
    }


@router.put("/{customer_id}")
async def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    customer = await db.customers.find_one({"_id": ObjectId(customer_id), "user_id": user_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")
    update = {k: v for k, v in data.model_dump().items() if v is not None}
    update["updated_at"] = datetime.now(timezone.utc)
    await db.customers.update_one({"_id": ObjectId(customer_id)}, {"$set": update})
    updated = await db.customers.find_one({"_id": ObjectId(customer_id)})
    return customer_helper(updated)


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: str,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_database)
):
    customer = await db.customers.find_one({"_id": ObjectId(customer_id), "user_id": user_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found.")
    await db.customers.delete_one({"_id": ObjectId(customer_id)})
    return {"message": "Customer deleted."}
