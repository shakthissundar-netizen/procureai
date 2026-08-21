from typing import List, Optional, Any, Dict
from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    total_rfqs: int
    active_rfqs: int
    completed_rfqs: int
    total_vendors: int
    total_quotations: int
    total_purchase_orders: int
    total_spend: float
    total_anomalies_detected: int
    critical_anomalies: int
    recent_rfqs: List[Dict[str, Any]] = []
    recent_anomalies: List[Dict[str, Any]] = []
    recent_purchase_orders: List[Dict[str, Any]] = []
