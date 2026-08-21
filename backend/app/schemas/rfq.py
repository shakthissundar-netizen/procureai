from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class RFQItemBase(BaseModel):
    product_name: str
    description: Optional[str] = None
    quantity: int = 1
    requirements_json: Optional[str] = None


class RFQItemCreate(RFQItemBase):
    pass


class RFQItemResponse(RFQItemBase):
    id: int
    rfq_id: int

    model_config = ConfigDict(from_attributes=True)


class RFQBase(BaseModel):
    title: str
    description: Optional[str] = None
    quantity: int = 1
    target_unit_price: float
    max_delivery_days: int
    min_warranty_years: int = 1
    created_by: str = "Procurement Manager"


class RFQCreate(RFQBase):
    rfq_number: Optional[str] = None
    items: Optional[List[RFQItemCreate]] = None


class RFQUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    status: Optional[str] = None
    target_unit_price: Optional[float] = None
    max_delivery_days: Optional[int] = None
    min_warranty_years: Optional[int] = None


class RFQResponse(RFQBase):
    id: int
    rfq_number: str
    status: str
    created_at: datetime
    items: List[RFQItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class RFQDetailResponse(RFQResponse):
    quotation_count: int = 0
    anomalies_count: int = 0
    has_analysis: bool = False
