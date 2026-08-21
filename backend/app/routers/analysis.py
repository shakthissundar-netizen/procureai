from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.analysis import (
    RecalculateRequest,
    RecommendationResponse,
    ApproveRFQRequest,
    ScoringWeights,
)
from backend.app.schemas.purchase_order import PurchaseOrderResponse
from backend.app.services.analysis_service import AnalysisService
from backend.app.services.po_service import POService

router = APIRouter(prefix="/rfqs", tags=["Analysis & Recommendations"])


@router.post("/{id}/analyze", response_model=RecommendationResponse)
def analyze_rfq(
    id: int,
    recalc_in: Optional[RecalculateRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Triggers complete RFQ quotation intelligence pipeline:
    1. Requirement Validation & Anomaly Detection
    2. Deterministic 0-100 Vendor Scoring
    3. Vendor Ranking
    4. AI Decision Trace & Negotiation Tactics
    """
    weights = recalc_in.weights if recalc_in and recalc_in.weights else None
    return AnalysisService.run_rfq_analysis(db=db, rfq_id=id, weights=weights)


@router.get("/{id}/analysis", response_model=RecommendationResponse)
def get_rfq_analysis(id: int, db: Session = Depends(get_db)):
    """
    Retrieves the latest analysis, scores, anomalies, and AI decision trace for the RFQ.
    """
    return AnalysisService.get_rfq_analysis(db=db, rfq_id=id)


@router.get("/{id}/recommendation", response_model=RecommendationResponse)
def get_rfq_recommendation(id: int, db: Session = Depends(get_db)):
    """
    Retrieves top recommended vendor and key decision trade-offs for the RFQ.
    """
    return AnalysisService.get_rfq_analysis(db=db, rfq_id=id)


@router.post("/{id}/recalculate", response_model=RecommendationResponse)
def recalculate_rfq_scores(
    id: int,
    recalc_in: RecalculateRequest,
    db: Session = Depends(get_db),
):
    """
    What-if Analysis: Dynamically recalculates scores and rankings with custom weights.
    Instant response without requiring LLM inference.
    """
    weights = recalc_in.weights or ScoringWeights()
    return AnalysisService.recalculate(db=db, rfq_id=id, weights=weights)


@router.post("/{id}/approve", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
def approve_rfq_recommendation(
    id: int,
    approval_in: Optional[ApproveRFQRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Human Approval: Approves the recommended vendor (or specified vendor) and generates a formal Purchase Order.
    """
    return POService.approve_rfq_and_create_po(db=db, rfq_id=id, approval_in=approval_in)
