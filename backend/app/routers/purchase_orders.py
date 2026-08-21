from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.purchase_order import PurchaseOrder
from backend.app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderResponse
from backend.app.services.po_service import POService

router = APIRouter(prefix="/purchase-orders", tags=["Purchase Orders"])


@router.get("", response_model=List[PurchaseOrderResponse])
def list_purchase_orders(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(PurchaseOrder)
    if status:
        query = query.filter(PurchaseOrder.status == status.upper())
    return query.order_by(PurchaseOrder.id.desc()).all()


@router.post("", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    po_in: PurchaseOrderCreate,
    db: Session = Depends(get_db),
):
    return POService.create_direct_po(db=db, po_in=po_in)


@router.get("/{id}", response_model=PurchaseOrderResponse)
def get_purchase_order(id: int, db: Session = Depends(get_db)):
    return POService.get_po(db=db, po_id=id)
