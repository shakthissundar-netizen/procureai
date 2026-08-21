from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.vendor import Vendor
from backend.app.schemas.vendor import VendorCreate, VendorResponse, VendorUpdate
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/vendors", tags=["Vendors"])


@router.get("", response_model=List[VendorResponse])
def get_vendors(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Vendor)
    if category:
        query = query.filter(Vendor.category.ilike(f"%{category}%"))
    if search:
        query = query.filter(
            (Vendor.name.ilike(f"%{search}%"))
            | (Vendor.company.ilike(f"%{search}%"))
            | (Vendor.email.ilike(f"%{search}%"))
        )
    return query.order_by(Vendor.id.asc()).all()


@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def create_vendor(vendor_in: VendorCreate, db: Session = Depends(get_db)):
    vendor = Vendor(
        name=vendor_in.name,
        email=vendor_in.email,
        phone=vendor_in.phone,
        company=vendor_in.company,
        category=vendor_in.category,
        rating=vendor_in.rating,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    AuditService.log_action(
        db=db,
        entity_name="Vendor",
        entity_id=vendor.id,
        action="CREATED",
        details={"name": vendor.name, "company": vendor.company},
    )

    return vendor


@router.get("/{id}", response_model=VendorResponse)
def get_vendor(id: int, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.id == id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail=f"Vendor with ID {id} not found")
    return vendor
