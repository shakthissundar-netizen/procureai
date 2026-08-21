# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from backend.app.database import get_db
from backend.app.models.rfq import RFQ
from backend.app.models.vendor import Vendor
from backend.app.models.quotation import Quotation
from backend.app.models.anomaly import Anomaly
from backend.app.models.purchase_order import PurchaseOrder
from backend.app.schemas.dashboard import DashboardStatsResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_rfqs = db.query(RFQ).count()
    active_rfqs = db.query(RFQ).filter(RFQ.status.in_(["OPEN", "ANALYZED"])).count()
    completed_rfqs = db.query(RFQ).filter(RFQ.status == "APPROVED").count()

    total_vendors = db.query(Vendor).count()
    total_quotations = db.query(Quotation).count()
    total_purchase_orders = db.query(PurchaseOrder).count()

    # Total spend calculation
    spend_result = db.query(func.sum(PurchaseOrder.total)).scalar()
    total_spend = float(spend_result) if spend_result else 0.0

    total_anomalies = db.query(Anomaly).count()
    critical_anomalies = db.query(Anomaly).filter(Anomaly.severity == "CRITICAL").count()

    # Recent activities
    recent_rfqs = (
        db.query(RFQ)
        .order_by(RFQ.id.desc())
        .limit(5)
        .all()
    )
    recent_rfqs_data = [
        {
            "id": r.id,
            "rfq_number": r.rfq_number,
            "title": r.title,
            "quantity": r.quantity,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in recent_rfqs
    ]

    recent_anomalies = (
        db.query(Anomaly)
        .order_by(Anomaly.id.desc())
        .limit(5)
        .all()
    )
    recent_anomalies_data = [
        {
            "id": a.id,
            "rfq_id": a.rfq_id,
            "vendor_id": a.vendor_id,
            "type": a.type,
            "severity": a.severity,
            "message": a.message,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in recent_anomalies
    ]

    recent_pos = (
        db.query(PurchaseOrder)
        .order_by(PurchaseOrder.id.desc())
        .limit(5)
        .all()
    )
    recent_pos_data = [
        {
            "id": p.id,
            "po_number": p.po_number,
            "rfq_id": p.rfq_id,
            "vendor_id": p.vendor_id,
            "status": p.status,
            "total": p.total,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in recent_pos
    ]

    return DashboardStatsResponse(
        total_rfqs=total_rfqs,
        active_rfqs=active_rfqs,
        completed_rfqs=completed_rfqs,
        total_vendors=total_vendors,
        total_quotations=total_quotations,
        total_purchase_orders=total_purchase_orders,
        total_spend=round(total_spend, 2),
        total_anomalies_detected=total_anomalies,
        critical_anomalies=critical_anomalies,
        recent_rfqs=recent_rfqs_data,
        recent_anomalies=recent_anomalies_data,
        recent_purchase_orders=recent_pos_data,
    )
