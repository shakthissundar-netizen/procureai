from typing import List, Dict, Any
from backend.app.models.rfq import RFQ
from backend.app.models.quotation import Quotation


class AnomalyService:
    """
    Rule-based and data integrity Anomaly Detection Engine.
    Detects violations against RFQ requirements and quotation mathematical inconsistencies.
    """

    @staticmethod
    def detect_anomalies(rfq: RFQ, quotation: Quotation) -> List[Dict[str, Any]]:
        anomalies: List[Dict[str, Any]] = []

        # 1. Delivery Timeline Violation
        if quotation.delivery_days > rfq.max_delivery_days:
            anomalies.append({
                "rfq_id": rfq.id,
                "quotation_id": quotation.id,
                "vendor_id": quotation.vendor_id,
                "type": "DELIVERY_VIOLATION",
                "severity": "CRITICAL",
                "message": f"Delivery timeline of {quotation.delivery_days} days exceeds maximum required {rfq.max_delivery_days} days.",
                "expected_value": f"<= {rfq.max_delivery_days} days",
                "actual_value": f"{quotation.delivery_days} days",
            })

        # 2. Warranty Violation
        if quotation.warranty_years < rfq.min_warranty_years:
            anomalies.append({
                "rfq_id": rfq.id,
                "quotation_id": quotation.id,
                "vendor_id": quotation.vendor_id,
                "type": "WARRANTY_VIOLATION",
                "severity": "CRITICAL",
                "message": f"Warranty of {quotation.warranty_years} year(s) is below the required minimum of {rfq.min_warranty_years} year(s).",
                "expected_value": f">= {rfq.min_warranty_years} years",
                "actual_value": f"{quotation.warranty_years} years",
            })

        # 3. Item Calculation Mismatch & Grand Total Inconsistency
        calculated_items_total = 0.0
        if quotation.items:
            for idx, item in enumerate(quotation.items, start=1):
                item_expected_total = round(item.quantity * item.unit_price, 2)
                if abs(item.total_price - item_expected_total) > 0.01:
                    anomalies.append({
                        "rfq_id": rfq.id,
                        "quotation_id": quotation.id,
                        "vendor_id": quotation.vendor_id,
                        "type": "PRICE_MISMATCH",
                        "severity": "CRITICAL",
                        "message": f"Line item #{idx} ({item.product_name}) total calculation mismatch: {item.quantity} x ₹{item.unit_price:,.2f} = ₹{item_expected_total:,.2f}, but quoted ₹{item.total_price:,.2f}.",
                        "expected_value": f"₹{item_expected_total:,.2f}",
                        "actual_value": f"₹{item.total_price:,.2f}",
                    })
                calculated_items_total += item.total_price
        else:
            calculated_items_total = quotation.grand_total - quotation.tax_amount - quotation.additional_charges

        expected_grand_total = round(
            calculated_items_total + quotation.tax_amount + quotation.additional_charges, 2
        )

        if abs(quotation.grand_total - expected_grand_total) > 1.0:
            anomalies.append({
                "rfq_id": rfq.id,
                "quotation_id": quotation.id,
                "vendor_id": quotation.vendor_id,
                "type": "TOTAL_MISMATCH",
                "severity": "CRITICAL",
                "message": f"Grand total mismatch: Sum of items (₹{calculated_items_total:,.2f}) + Tax (₹{quotation.tax_amount:,.2f}) + Charges (₹{quotation.additional_charges:,.2f}) equals ₹{expected_grand_total:,.2f}, but quotation states ₹{quotation.grand_total:,.2f}.",
                "expected_value": f"₹{expected_grand_total:,.2f}",
                "actual_value": f"₹{quotation.grand_total:,.2f}",
            })

        # 4. Unexpected or Disproportionate Additional Charges
        if quotation.grand_total > 0 and quotation.additional_charges > (0.10 * quotation.grand_total):
            anomalies.append({
                "rfq_id": rfq.id,
                "quotation_id": quotation.id,
                "vendor_id": quotation.vendor_id,
                "type": "UNEXPECTED_CHARGES",
                "severity": "WARNING",
                "message": f"Additional charges of ₹{quotation.additional_charges:,.2f} represent >10% of quotation total.",
                "expected_value": "< 10% of total",
                "actual_value": f"₹{quotation.additional_charges:,.2f} ({round((quotation.additional_charges / quotation.grand_total) * 100, 1)}%)",
            })

        # 5. Suspicious Pricing (significantly exceeding target or suspiciously low)
        unit_price = 0.0
        if quotation.items and len(quotation.items) > 0:
            unit_price = quotation.items[0].unit_price
        elif rfq.quantity > 0:
            unit_price = quotation.grand_total / rfq.quantity

        if rfq.target_unit_price > 0 and unit_price > 0:
            if unit_price > (1.35 * rfq.target_unit_price):
                anomalies.append({
                    "rfq_id": rfq.id,
                    "quotation_id": quotation.id,
                    "vendor_id": quotation.vendor_id,
                    "type": "SUSPICIOUS_PRICING",
                    "severity": "WARNING",
                    "message": f"Quoted unit price (₹{unit_price:,.2f}) is over 35% higher than target budget (₹{rfq.target_unit_price:,.2f}).",
                    "expected_value": f"<= ₹{rfq.target_unit_price:,.2f}",
                    "actual_value": f"₹{unit_price:,.2f}",
                })
            elif unit_price < (0.50 * rfq.target_unit_price):
                anomalies.append({
                    "rfq_id": rfq.id,
                    "quotation_id": quotation.id,
                    "vendor_id": quotation.vendor_id,
                    "type": "SUSPICIOUS_PRICING",
                    "severity": "WARNING",
                    "message": f"Quoted unit price (₹{unit_price:,.2f}) is unusually low (<50% of target budget), indicating possible omission or counterfeit parts.",
                    "expected_value": f"~ ₹{rfq.target_unit_price:,.2f}",
                    "actual_value": f"₹{unit_price:,.2f}",
                })

        # 6. Missing or Invalid Payment Terms
        if not quotation.payment_terms or quotation.payment_terms.strip() == "":
            anomalies.append({
                "rfq_id": rfq.id,
                "quotation_id": quotation.id,
                "vendor_id": quotation.vendor_id,
                "type": "MISSING_FIELD",
                "severity": "WARNING",
                "message": "Payment terms were not specified in the quotation.",
                "expected_value": "Explicit payment terms (e.g. Net 30)",
                "actual_value": "Empty/Missing",
            })

        return anomalies
