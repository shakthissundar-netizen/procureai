from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.rfq import RFQ
from backend.app.models.vendor import Vendor
from backend.app.models.quotation import Quotation, QuotationItem
from backend.app.schemas.quotation import (
    QuotationCreate,
    QuotationResponse,
)
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/rfqs", tags=["Quotations"])


@router.post("/{id}/quotations", response_model=QuotationResponse, status_code=status.HTTP_201_CREATED)
def create_quotation_for_rfq(
    id: int,
    quotation_in: QuotationCreate,
    db: Session = Depends(get_db),
):
    rfq = db.query(RFQ).filter(RFQ.id == id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail=f"RFQ with ID {id} not found")

    vendor = db.query(Vendor).filter(Vendor.id == quotation_in.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor with ID {quotation_in.vendor_id} not found")

    # Create quotation
    quotation = Quotation(
        rfq_id=rfq.id,
        vendor_id=vendor.id,
        quotation_number=quotation_in.quotation_number,
        file_name=quotation_in.file_name,
        delivery_days=quotation_in.delivery_days,
        warranty_years=quotation_in.warranty_years,
        payment_terms=quotation_in.payment_terms,
        tax_amount=quotation_in.tax_amount,
        additional_charges=quotation_in.additional_charges,
        grand_total=quotation_in.grand_total,
        extraction_confidence=quotation_in.extraction_confidence,
        status="EXTRACTED",
    )
    db.add(quotation)
    db.flush()

    # Add items if provided
    if quotation_in.items:
        for item_in in quotation_in.items:
            item = QuotationItem(
                quotation_id=quotation.id,
                product_name=item_in.product_name,
                description=item_in.description,
                quantity=item_in.quantity,
                unit_price=item_in.unit_price,
                total_price=item_in.total_price,
            )
            db.add(item)
    else:
        # Default single item
        unit_price = round(quotation.grand_total / rfq.quantity, 2) if rfq.quantity > 0 else quotation.grand_total
        item = QuotationItem(
            quotation_id=quotation.id,
            product_name=rfq.title,
            description=None,
            quantity=rfq.quantity,
            unit_price=unit_price,
            total_price=quotation.grand_total,
        )
        db.add(item)

    db.commit()
    db.refresh(quotation)

    AuditService.log_action(
        db=db,
        entity_name="Quotation",
        entity_id=quotation.id,
        action="UPLOADED",
        details={
            "rfq_id": rfq.id,
            "vendor_id": vendor.id,
            "quotation_number": quotation.quotation_number,
            "grand_total": quotation.grand_total,
        },
    )

    return quotation


@router.get("/{id}/quotations", response_model=List[QuotationResponse])
def get_quotations_for_rfq(id: int, db: Session = Depends(get_db)):
    rfq = db.query(RFQ).filter(RFQ.id == id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail=f"RFQ with ID {id} not found")

    return db.query(Quotation).filter(Quotation.rfq_id == id).order_by(Quotation.id.asc()).all()
