import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.rfq import RFQ, RFQItem
from backend.app.models.quotation import Quotation
from backend.app.models.anomaly import Anomaly
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.schemas.rfq import (
    RFQCreate,
    RFQResponse,
    RFQDetailResponse,
    RFQUpdate,
)
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/rfqs", tags=["RFQs"])


@router.get("", response_model=List[RFQResponse])
def list_rfqs(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(RFQ)
    if status:
        query = query.filter(RFQ.status == status.upper())
    return query.order_by(RFQ.id.desc()).all()


@router.post("", response_model=RFQResponse, status_code=status.HTTP_201_CREATED)
def create_rfq(rfq_in: RFQCreate, db: Session = Depends(get_db)):
    rfq_number = rfq_in.rfq_number or f"RFQ-{str(uuid.uuid4())[:8].upper()}"

    # Verify uniqueness of rfq_number
    existing = db.query(RFQ).filter(RFQ.rfq_number == rfq_number).first()
    if existing:
        rfq_number = f"RFQ-{str(uuid.uuid4())[:8].upper()}"

    rfq = RFQ(
        rfq_number=rfq_number,
        title=rfq_in.title,
        description=rfq_in.description,
        quantity=rfq_in.quantity,
        status="OPEN",
        target_unit_price=rfq_in.target_unit_price,
        max_delivery_days=rfq_in.max_delivery_days,
        min_warranty_years=rfq_in.min_warranty_years,
        created_by=rfq_in.created_by,
    )
    db.add(rfq)
    db.flush()

    if rfq_in.items:
        for item_in in rfq_in.items:
            item = RFQItem(
                rfq_id=rfq.id,
                product_name=item_in.product_name,
                description=item_in.description,
                quantity=item_in.quantity,
                requirements_json=item_in.requirements_json,
            )
            db.add(item)
    else:
        # Default single item
        item = RFQItem(
            rfq_id=rfq.id,
            product_name=rfq_in.title,
            description=rfq_in.description,
            quantity=rfq_in.quantity,
            requirements_json=None,
        )
        db.add(item)

    db.commit()
    db.refresh(rfq)

    AuditService.log_action(
        db=db,
        entity_name="RFQ",
        entity_id=rfq.id,
        action="CREATED",
        details={"rfq_number": rfq.rfq_number, "title": rfq.title, "target_unit_price": rfq.target_unit_price},
    )

    return rfq


@router.get("/{id}", response_model=RFQDetailResponse)
def get_rfq(id: int, db: Session = Depends(get_db)):
    rfq = db.query(RFQ).filter(RFQ.id == id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail=f"RFQ with ID {id} not found")

    quotations_count = db.query(Quotation).filter(Quotation.rfq_id == id).count()
    anomalies_count = db.query(Anomaly).filter(Anomaly.rfq_id == id).count()
    has_analysis = db.query(AIAnalysis).filter(AIAnalysis.rfq_id == id).count() > 0

    return RFQDetailResponse(
        id=rfq.id,
        rfq_number=rfq.rfq_number,
        title=rfq.title,
        description=rfq.description,
        quantity=rfq.quantity,
        status=rfq.status,
        target_unit_price=rfq.target_unit_price,
        max_delivery_days=rfq.max_delivery_days,
        min_warranty_years=rfq.min_warranty_years,
        created_by=rfq.created_by,
        created_at=rfq.created_at,
        items=rfq.items,
        quotation_count=quotations_count,
        anomalies_count=anomalies_count,
        has_analysis=has_analysis,
    )
