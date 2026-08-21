"""Quotation normalization and mathematical validation module for ProcureAI.

Provides deterministic data sanitization, type coercion, mathematical cross-checking,
and rule-based anomaly detection without performing AI reasoning.
"""

import math
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from document_processing.types import (
    AnomalyReport,
    AnomalySeverity,
    AnomalyType,
    QuotationDict,
)


def _clean_numeric_string(val: Any) -> Optional[float]:
    """Strip currency symbols (₹, Rs, $, etc.), commas, and parse as float."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return None
        return float(val)

    s = str(val).strip()
    if not s or s.lower() in ("na", "n/a", "none", "null", "nil", "free", "-"):
        return 0.0 if s.lower() == "free" else None

    # Replace common currency markers & notations
    # e.g., "₹ 52,000.00/-", "Rs. 48500", "USD 5000", "INR 50,000"
    cleaned = re.sub(r"[₹$€£,/\-\s]", "", s)
    cleaned = re.sub(r"(?i)\b(inr|rs\.?|usd|eur|gbp|rupees?|units?|lakhs?|cr|crore)\b", "", cleaned).strip()

    # Match numeric float / int pattern
    match = re.search(r"[-+]?\d*\.?\d+", cleaned)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None


def parse_quantity(val: Any, default: int = 0) -> int:
    """Parse quantity value into a non-negative integer."""
    if val is None:
        return default
    num = _clean_numeric_string(val)
    if num is None:
        return default
    return max(0, int(round(num)))


def parse_currency_amount(val: Any, default: float = 0.0) -> float:
    """Parse monetary amount into float rounded to 2 decimal places."""
    if val is None:
        return default
    num = _clean_numeric_string(val)
    if num is None:
        return default
    return round(float(num), 2)


def parse_delivery_days(val: Any, default: int = 0) -> int:
    """Parse delivery period string/number into total number of days.

    Handles expressions like:
    - 10, "10", "10 days", "10-12 days" (takes upper bound 12 or exact 10)
    - "2 weeks" (14 days), "1 month" (30 days)
    - "15 business days" (15 days)
    """
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return max(0, int(round(float(val))))

    s = str(val).strip().lower()
    if not s:
        return default

    # Check for weeks
    week_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:week|wk)s?", s)
    if week_match:
        weeks = float(week_match.group(1))
        return int(round(weeks * 7))

    # Check for months
    month_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:month|mo)s?", s)
    if month_match:
        months = float(month_match.group(1))
        return int(round(months * 30))

    # Check for range: e.g. "10-15 days" -> take upper bound (15)
    range_match = re.search(r"(\d+)\s*(?:-|to)\s*(\d+)\s*(?:day|business day|working day)?s?", s)
    if range_match:
        return int(range_match.group(2))

    # Check for single number of days
    day_match = re.search(r"(\d+)", s)
    if day_match:
        return int(day_match.group(1))

    return default


def parse_warranty_years(val: Any, default: int = 0) -> int:
    """Parse warranty period into integer number of years.

    Handles expressions like:
    - 3, "3", "3 years", "3 yrs", "3 yr"
    - "36 months" (3 years), "60 months" (5 years), "24 mos" (2 years)
    - "18 months" (1.5 -> 1 or 2)
    """
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return max(0, int(round(float(val))))

    s = str(val).strip().lower()
    if not s:
        return default

    # Check for months: "36 months", "36 mos"
    month_match = re.search(r"(\d+)\s*(?:month|mo)s?", s)
    if month_match:
        months = int(month_match.group(1))
        return max(0, int(round(months / 12.0)))

    # Check for years: "3 years", "5 yrs"
    year_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:year|yr)s?", s)
    if year_match:
        years = float(year_match.group(1))
        return max(0, int(round(years)))

    # Fallback to plain number
    num_match = re.search(r"(\d+)", s)
    if num_match:
        return int(num_match.group(1))

    return default


def parse_tax_percentage(val: Any, default: float = 0.0) -> float:
    """Parse tax percentage into float between 0 and 100.

    Handles:
    - 18 -> 18.0
    - "18%" -> 18.0
    - 0.18 -> 18.0 (fractional representation)
    """
    if val is None:
        return default
    num = _clean_numeric_string(val)
    if num is None:
        return default

    # If expressed as decimal fraction e.g. 0.18 -> 18.0
    if 0 < num <= 1.0:
        return round(num * 100.0, 2)
    return round(float(num), 2)


def normalize_payment_terms(val: Any, default: str = "") -> str:
    """Standardize payment terms string."""
    if val is None:
        return default
    s = str(val).strip()
    if not s:
        return default

    # Standardize common variations
    lower = s.lower()
    if "30" in lower and ("day" in lower or "net" in lower):
        return "Net 30 Days"
    if "15" in lower and ("day" in lower or "net" in lower):
        return "Net 15 Days"
    if "45" in lower and ("day" in lower or "net" in lower):
        return "Net 45 Days"
    if "60" in lower and ("day" in lower or "net" in lower):
        return "Net 60 Days"
    if "advance" in lower or "100% advance" in lower:
        return "100% Advance"
    if "immediate" in lower or "cod" in lower or "delivery" in lower:
        return "Payment on Delivery"

    return s


def normalize_quotation(raw_data: Dict[str, Any]) -> QuotationDict:
    """Normalize raw dictionary (from AI extraction or spreadsheet) into standard QuotationDict.

    Args:
        raw_data: Dictionary with quotation fields in any casing/format.

    Returns:
        QuotationDict with guaranteed keys and correctly typed values.
    """
    if not isinstance(raw_data, dict):
        raw_data = {}

    # Case-insensitive lookup helper
    lookup: Dict[str, Any] = {}
    for k, v in raw_data.items():
        if isinstance(k, str):
            clean_key = k.strip().lower().replace(" ", "_").replace("-", "_")
            lookup[clean_key] = v

    def get_field(*keys: str, default: Any = None) -> Any:
        for k in keys:
            clean_k = k.lower().replace(" ", "_").replace("-", "_")
            if clean_k in lookup and lookup[clean_k] is not None:
                return lookup[clean_k]
        return default

    vendor_name = str(get_field("vendor_name", "vendor", "supplier", "company", "vendor_title", default="")).strip()
    quotation_number = str(get_field("quotation_number", "quotation_no", "quote_no", "quote_number", "reference_no", "ref_no", default="")).strip()
    product_name = str(get_field("product_name", "item_name", "product", "description", "item_description", default="")).strip()

    quantity = parse_quantity(get_field("quantity", "qty", "units", "ordered_quantity", default=0))
    unit_price = parse_currency_amount(get_field("unit_price", "price_per_unit", "rate", "unit_rate", default=0.0))
    delivery_days = parse_delivery_days(get_field("delivery_days", "delivery_time", "delivery_period", "lead_time", "delivery", default=0))
    warranty_years = parse_warranty_years(get_field("warranty_years", "warranty", "warranty_period", "warranty_duration", default=0))
    payment_terms = normalize_payment_terms(get_field("payment_terms", "payment_term", "payment", "commercial_terms", default=""))
    tax_percentage = parse_tax_percentage(get_field("tax_percentage", "tax_percent", "tax_rate", "gst_rate", "gst_percentage", "gst", "tax", default=0.0))
    additional_charges = parse_currency_amount(get_field("additional_charges", "shipping_charges", "freight", "handling_charges", "extra_charges", default=0.0))
    grand_total = parse_currency_amount(get_field("grand_total", "total_amount", "final_amount", "invoice_total", "total_price", "total", default=0.0))

    return QuotationDict(
        vendor_name=vendor_name,
        quotation_number=quotation_number,
        product_name=product_name,
        quantity=quantity,
        unit_price=unit_price,
        delivery_days=delivery_days,
        warranty_years=warranty_years,
        payment_terms=payment_terms,
        tax_percentage=tax_percentage,
        additional_charges=additional_charges,
        grand_total=grand_total,
    )


def validate_quotation_math(
    quotation: QuotationDict,
    tolerance: float = 5.0,
) -> Tuple[bool, float, List[AnomalyReport]]:
    """Verify financial calculation integrity of the quotation.

    Calculates:
        subtotal = quantity * unit_price
        tax_amount = subtotal * (tax_percentage / 100.0)
        expected_grand_total = subtotal + tax_amount + additional_charges

    Args:
        quotation: Standard QuotationDict.
        tolerance: Allowed currency deviation before flagging mismatch.

    Returns:
        Tuple of (is_valid, expected_grand_total, list_of_anomalies).
    """
    anomalies: List[AnomalyReport] = []
    qty = quotation.get("quantity", 0)
    unit_price = quotation.get("unit_price", 0.0)
    tax_pct = quotation.get("tax_percentage", 0.0)
    additional_charges = quotation.get("additional_charges", 0.0)
    stated_grand_total = quotation.get("grand_total", 0.0)

    calculated_subtotal = round(qty * unit_price, 2)
    calculated_tax = round(calculated_subtotal * (tax_pct / 100.0), 2)
    expected_grand_total = round(calculated_subtotal + calculated_tax + additional_charges, 2)

    is_valid = True

    # If both qty and unit_price are non-zero, check grand_total
    if qty > 0 and unit_price > 0 and stated_grand_total > 0:
        diff = abs(stated_grand_total - expected_grand_total)
        if diff > tolerance:
            is_valid = False
            anomalies.append(
                AnomalyReport(
                    anomaly_type=AnomalyType.GRAND_TOTAL_MISMATCH,
                    severity=AnomalySeverity.CRITICAL,
                    field="grand_total",
                    message=(
                        f"Grand total mismatch: stated ₹{stated_grand_total:,.2f} "
                        f"does not match calculated total ₹{expected_grand_total:,.2f} "
                        f"(Subtotal: ₹{calculated_subtotal:,.2f}, Tax {tax_pct}%: ₹{calculated_tax:,.2f}, "
                        f"Additional Charges: ₹{additional_charges:,.2f}, Diff: ₹{diff:,.2f})"
                    ),
                    expected_value=expected_grand_total,
                    actual_value=stated_grand_total,
                )
            )

    return is_valid, expected_grand_total, anomalies


def check_rfq_compliance(
    quotation: QuotationDict,
    rfq_requirements: Dict[str, Any],
) -> List[AnomalyReport]:
    """Check quotation against specified RFQ benchmark requirements.

    Detects:
    - Delivery violations (delivery_days > max_delivery_days)
    - Warranty violations (warranty_years < min_warranty_years)
    - Unexpected additional charges (additional_charges > 0)
    - Missing required fields

    Args:
        quotation: Normalized QuotationDict.
        rfq_requirements: RFQ specification dictionary.

    Returns:
        List of AnomalyReport items.
    """
    anomalies: List[AnomalyReport] = []

    # 1. Delivery violation
    max_delivery_days = rfq_requirements.get("max_delivery_days") or rfq_requirements.get("delivery_max_days")
    if max_delivery_days is not None:
        delivery_days = quotation.get("delivery_days", 0)
        if delivery_days > int(max_delivery_days):
            anomalies.append(
                AnomalyReport(
                    anomaly_type=AnomalyType.DELIVERY_VIOLATION,
                    severity=AnomalySeverity.CRITICAL,
                    field="delivery_days",
                    message=(
                        f"Delivery period ({delivery_days} days) violates RFQ requirement "
                        f"(<= {max_delivery_days} days)"
                    ),
                    expected_value=int(max_delivery_days),
                    actual_value=delivery_days,
                )
            )

    # 2. Warranty violation
    min_warranty_years = rfq_requirements.get("min_warranty_years") or rfq_requirements.get("warranty_min_years")
    if min_warranty_years is not None:
        warranty_years = quotation.get("warranty_years", 0)
        if warranty_years < int(min_warranty_years):
            anomalies.append(
                AnomalyReport(
                    anomaly_type=AnomalyType.WARRANTY_VIOLATION,
                    severity=AnomalySeverity.CRITICAL,
                    field="warranty_years",
                    message=(
                        f"Warranty period ({warranty_years} years) does not meet minimum requirement "
                        f"(>= {min_warranty_years} years)"
                    ),
                    expected_value=int(min_warranty_years),
                    actual_value=warranty_years,
                )
            )

    # 3. Additional charges warning
    additional_charges = quotation.get("additional_charges", 0.0)
    if additional_charges > 0:
        anomalies.append(
            AnomalyReport(
                anomaly_type=AnomalyType.ADDITIONAL_CHARGES_UNEXPECTED,
                severity=AnomalySeverity.WARNING,
                field="additional_charges",
                message=f"Quotation includes extra charges of ₹{additional_charges:,.2f}",
                expected_value=0.0,
                actual_value=additional_charges,
            )
        )

    # 4. Check for missing required fields
    required_fields = ["vendor_name", "unit_price", "quantity", "delivery_days", "warranty_years"]
    for f in required_fields:
        val = quotation.get(f)  # type: ignore
        if val is None or val == "" or val == 0:
            anomalies.append(
                AnomalyReport(
                    anomaly_type=AnomalyType.MISSING_FIELDS,
                    severity=AnomalySeverity.WARNING,
                    field=f,
                    message=f"Required quotation field '{f}' is missing or zero",
                    expected_value="non-empty / non-zero",
                    actual_value=val,
                )
            )

    return anomalies
