"""
Deterministic anomaly detection for vendor quotations.
"""

from typing import Dict, Any, List


def detect_anomalies(
    quotation_data: Dict[str, Any],
    rfq_requirements: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Performs deterministic verification of financial totals, policy rules, and fields.

    Detects:
    1. DELIVERY_VIOLATION (delivery_days > max_delivery_days)
    2. WARRANTY_VIOLATION (warranty_years < min_warranty_years)
    3. PRICE_TOTAL_MISMATCH (subtotal + tax + charges != grand_total)
    4. TAX_INCONSISTENCY (negative or unusual tax percentages)
    5. UNEXPECTED_ADDITIONAL_CHARGES (extra fees present)
    6. MISSING_FIELDS (empty vendor, quotation_number, etc.)
    7. SUSPICIOUS_PRICING (unit_price significantly deviating from target_price)

    Returns:
        List of detected anomaly records.
    """
    anomalies: List[Dict[str, Any]] = []

    # Safe extraction of basic numeric fields
    quantity = int(quotation_data.get("quantity", 0))
    unit_price = float(quotation_data.get("unit_price", 0.0))
    delivery_days = int(quotation_data.get("delivery_days", 0))
    warranty_years = float(quotation_data.get("warranty_years", 0.0))
    tax_percentage = float(quotation_data.get("tax_percentage", 0.0))
    additional_charges = float(quotation_data.get("additional_charges", 0.0))
    grand_total = float(quotation_data.get("grand_total", 0.0))

    vendor_name = str(quotation_data.get("vendor_name", "")).strip()
    quotation_number = str(quotation_data.get("quotation_number", "")).strip()

    # 1. Missing Fields Check
    missing_fields = []
    if not vendor_name:
        missing_fields.append("vendor_name")
    if not quotation_number:
        missing_fields.append("quotation_number")
    if quantity <= 0:
        missing_fields.append("quantity")
    if unit_price <= 0:
        missing_fields.append("unit_price")

    if missing_fields:
        anomalies.append({
            "anomaly_type": "MISSING_FIELDS",
            "severity": "CRITICAL" if ("vendor_name" in missing_fields or quantity <= 0) else "WARNING",
            "message": f"Quotation is missing critical field(s): {', '.join(missing_fields)}.",
            "expected_value": "Non-empty valid fields",
            "actual_value": f"Missing: {missing_fields}",
        })

    # 2. Financial Total Mismatch (Deterministic Math Calculation)
    subtotal = quantity * unit_price
    tax_amount = subtotal * (tax_percentage / 100.0)
    expected_total = round(subtotal + tax_amount + additional_charges, 2)

    diff = abs(expected_total - grand_total)
    if diff > 1.0:  # Tolerance threshold for floating point / rounding
        anomalies.append({
            "anomaly_type": "PRICE_TOTAL_MISMATCH",
            "severity": "CRITICAL",
            "message": (
                f"Quoted grand total (₹{grand_total:,.2f}) does not match calculated total "
                f"(₹{expected_total:,.2f} = subtotal ₹{subtotal:,.2f} + tax ₹{tax_amount:,.2f} + charges ₹{additional_charges:,.2f}). "
                f"Discrepancy of ₹{diff:,.2f}."
            ),
            "expected_value": f"₹{expected_total:,.2f}",
            "actual_value": f"₹{grand_total:,.2f}",
        })

    # 3. Delivery Violation
    if "max_delivery_days" in rfq_requirements:
        max_delivery = int(rfq_requirements["max_delivery_days"])
        if delivery_days > max_delivery:
            anomalies.append({
                "anomaly_type": "DELIVERY_VIOLATION",
                "severity": "CRITICAL",
                "message": f"Delivery timeline ({delivery_days} days) exceeds maximum allowed ({max_delivery} days).",
                "expected_value": f"<= {max_delivery} days",
                "actual_value": f"{delivery_days} days",
            })

    # 4. Warranty Violation
    if "min_warranty_years" in rfq_requirements:
        min_warranty = float(rfq_requirements["min_warranty_years"])
        if warranty_years < min_warranty:
            anomalies.append({
                "anomaly_type": "WARRANTY_VIOLATION",
                "severity": "WARNING",
                "message": f"Warranty period ({warranty_years} years) is below required minimum ({min_warranty} years).",
                "expected_value": f">= {min_warranty} years",
                "actual_value": f"{warranty_years} years",
            })

    # 5. Tax Inconsistency
    if tax_percentage < 0 or tax_percentage > 30.0:
        anomalies.append({
            "anomaly_type": "TAX_INCONSISTENCY",
            "severity": "WARNING",
            "message": f"Quoted tax percentage ({tax_percentage}%) is unusual or outside standard range (0-30%).",
            "expected_value": "0.0% to 30.0%",
            "actual_value": f"{tax_percentage}%",
        })

    # 6. Unexpected Additional Charges
    if additional_charges > 0:
        subtotal_threshold = subtotal * 0.05 if subtotal > 0 else 0
        severity = "WARNING" if (subtotal_threshold > 0 and additional_charges > subtotal_threshold) else "INFO"
        anomalies.append({
            "anomaly_type": "UNEXPECTED_ADDITIONAL_CHARGES",
            "severity": severity,
            "message": f"Quotation includes unexpected additional charges of ₹{additional_charges:,.2f}.",
            "expected_value": "₹0.00 additional charges",
            "actual_value": f"₹{additional_charges:,.2f}",
        })

    # 7. Suspicious Pricing
    if "target_unit_price" in rfq_requirements and unit_price > 0:
        target_price = float(rfq_requirements["target_unit_price"])
        if unit_price > target_price * 1.5:
            anomalies.append({
                "anomaly_type": "SUSPICIOUS_PRICING",
                "severity": "WARNING",
                "message": f"Unit price (₹{unit_price:,.2f}) is more than 50% above target price (₹{target_price:,.2f}).",
                "expected_value": f"<= ₹{target_price * 1.5:,.2f}",
                "actual_value": f"₹{unit_price:,.2f}",
            })
        elif unit_price < target_price * 0.4:
            anomalies.append({
                "anomaly_type": "SUSPICIOUS_PRICING",
                "severity": "WARNING",
                "message": f"Unit price (₹{unit_price:,.2f}) is suspiciously low compared to target price (₹{target_price:,.2f}).",
                "expected_value": f">= ₹{target_price * 0.4:,.2f}",
                "actual_value": f"₹{unit_price:,.2f}",
            })

    return anomalies
