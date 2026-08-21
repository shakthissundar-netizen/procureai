import re
from typing import List, Dict, Any, Tuple
from backend.app.schemas.analysis import ScoringWeights
from backend.app.models.rfq import RFQ
from backend.app.models.quotation import Quotation
from backend.app.models.vendor import Vendor


class ScoringService:
    """
    Deterministic Vendor Scoring Engine.
    All component scores are normalized to 0-100 before applying weights.
    The scoring is 100% reproducible and transparent.
    """

    @staticmethod
    def calculate_price_score(unit_price: float, target_price: float, min_price_in_batch: float) -> float:
        """
        Normalized Price Score (0-100).
        Lower price yields higher score.
        """
        if unit_price <= 0 or target_price <= 0:
            return 50.0
        
        # If price is at or below lowest in batch
        if unit_price <= min_price_in_batch:
            return 100.0
        
        # Relative to target price
        ratio = unit_price / target_price
        if ratio <= 0.8:
            return 100.0
        elif ratio <= 1.0:
            # 80 to 100
            return round(100.0 - ((ratio - 0.8) / 0.2) * 20.0, 2)
        elif ratio <= 1.2:
            # 50 to 80
            return round(80.0 - ((ratio - 1.0) / 0.2) * 30.0, 2)
        else:
            # Under 50
            return max(0.0, round(50.0 - ((ratio - 1.2) / 0.3) * 50.0, 2))

    @staticmethod
    def calculate_delivery_score(delivery_days: int, max_delivery_days: int) -> float:
        """
        Normalized Delivery Score (0-100).
        Faster delivery within max_delivery_days gets top score.
        Violations beyond max_delivery_days are heavily penalized.
        """
        if max_delivery_days <= 0:
            return 70.0
        
        if delivery_days <= max_delivery_days:
            # Delivery within timeline: 75 to 100
            fraction = delivery_days / max_delivery_days
            return round(100.0 - (fraction * 25.0), 2)
        else:
            # Violation: 0 to 50
            excess_days = delivery_days - max_delivery_days
            penalty = excess_days * 5.0
            return max(0.0, round(50.0 - penalty, 2))

    @staticmethod
    def calculate_quality_score(vendor_rating: float) -> float:
        """
        Normalized Quality Score (0-100) based on vendor rating (out of 5).
        """
        if vendor_rating <= 0:
            return 50.0
        score = (min(vendor_rating, 5.0) / 5.0) * 100.0
        return round(score, 2)

    @staticmethod
    def calculate_warranty_score(warranty_years: int, min_warranty_years: int) -> float:
        """
        Normalized Warranty Score (0-100).
        Meets requirement: 80-100. Exceeds requirement: up to 100.
        Deficit: severe penalty.
        """
        if min_warranty_years <= 0:
            return 80.0
        
        if warranty_years >= min_warranty_years:
            extra = warranty_years - min_warranty_years
            return min(100.0, round(80.0 + (extra * 10.0), 2))
        else:
            deficit = min_warranty_years - warranty_years
            return max(0.0, round(50.0 - (deficit * 30.0), 2))

    @staticmethod
    def calculate_payment_score(payment_terms: str) -> float:
        """
        Normalized Payment Terms Score (0-100).
        Net 45 / Net 60 (favorable credit) > Net 30 > Net 15 > Advance.
        """
        terms_lower = (payment_terms or "").lower()
        
        # Check for numbers in payment terms (e.g. 45 days, 30 days)
        match = re.search(r'(\d+)\s*(?:days|day)?', terms_lower)
        if match:
            days = int(match.group(1))
            if days >= 60:
                return 100.0
            elif days >= 45:
                return 95.0
            elif days >= 30:
                return 85.0
            elif days >= 15:
                return 65.0
            else:
                return 45.0

        if "advance" in terms_lower or "immediate" in terms_lower or "prepaid" in terms_lower:
            return 30.0
        elif "milestone" in terms_lower:
            return 75.0
        
        return 70.0  # standard baseline

    @staticmethod
    def calculate_compliance_score(has_anomalies: bool, critical_count: int, warning_count: int) -> float:
        """
        Compliance score based on detected anomalies.
        No anomalies = 100.
        Critical anomalies reduce score significantly.
        """
        if not has_anomalies:
            return 100.0
        score = 100.0 - (critical_count * 35.0) - (warning_count * 10.0)
        return max(0.0, round(score, 2))

    @classmethod
    def evaluate_quotations(
        cls,
        rfq: RFQ,
        quotations: List[Quotation],
        quotation_anomalies_map: Dict[int, List[Any]],
        weights: ScoringWeights = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluates and ranks all quotations for an RFQ using deterministic scoring.
        """
        if weights is None:
            weights = ScoringWeights()

        if not quotations:
            return []

        # Find unit prices per quotation
        effective_unit_prices = []
        for q in quotations:
            if q.items and len(q.items) > 0:
                avg_unit = sum(item.unit_price for item in q.items) / len(q.items)
            elif q.grand_total > 0 and rfq.quantity > 0:
                avg_unit = q.grand_total / rfq.quantity
            else:
                avg_unit = rfq.target_unit_price
            effective_unit_prices.append(avg_unit)

        min_price = min(effective_unit_prices) if effective_unit_prices else rfq.target_unit_price

        scores = []
        for i, q in enumerate(quotations):
            unit_price = effective_unit_prices[i]
            vendor_rating = q.vendor.rating if q.vendor else 4.0

            anomalies = quotation_anomalies_map.get(q.id, [])
            critical_count = sum(1 for a in anomalies if getattr(a, "severity", "") == "CRITICAL")
            warning_count = sum(1 for a in anomalies if getattr(a, "severity", "") == "WARNING")
            has_anomalies = len(anomalies) > 0

            p_score = cls.calculate_price_score(unit_price, rfq.target_unit_price, min_price)
            d_score = cls.calculate_delivery_score(q.delivery_days, rfq.max_delivery_days)
            q_score = cls.calculate_quality_score(vendor_rating)
            w_score = cls.calculate_warranty_score(q.warranty_years, rfq.min_warranty_years)
            pay_score = cls.calculate_payment_score(q.payment_terms)
            comp_score = cls.calculate_compliance_score(has_anomalies, critical_count, warning_count)

            # Weighted sum
            final_score = (
                p_score * weights.price_weight
                + d_score * weights.delivery_weight
                + q_score * weights.quality_weight
                + w_score * weights.warranty_weight
                + pay_score * weights.payment_weight
                + comp_score * weights.compliance_weight
            )
            final_score = round(final_score, 2)

            scores.append({
                "rfq_id": rfq.id,
                "quotation_id": q.id,
                "vendor_id": q.vendor_id,
                "price_score": p_score,
                "delivery_score": d_score,
                "quality_score": q_score,
                "warranty_score": w_score,
                "payment_score": pay_score,
                "compliance_score": comp_score,
                "final_score": final_score,
            })

        # Sort descending by final score
        scores.sort(key=lambda x: x["final_score"], reverse=True)

        # Assign ranks
        for rank, item in enumerate(scores, start=1):
            item["rank"] = rank

        return scores
