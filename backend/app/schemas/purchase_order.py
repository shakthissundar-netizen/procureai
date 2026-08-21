from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from backend.app.schemas.vendor import VendorResponse


class PurchaseOrderItemBase(BaseModel):
    product_name: str
    quantity: int = 1
    unit_price: float
    total_price: float


class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass


class PurchaseOrderItemResponse(PurchaseOrderItemBase):
    id: int
    purchase_order_id: int

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderBase(BaseModel):
    rfq_id: int
    vendor_id: int
    status: str = "DRAFT"
    subtotal: float
    tax: float = 0.0
    total: float
    delivery_terms: Optional[str] = None
    payment_terms: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    po_number: Optional[str] = None
    items: Optional[List[PurchaseOrderItemCreate]] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    id: int
    po_number: str
    created_at: datetime
    approved_at: Optional[datetime] = None
    vendor: Optional[VendorResponse] = None
    items: List[PurchaseOrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
