from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.vendor import VendorResponse


class ScoringWeights(BaseModel):
    price_weight: float = Field(0.30, ge=0.0, le=1.0)
    delivery_weight: float = Field(0.25, ge=0.0, le=1.0)
    quality_weight: float = Field(0.20, ge=0.0, le=1.0)
    warranty_weight: float = Field(0.10, ge=0.0, le=1.0)
    payment_weight: float = Field(0.10, ge=0.0, le=1.0)
    compliance_weight: float = Field(0.05, ge=0.0, le=1.0)


class RecalculateRequest(BaseModel):
    weights: Optional[ScoringWeights] = None


class VendorScoreResponse(BaseModel):
    id: int
    rfq_id: int
    vendor_id: int
    vendor: Optional[VendorResponse] = None
    price_score: float
    delivery_score: float
    quality_score: float
    warranty_score: float
    payment_score: float
    compliance_score: float
    final_score: float
    rank: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnomalyResponse(BaseModel):
    id: int
    rfq_id: int
    quotation_id: Optional[int] = None
    vendor_id: Optional[int] = None
    vendor: Optional[VendorResponse] = None
    type: str
    severity: str
    message: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DecisionTraceItem(BaseModel):
    vendor_name: str
    vendor_id: int
    strengths: List[str] = []
    risks: List[str] = []
    compliance_summary: str
    commercial_terms: str
    final_score: float
    rank: int


class DecisionTrace(BaseModel):
    recommended_vendor: str
    summary_of_tradeoffs: str
    vendor_evaluations: List[DecisionTraceItem] = []


class AIAnalysisResponse(BaseModel):
    id: int
    rfq_id: int
    recommended_vendor_id: Optional[int] = None
    recommended_vendor: Optional[VendorResponse] = None
    summary: str
    decision_trace: Optional[Dict[str, Any]] = None
    negotiation_strategy: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseModel):
    rfq_id: int
    rfq_number: str
    recommended_vendor: Optional[VendorResponse] = None
    scores: List[VendorScoreResponse] = []
    anomalies: List[AnomalyResponse] = []
    summary: str
    decision_trace: Optional[Dict[str, Any]] = None
    negotiation_strategy: Optional[str] = None


class ApproveRFQRequest(BaseModel):
    vendor_id: Optional[int] = None
    delivery_terms: Optional[str] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
