from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from backend.app.schemas.vendor import VendorResponse


class QuotationItemBase(BaseModel):
    product_name: str
    description: Optional[str] = None
    quantity: int = 1
    unit_price: float
    total_price: float


class QuotationItemCreate(QuotationItemBase):
    pass


class QuotationItemResponse(QuotationItemBase):
    id: int
    quotation_id: int

    model_config = ConfigDict(from_attributes=True)


class QuotationBase(BaseModel):
    rfq_id: int
    vendor_id: int
    quotation_number: str
    file_name: Optional[str] = None
    delivery_days: int
    warranty_years: int = 1
    payment_terms: str
    tax_amount: float = 0.0
    additional_charges: float = 0.0
    grand_total: float
    extraction_confidence: float = 1.0
    status: str = "PENDING"


class QuotationCreate(QuotationBase):
    items: Optional[List[QuotationItemCreate]] = None


class QuotationResponse(QuotationBase):
    id: int
    created_at: datetime
    vendor: Optional[VendorResponse] = None
    items: List[QuotationItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
