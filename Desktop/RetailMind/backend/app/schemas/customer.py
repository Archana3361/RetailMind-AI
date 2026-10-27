from pydantic import BaseModel, Field
from typing import Optional


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    phone: Optional[str] = ""
    email: Optional[str] = ""
    address: Optional[str] = ""


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
