"""
Deterministic vendor scoring and ranking engine.
"""

import re
from typing import Dict, Any, List, Optional
from ai.config import DEFAULT_WEIGHTS


def parse_payment_days(payment_terms: str) -> int:
    """
    Extracts payment term duration in days from string (e.g. 'Net 30', '45 days').
    """
    if not payment_terms:
        return 15

    terms_lower = str(payment_terms).lower()
    match = re.search(r"(\d+)", terms_lower)
    if match:
        return int(match.group(1))

    if "immediate" in terms_lower or "advance" in terms_lower:
        return 0
    return 15


def calculate_vendor_scores(
    quotations_with_anomalies: List[Dict[str, Any]],
    rfq_requirements: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """
    Calculates deterministic component scores and weighted final scores for vendors.

    Args:
        quotations_with_anomalies: List of dicts, each containing:
            - "quotation": extracted quotation dict
            - "anomalies": list of detected anomaly dicts
            - "matches": (optional) requirement match list
        rfq_requirements: RFQ specification rules dict.
        weights: Optional dictionary overriding default component weights.

    Returns:
        List of vendor score result dicts, sorted by rank (rank 1 is best).
    """
    if not quotations_with_anomalies:
        return []

    effective_weights = DEFAULT_WEIGHTS.copy()
    if weights:
        effective_weights.update(weights)

    # Normalize weights so they sum to 1.0
    total_weight_sum = sum(effective_weights.values())
    if total_weight_sum > 0:
        normalized_weights = {k: v / total_weight_sum for k, v in effective_weights.items()}
    else:
        normalized_weights = DEFAULT_WEIGHTS.copy()

    # Pre-extract values to compute relative metrics across vendors
    unit_prices = []
    delivery_days_list = []
    warranty_years_list = []
    payment_days_list = []

    target_price = float(rfq_requirements.get("target_unit_price", 0.0))
    target_delivery = int(rfq_requirements.get("max_delivery_days", 15))
    target_warranty = float(rfq_requirements.get("min_warranty_years", 3.0))

    for item in quotations_with_anomalies:
        q = item.get("quotation", {})
        price = float(q.get("unit_price", 0.0))
        delivery = int(q.get("delivery_days", 0))
        warranty = float(q.get("warranty_years", 0.0))
        payment = parse_payment_days(str(q.get("payment_terms", "")))

        if price > 0:
            unit_prices.append(price)
        if delivery > 0:
            delivery_days_list.append(delivery)
        warranty_years_list.append(warranty)
        payment_days_list.append(payment)

    min_price = min(unit_prices) if unit_prices else target_price
    min_delivery = min(delivery_days_list) if delivery_days_list else target_delivery
    max_warranty = max(warranty_years_list) if warranty_years_list and max(warranty_years_list) > 0 else max(target_warranty, 1.0)
    max_payment = max(payment_days_list) if payment_days_list and max(payment_days_list) > 0 else 45.0

    scored_vendors: List[Dict[str, Any]] = []

    for item in quotations_with_anomalies:
        q = item.get("quotation", {})
        anomalies = item.get("anomalies", [])

        vendor_name = str(q.get("vendor_name", "Unknown Vendor"))
        price = float(q.get("unit_price", 0.0))
        delivery = int(q.get("delivery_days", 0))
        warranty = float(q.get("warranty_years", 0.0))
        payment_days = parse_payment_days(str(q.get("payment_terms", "")))

        # 1. Price Score (0 - 100)
        if len(unit_prices) > 1 and min_price > 0 and price > 0:
            price_score = (min_price / price) * 100.0
        elif target_price > 0 and price > 0:
            if price <= target_price:
                price_score = 100.0
            else:
                price_score = max(0.0, 100.0 - ((price - target_price) / target_price) * 100.0)
        else:
            price_score = 50.0

        # 2. Delivery Score (0 - 100)
        if len(delivery_days_list) > 1 and min_delivery > 0 and delivery > 0:
            delivery_score = (min_delivery / delivery) * 100.0
        elif delivery > 0:
            if delivery <= target_delivery:
                delivery_score = 100.0
            else:
                delivery_score = max(0.0, 100.0 - (delivery - target_delivery) * 5.0)
        else:
            delivery_score = 0.0

        # 3. Quality Score (0 - 100)
        # Quality baseline based on specs matching and presence of warranty
        quality_score = 100.0
        if warranty < target_warranty:
            quality_score -= 20.0

        # 4. Warranty Score (0 - 100)
        if max_warranty > 0:
            warranty_score = min(100.0, (warranty / max_warranty) * 100.0)
        else:
            warranty_score = 50.0

        # 5. Payment Score (0 - 100)
        if max_payment > 0:
            payment_score = min(100.0, (payment_days / max_payment) * 100.0)
        else:
            payment_score = 50.0

        # 6. Compliance Score (0 - 100)
        compliance_score = 100.0
        for anomaly in anomalies:
            severity = str(anomaly.get("severity", "")).upper()
            if severity == "CRITICAL":
                compliance_score -= 40.0
            elif severity == "WARNING":
                compliance_score -= 15.0
            elif severity == "INFO":
                compliance_score -= 5.0
        compliance_score = max(0.0, compliance_score)

        component_scores = {
            "price": round(max(0.0, min(100.0, price_score)), 2),
            "delivery": round(max(0.0, min(100.0, delivery_score)), 2),
            "quality": round(max(0.0, min(100.0, quality_score)), 2),
            "warranty": round(max(0.0, min(100.0, warranty_score)), 2),
            "payment": round(max(0.0, min(100.0, payment_score)), 2),
            "compliance": round(max(0.0, min(100.0, compliance_score)), 2),
        }

        weighted_scores = {
            comp: round(component_scores[comp] * normalized_weights.get(comp, 0.0), 2)
            for comp in component_scores
        }

        final_score = round(sum(weighted_scores.values()), 2)

        scored_vendors.append({
            "vendor_name": vendor_name,
            "quotation_number": q.get("quotation_number", ""),
            "component_scores": component_scores,
            "weights": {k: round(v, 4) for k, v in normalized_weights.items()},
            "weighted_scores": weighted_scores,
            "final_score": final_score,
            "anomalies_count": len(anomalies),
            "critical_anomalies_count": sum(1 for a in anomalies if a.get("severity") == "CRITICAL"),
        })

    # Sort vendors by final_score descending
    scored_vendors.sort(key=lambda x: x["final_score"], reverse=True)

    # Assign 1-indexed rank
    for rank_idx, vendor in enumerate(scored_vendors, start=1):
        vendor["rank"] = rank_idx

    return scored_vendors
