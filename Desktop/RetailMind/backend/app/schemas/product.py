from pydantic import BaseModel, Field
from typing import Optional


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    sku: str = Field(..., min_length=1, max_length=50)
    category_id: Optional[str] = None
    brand: Optional[str] = ""
    unit: Optional[str] = "pcs"
    cost_price: float = Field(default=0.0, ge=0)
    selling_price: float = Field(default=0.0, ge=0)
    current_stock: int = Field(default=0, ge=0)
    minimum_stock: int = Field(default=0, ge=0)
    supplier_id: Optional[str] = None
    description: Optional[str] = ""


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    category_id: Optional[str] = None
    brand: Optional[str] = None
    unit: Optional[str] = None
    cost_price: Optional[float] = Field(None, ge=0)
    selling_price: Optional[float] = Field(None, ge=0)
    current_stock: Optional[int] = Field(None, ge=0)
    minimum_stock: Optional[int] = Field(None, ge=0)
    supplier_id: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
