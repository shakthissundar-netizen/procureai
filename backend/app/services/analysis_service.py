import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.models.rfq import RFQ
from backend.app.models.quotation import Quotation
from backend.app.models.vendor import Vendor
from backend.app.models.vendor_score import VendorScore
from backend.app.models.anomaly import Anomaly
from backend.app.models.ai_analysis import AIAnalysis
from backend.app.schemas.analysis import ScoringWeights
from backend.app.services.scoring_service import ScoringService
from backend.app.services.anomaly_service import AnomalyService
from backend.app.services.ai_service import AIService
from backend.app.services.audit_service import AuditService


class AnalysisService:

    @classmethod
    def run_rfq_analysis(
        cls,
        db: Session,
        rfq_id: int,
        weights: Optional[ScoringWeights] = None,
    ) -> Dict[str, Any]:
        rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
        if not rfq:
            raise HTTPException(status_code=404, detail=f"RFQ with ID {rfq_id} not found")

        quotations = db.query(Quotation).filter(Quotation.rfq_id == rfq_id).all()
        if not quotations:
            raise HTTPException(
                status_code=400,
                detail=f"No quotations found for RFQ {rfq_id}. Please upload vendor quotations before running analysis.",
            )

        if weights is None:
            weights = ScoringWeights()

        # 1. Clear previous analysis, scores, anomalies for fresh calculation
        db.query(Anomaly).filter(Anomaly.rfq_id == rfq_id).delete()
        db.query(VendorScore).filter(VendorScore.rfq_id == rfq_id).delete()
        db.query(AIAnalysis).filter(AIAnalysis.rfq_id == rfq_id).delete()
        db.commit()

        # 2. Anomaly Detection
        created_anomalies: List[Anomaly] = []
        quotation_anomalies_map: Dict[int, List[Anomaly]] = {}

        for q in quotations:
            detected = AnomalyService.detect_anomalies(rfq, q)
            q_anoms = []
            for d in detected:
                anom = Anomaly(
                    rfq_id=rfq.id,
                    quotation_id=q.id,
                    vendor_id=q.vendor_id,
                    type=d["type"],
                    severity=d["severity"],
                    message=d["message"],
                    expected_value=d.get("expected_value"),
                    actual_value=d.get("actual_value"),
                )
                db.add(anom)
                created_anomalies.append(anom)
                q_anoms.append(anom)
            quotation_anomalies_map[q.id] = q_anoms

        db.commit()

        # 3. Deterministic Scoring & Ranking
        score_dicts = ScoringService.evaluate_quotations(
            rfq=rfq,
            quotations=quotations,
            quotation_anomalies_map=quotation_anomalies_map,
            weights=weights,
        )

        created_scores: List[VendorScore] = []
        for s in score_dicts:
            score_obj = VendorScore(
                rfq_id=rfq.id,
                vendor_id=s["vendor_id"],
                price_score=s["price_score"],
                delivery_score=s["delivery_score"],
                quality_score=s["quality_score"],
                warranty_score=s["warranty_score"],
                payment_score=s["payment_score"],
                compliance_score=s["compliance_score"],
                final_score=s["final_score"],
                rank=s["rank"],
            )
            db.add(score_obj)
            created_scores.append(score_obj)

        db.commit()

        # 4. Prepare Vendor Data for AI Decision Trace
        ranked_vendors_data = []
        for s in score_dicts:
            v_obj = db.query(Vendor).filter(Vendor.id == s["vendor_id"]).first()
            q_obj = next((q for q in quotations if q.vendor_id == s["vendor_id"]), None)
            
            unit_price = rfq.target_unit_price
            if q_obj and q_obj.items and len(q_obj.items) > 0:
                unit_price = q_obj.items[0].unit_price
            elif q_obj and rfq.quantity > 0:
                unit_price = q_obj.grand_total / rfq.quantity

            ranked_vendors_data.append({
                "vendor_id": s["vendor_id"],
                "name": v_obj.name if v_obj else f"Vendor #{s['vendor_id']}",
                "rank": s["rank"],
                "final_score": s["final_score"],
                "price_score": s["price_score"],
                "delivery_score": s["delivery_score"],
                "warranty_score": s["warranty_score"],
                "payment_score": s["payment_score"],
                "unit_price": unit_price,
                "delivery_days": q_obj.delivery_days if q_obj else 0,
                "warranty_years": q_obj.warranty_years if q_obj else 1,
                "payment_terms": q_obj.payment_terms if q_obj else "Net 30",
            })

        anomalies_dicts = [
            {
                "vendor_id": a.vendor_id,
                "type": a.type,
                "severity": a.severity,
                "message": a.message,
            }
            for a in created_anomalies
        ]

        # 5. AI Decision Trace and Negotiation Strategy
        decision_trace = AIService.generate_decision_trace(
            rfq_title=rfq.title,
            rfq_quantity=rfq.quantity,
            target_price=rfq.target_unit_price,
            max_delivery=rfq.max_delivery_days,
            min_warranty=rfq.min_warranty_years,
            ranked_vendors_data=ranked_vendors_data,
            anomalies_data=anomalies_dicts,
        )

        negotiation_strategy = AIService.generate_negotiation_strategy(
            ranked_vendors_data=ranked_vendors_data,
            target_price=rfq.target_unit_price,
        )

        recommended_vendor_id = decision_trace.get("recommended_vendor_id")
        summary_text = decision_trace.get("summary_of_tradeoffs", "")

        ai_analysis = AIAnalysis(
            rfq_id=rfq.id,
            recommended_vendor_id=recommended_vendor_id,
            summary=summary_text,
            decision_trace_json=json.dumps(decision_trace),
            negotiation_strategy=negotiation_strategy,
        )
        db.add(ai_analysis)

        # 6. Update RFQ Status to ANALYZED
        rfq.status = "ANALYZED"
        db.commit()

        # 7. Audit Log
        AuditService.log_action(
            db=db,
            entity_name="RFQ",
            entity_id=rfq.id,
            action="ANALYZED",
            details={
                "quotation_count": len(quotations),
                "anomalies_count": len(created_anomalies),
                "recommended_vendor_id": recommended_vendor_id,
            },
        )

        return cls.get_rfq_analysis(db, rfq_id)

    @classmethod
    def get_rfq_analysis(cls, db: Session, rfq_id: int) -> Dict[str, Any]:
        rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
        if not rfq:
            raise HTTPException(status_code=404, detail=f"RFQ with ID {rfq_id} not found")

        ai_analysis = db.query(AIAnalysis).filter(AIAnalysis.rfq_id == rfq_id).order_by(AIAnalysis.id.desc()).first()
        scores = db.query(VendorScore).filter(VendorScore.rfq_id == rfq_id).order_by(VendorScore.rank.asc()).all()
        anomalies = db.query(Anomaly).filter(Anomaly.rfq_id == rfq_id).order_by(Anomaly.id.asc()).all()

        recommended_vendor = None
        if ai_analysis and ai_analysis.recommended_vendor_id:
            recommended_vendor = db.query(Vendor).filter(Vendor.id == ai_analysis.recommended_vendor_id).first()

        decision_trace = {}
        if ai_analysis and ai_analysis.decision_trace_json:
            try:
                decision_trace = json.loads(ai_analysis.decision_trace_json)
            except Exception:
                decision_trace = {}

        return {
            "rfq_id": rfq.id,
            "rfq_number": rfq.rfq_number,
            "recommended_vendor": recommended_vendor,
            "scores": scores,
            "anomalies": anomalies,
            "summary": ai_analysis.summary if ai_analysis else "Analysis has not been run yet.",
            "decision_trace": decision_trace,
            "negotiation_strategy": ai_analysis.negotiation_strategy if ai_analysis else None,
        }

    @classmethod
    def recalculate(
        cls,
        db: Session,
        rfq_id: int,
        weights: ScoringWeights,
    ) -> Dict[str, Any]:
        """
        What-if Analysis: Recalculates vendor scores instantly with modified weights (No LLM needed).
        """
        rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
        if not rfq:
            raise HTTPException(status_code=404, detail=f"RFQ with ID {rfq_id} not found")

        quotations = db.query(Quotation).filter(Quotation.rfq_id == rfq_id).all()
        if not quotations:
            raise HTTPException(status_code=400, detail="No quotations available to recalculate.")

        # Get existing anomalies
        existing_anomalies = db.query(Anomaly).filter(Anomaly.rfq_id == rfq_id).all()
        quotation_anomalies_map: Dict[int, List[Anomaly]] = {}
        for a in existing_anomalies:
            quotation_anomalies_map.setdefault(a.quotation_id, []).append(a)

        # Recalculate scores
        score_dicts = ScoringService.evaluate_quotations(
            rfq=rfq,
            quotations=quotations,
            quotation_anomalies_map=quotation_anomalies_map,
            weights=weights,
        )

        # Update existing score records
        for s in score_dicts:
            existing = db.query(VendorScore).filter(
                VendorScore.rfq_id == rfq.id,
                VendorScore.vendor_id == s["vendor_id"],
            ).first()
            if existing:
                existing.price_score = s["price_score"]
                existing.delivery_score = s["delivery_score"]
                existing.quality_score = s["quality_score"]
                existing.warranty_score = s["warranty_score"]
                existing.payment_score = s["payment_score"]
                existing.compliance_score = s["compliance_score"]
                existing.final_score = s["final_score"]
                existing.rank = s["rank"]
            else:
                db.add(VendorScore(
                    rfq_id=rfq.id,
                    vendor_id=s["vendor_id"],
                    price_score=s["price_score"],
                    delivery_score=s["delivery_score"],
                    quality_score=s["quality_score"],
                    warranty_score=s["warranty_score"],
                    payment_score=s["payment_score"],
                    compliance_score=s["compliance_score"],
                    final_score=s["final_score"],
                    rank=s["rank"],
                ))

        # Update recommended vendor in AIAnalysis
        top_score = next((s for s in score_dicts if s["rank"] == 1), None)
        if top_score:
            top_vendor = db.query(Vendor).filter(Vendor.id == top_score["vendor_id"]).first()
            ai_analysis = db.query(AIAnalysis).filter(AIAnalysis.rfq_id == rfq_id).order_by(AIAnalysis.id.desc()).first()
            if ai_analysis:
                ai_analysis.recommended_vendor_id = top_score["vendor_id"]
                ai_analysis.summary = (
                    f"Recalculated with custom weights. Top recommended vendor is "
                    f"{top_vendor.name if top_vendor else 'Vendor'} with score {top_score['final_score']}/100."
                )

        db.commit()

        AuditService.log_action(
            db=db,
            entity_name="RFQ",
            entity_id=rfq.id,
            action="RECALCULATED",
            details={"weights": weights.model_dump()},
        )

        return cls.get_rfq_analysis(db, rfq_id)
