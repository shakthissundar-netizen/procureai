from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class VendorBase(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    company: str
    category: str = "General"
    rating: float = 4.0


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[float] = None


class VendorResponse(VendorBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
