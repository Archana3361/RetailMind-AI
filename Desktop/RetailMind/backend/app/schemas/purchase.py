from pydantic import BaseModel, Field
from typing import Optional, List


class PurchaseItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)
    unit_cost: float = Field(..., ge=0)


class PurchaseCreate(BaseModel):
    purchase_number: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_invoice_number: Optional[str] = ""
    purchase_date: Optional[str] = None
    items: List[PurchaseItemCreate] = Field(..., min_length=1)
    discount: float = Field(default=0.0, ge=0)
    payment_method: str = Field(default="cash")
    payment_status: Optional[str] = Field(default="paid")
    amount_paid: Optional[float] = Field(default=None, ge=0)
    balance_due: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = ""

