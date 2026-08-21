"""
Requirement matching engine comparing extracted quotations against RFQ specifications.
"""

from typing import Dict, Any, List


def match_quotation_requirements(
    quotation_data: Dict[str, Any],
    rfq_requirements: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Compares extracted quotation data against RFQ requirements.

    Args:
        quotation_data: Extracted quotation dictionary.
        rfq_requirements: RFQ rules dictionary containing expected values.
            Expected keys (optional with fallbacks):
            - max_delivery_days (int)
            - min_warranty_years (float)
            - target_unit_price (float)
            - required_quantity (int)
            - required_product_specs (list[str])

    Returns:
        List of matching result items with fields:
        - requirement: str
        - expected: str
        - actual: str
        - passed: bool
        - explanation: str
    """
    results: List[Dict[str, Any]] = []

    # 1. Delivery Requirement
    if "max_delivery_days" in rfq_requirements:
        max_delivery = int(rfq_requirements["max_delivery_days"])
        actual_delivery = int(quotation_data.get("delivery_days", 0))
        passed = actual_delivery <= max_delivery
        diff = actual_delivery - max_delivery

        explanation = (
            f"Vendor meets delivery requirement ({actual_delivery} days <= {max_delivery} days)."
            if passed
            else f"Vendor exceeds delivery requirement by {diff} days."
        )

        results.append({
            "requirement": "Maximum delivery",
            "expected": f"<= {max_delivery} days",
            "actual": f"{actual_delivery} days",
            "passed": passed,
            "explanation": explanation,
        })

    # 2. Warranty Requirement
    if "min_warranty_years" in rfq_requirements:
        min_warranty = float(rfq_requirements["min_warranty_years"])
        actual_warranty = float(quotation_data.get("warranty_years", 0.0))
        passed = actual_warranty >= min_warranty

        explanation = (
            f"Vendor satisfies warranty requirement ({actual_warranty} years >= {min_warranty} years)."
            if passed
            else f"Vendor warranty ({actual_warranty} years) is below required {min_warranty} years."
        )

        results.append({
            "requirement": "Minimum warranty",
            "expected": f">= {min_warranty} years",
            "actual": f"{actual_warranty} years",
            "passed": passed,
            "explanation": explanation,
        })

    # 3. Target Unit Price Requirement
    if "target_unit_price" in rfq_requirements:
        target_price = float(rfq_requirements["target_unit_price"])
        actual_price = float(quotation_data.get("unit_price", 0.0))
        passed = actual_price <= target_price
        diff_pct = abs(actual_price - target_price) / target_price * 100 if target_price > 0 else 0.0

        if passed:
            explanation = f"Vendor unit price (₹{actual_price:,.2f}) is within target price (₹{target_price:,.2f})."
        else:
            explanation = f"Vendor unit price (₹{actual_price:,.2f}) exceeds target price (₹{target_price:,.2f}) by {diff_pct:.1f}%."

        results.append({
            "requirement": "Target unit price",
            "expected": f"<= ₹{target_price:,.2f}",
            "actual": f"₹{actual_price:,.2f}",
            "passed": passed,
            "explanation": explanation,
        })

    # 4. Required Quantity Requirement
    if "required_quantity" in rfq_requirements:
        req_qty = int(rfq_requirements["required_quantity"])
        actual_qty = int(quotation_data.get("quantity", 0))
        passed = actual_qty >= req_qty

        explanation = (
            f"Quoted quantity ({actual_qty}) meets required quantity ({req_qty})."
            if passed
            else f"Quoted quantity ({actual_qty}) is below required quantity ({req_qty})."
        )

        results.append({
            "requirement": "Required quantity",
            "expected": f">= {req_qty}",
            "actual": f"{actual_qty}",
            "passed": passed,
            "explanation": explanation,
        })

    # 5. Product Specifications Check
    if "required_product_specs" in rfq_requirements and isinstance(rfq_requirements["required_product_specs"], list):
        prod_name = str(quotation_data.get("product_name", "")).lower()
        req_specs = rfq_requirements["required_product_specs"]

        matched_specs = [spec for spec in req_specs if any(term.lower() in prod_name for term in str(spec).split())]
        passed = len(matched_specs) > 0 or len(req_specs) == 0

        results.append({
            "requirement": "Product specifications",
            "expected": ", ".join([str(s) for s in req_specs]),
            "actual": str(quotation_data.get("product_name", "")),
            "passed": passed,
            "explanation": (
                "Product description aligns with RFQ specification."
                if passed
                else "Product description may require technical specification verification."
            ),
        })

    return results
