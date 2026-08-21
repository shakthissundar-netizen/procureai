import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from fastapi import HTTPException

from backend.app.models.rfq import RFQ
from backend.app.models.vendor import Vendor
from backend.app.models.quotation import Quotation
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from backend.app.schemas.analysis import ApproveRFQRequest
from backend.app.schemas.purchase_order import PurchaseOrderCreate
from backend.app.services.audit_service import AuditService


class POService:

    @staticmethod
    def generate_po_number(rfq_id: int) -> str:
        unique_suffix = str(uuid.uuid4())[:6].upper()
        return f"PO-RFQ{rfq_id}-{unique_suffix}"

    @classmethod
    def approve_rfq_and_create_po(
        cls,
        db: Session,
        rfq_id: int,
        approval_in: Optional[ApproveRFQRequest] = None,
    ) -> PurchaseOrder:
        rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
        if not rfq:
            raise HTTPException(status_code=404, detail=f"RFQ with ID {rfq_id} not found")

        # Determine target vendor
        target_vendor_id = approval_in.vendor_id if approval_in and approval_in.vendor_id else None
        
        if not target_vendor_id:
            # Fallback to recommended vendor from AI Analysis
            analysis = db.query(AIAnalysis).filter(AIAnalysis.rfq_id == rfq_id).order_by(AIAnalysis.id.desc()).first()
            if analysis and analysis.recommended_vendor_id:
                target_vendor_id = analysis.recommended_vendor_id

        if not target_vendor_id:
            # Fallback to first quotation's vendor
            q = db.query(Quotation).filter(Quotation.rfq_id == rfq_id).first()
            if q:
                target_vendor_id = q.vendor_id

        if not target_vendor_id:
            raise HTTPException(
                status_code=400,
                detail="No vendor available to approve for this RFQ. Upload quotations first.",
            )

        vendor = db.query(Vendor).filter(Vendor.id == target_vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=404, detail=f"Vendor with ID {target_vendor_id} not found")

        quotation = (
            db.query(Quotation)
            .filter(Quotation.rfq_id == rfq_id, Quotation.vendor_id == target_vendor_id)
            .first()
        )

        po_number = cls.generate_po_number(rfq_id)
        
        # Calculate financials
        if quotation:
            subtotal = quotation.grand_total - quotation.tax_amount
            tax = quotation.tax_amount
            total = quotation.grand_total
            delivery_terms = f"{quotation.delivery_days} days from PO issuance"
            payment_terms = quotation.payment_terms
        else:
            subtotal = rfq.quantity * rfq.target_unit_price
            tax = round(subtotal * 0.18, 2)
            total = subtotal + tax
            delivery_terms = f"{rfq.max_delivery_days} days"
            payment_terms = "Net 30"

        if approval_in and approval_in.delivery_terms:
            delivery_terms = approval_in.delivery_terms
        if approval_in and approval_in.payment_terms:
            payment_terms = approval_in.payment_terms

        po = PurchaseOrder(
            po_number=po_number,
            rfq_id=rfq.id,
            vendor_id=target_vendor_id,
            status="APPROVED",
            subtotal=round(subtotal, 2),
            tax=round(tax, 2),
            total=round(total, 2),
            delivery_terms=delivery_terms,
            payment_terms=payment_terms,
            approved_at=datetime.now(),
        )
        db.add(po)
        db.flush()

        # Copy line items
        if quotation and quotation.items:
            for q_item in quotation.items:
                po_item = PurchaseOrderItem(
                    purchase_order_id=po.id,
                    product_name=q_item.product_name,
                    quantity=q_item.quantity,
                    unit_price=q_item.unit_price,
                    total_price=q_item.total_price,
                )
                db.add(po_item)
        elif rfq.items:
            unit_price = round(subtotal / rfq.quantity, 2) if rfq.quantity > 0 else rfq.target_unit_price
            for r_item in rfq.items:
                po_item = PurchaseOrderItem(
                    purchase_order_id=po.id,
                    product_name=r_item.product_name,
                    quantity=r_item.quantity,
                    unit_price=unit_price,
                    total_price=round(r_item.quantity * unit_price, 2),
                )
                db.add(po_item)
        else:
            po_item = PurchaseOrderItem(
                purchase_order_id=po.id,
                product_name=rfq.title,
                quantity=rfq.quantity,
                unit_price=round(subtotal / rfq.quantity, 2) if rfq.quantity > 0 else rfq.target_unit_price,
                total_price=subtotal,
            )
            db.add(po_item)

        # Update RFQ status
        rfq.status = "APPROVED"
        db.commit()
        db.refresh(po)

        AuditService.log_action(
            db=db,
            entity_name="RFQ",
            entity_id=rfq.id,
            action="APPROVED_AND_PO_CREATED",
            details={"po_id": po.id, "po_number": po.po_number, "vendor_id": target_vendor_id, "total": po.total},
        )

        return po

    @classmethod
    def create_direct_po(cls, db: Session, po_in: PurchaseOrderCreate) -> PurchaseOrder:
        po_number = po_in.po_number or f"PO-DIR-{str(uuid.uuid4())[:6].upper()}"
        po = PurchaseOrder(
            po_number=po_number,
            rfq_id=po_in.rfq_id,
            vendor_id=po_in.vendor_id,
            status=po_in.status,
            subtotal=po_in.subtotal,
            tax=po_in.tax,
            total=po_in.total,
            delivery_terms=po_in.delivery_terms,
            payment_terms=po_in.payment_terms,
        )
        db.add(po)
        db.flush()

        if po_in.items:
            for item in po_in.items:
                po_item = PurchaseOrderItem(
                    purchase_order_id=po.id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                )
                db.add(po_item)

        db.commit()
        db.refresh(po)

        AuditService.log_action(
            db=db,
            entity_name="PurchaseOrder",
            entity_id=po.id,
            action="CREATED",
            details={"po_number": po.po_number, "vendor_id": po.vendor_id, "total": po.total},
        )
        return po

    @staticmethod
    def get_po(db: Session, po_id: int) -> PurchaseOrder:
        po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
        if not po:
            raise HTTPException(status_code=404, detail=f"Purchase Order with ID {po_id} not found")
        return po
