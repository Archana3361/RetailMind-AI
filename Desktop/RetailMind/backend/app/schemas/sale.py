from pydantic import BaseModel, Field
from typing import Optional, List


class SaleItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)


class SaleCreate(BaseModel):
    sale_number: Optional[str] = None
    sale_date: Optional[str] = None
    customer_id: Optional[str] = None
    items: List[SaleItemCreate] = Field(..., min_length=1)
    discount: float = Field(default=0.0, ge=0)
    discount_type: str = Field(default="amount")  # amount | percent
    tax: float = Field(default=0.0, ge=0)
    payment_method: str = Field(default="cash")
    payment_status: Optional[str] = Field(default="paid")
    amount_paid: Optional[float] = Field(default=None, ge=0)
    balance_due: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = ""

