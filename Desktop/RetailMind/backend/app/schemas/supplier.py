from pydantic import BaseModel, Field
from typing import Optional


class SupplierCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    phone: Optional[str] = ""
    email: Optional[str] = ""
    address: Optional[str] = ""
    contact_person: Optional[str] = ""


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
