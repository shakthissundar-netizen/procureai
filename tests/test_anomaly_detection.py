"""Unit tests for Anomaly Detection and RFQ validation logic."""

from typing import Any, Dict

import pytest

from document_processing.normalizer import check_rfq_compliance, validate_quotation_math
from document_processing.types import AnomalySeverity, AnomalyType, QuotationDict


def test_delivery_violation_detection(standard_rfq: Dict[str, Any]):
    """Test detection of delivery timeline violation (e.g. 25 days > 15 days max)."""
    quote: QuotationDict = {
        "vendor_name": "BudgetByte Infotech Pvt Ltd",
        "quotation_number": "BB-409",
        "product_name": "Business Laptop",
        "quantity": 500,
        "unit_price": 48500.0,
        "delivery_days": 25,  # Violates 15 days requirement
        "warranty_years": 5,
        "payment_terms": "Net 15 Days",
        "tax_percentage": 18.0,
        "additional_charges": 25000.0,
        "grand_total": 27500000.0,
    }

    anomalies = check_rfq_compliance(quote, standard_rfq)
    delivery_anomalies = [a for a in anomalies if a.anomaly_type == AnomalyType.DELIVERY_VIOLATION]

    assert len(delivery_anomalies) == 1
    assert delivery_anomalies[0].severity == AnomalySeverity.CRITICAL
    assert delivery_anomalies[0].actual_value == 25
    assert delivery_anomalies[0].expected_value == 15
    assert "violates RFQ requirement" in delivery_anomalies[0].message


def test_warranty_violation_detection(standard_rfq: Dict[str, Any]):
    """Test detection of insufficient warranty period (e.g. 1 year < 3 years min)."""
    quote: QuotationDict = {
        "vendor_name": "Short Warranty Vendor",
        "quotation_number": "SW-101",
        "product_name": "Business Laptop",
        "quantity": 500,
        "unit_price": 47000.0,
        "delivery_days": 10,
        "warranty_years": 1,  # Violates min 3 years requirement
        "payment_terms": "Net 30 Days",
        "tax_percentage": 18.0,
        "additional_charges": 0.0,
        "grand_total": 27730000.0,
    }

    anomalies = check_rfq_compliance(quote, standard_rfq)
    warranty_anomalies = [a for a in anomalies if a.anomaly_type == AnomalyType.WARRANTY_VIOLATION]

    assert len(warranty_anomalies) == 1
    assert warranty_anomalies[0].severity == AnomalySeverity.CRITICAL
    assert warranty_anomalies[0].actual_value == 1
    assert warranty_anomalies[0].expected_value == 3


def test_grand_total_mismatch_detection():
    """Test detection of mathematical discrepancy in grand total (Vendor B scenario)."""
    # Subtotal: 500 * 48,500 = 24,250,000
    # Tax: 18% = 4,365,000
    # Addl Charges: 25,000
    # Correct Grand Total: 28,640,000
    # Stated Grand Total: 27,500,000 (Mismatch: 1,140,000)
    quote: QuotationDict = {
        "vendor_name": "BudgetByte Infotech Pvt Ltd",
        "quotation_number": "BB-409",
        "product_name": "Business Laptop",
        "quantity": 500,
        "unit_price": 48500.0,
        "delivery_days": 25,
        "warranty_years": 5,
        "payment_terms": "Net 15 Days",
        "tax_percentage": 18.0,
        "additional_charges": 25000.0,
        "grand_total": 27500000.0,
    }

    is_valid, expected_total, anomalies = validate_quotation_math(quote)

    assert not is_valid
    assert expected_total == 28640000.0
    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == AnomalyType.GRAND_TOTAL_MISMATCH
    assert anomalies[0].severity == AnomalySeverity.CRITICAL
    assert anomalies[0].expected_value == 28640000.0
    assert anomalies[0].actual_value == 27500000.0


def test_additional_charges_detection(standard_rfq: Dict[str, Any]):
    """Test detection and warning for unexpected extra charges."""
    quote: QuotationDict = {
        "vendor_name": "Extra Fee Vendor",
        "quotation_number": "EF-201",
        "product_name": "Business Laptop",
        "quantity": 500,
        "unit_price": 50000.0,
        "delivery_days": 10,
        "warranty_years": 3,
        "payment_terms": "Net 30 Days",
        "tax_percentage": 18.0,
        "additional_charges": 50000.0,  # Unexpected extra charges
        "grand_total": 29550000.0,
    }

    anomalies = check_rfq_compliance(quote, standard_rfq)
    fee_anomalies = [a for a in anomalies if a.anomaly_type == AnomalyType.ADDITIONAL_CHARGES_UNEXPECTED]

    assert len(fee_anomalies) == 1
    assert fee_anomalies[0].severity == AnomalySeverity.WARNING
    assert fee_anomalies[0].actual_value == 50000.0


def test_missing_fields_anomaly(standard_rfq: Dict[str, Any]):
    """Test detection of missing required quotation fields."""
    quote: QuotationDict = {
        "vendor_name": "",  # Missing
        "quotation_number": "Q-001",
        "product_name": "Laptop",
        "quantity": 0,  # Zero / missing
        "unit_price": 0.0,  # Zero / missing
        "delivery_days": 10,
        "warranty_years": 0,  # Missing
        "payment_terms": "Net 30",
        "tax_percentage": 18.0,
        "additional_charges": 0.0,
        "grand_total": 0.0,
    }

    anomalies = check_rfq_compliance(quote, standard_rfq)
    missing_anomalies = [a for a in anomalies if a.anomaly_type == AnomalyType.MISSING_FIELDS]
    missing_fields = {a.field for a in missing_anomalies}

    assert "vendor_name" in missing_fields
    assert "quantity" in missing_fields
    assert "unit_price" in missing_fields
    assert "warranty_years" in missing_fields


def test_valid_quotation_math_passes():
    """Test mathematical verification passes for accurate quotation (Vendor A & C scenario)."""
    quote_a: QuotationDict = {
        "vendor_name": "Apex Computech",
        "quotation_number": "APX-8801",
        "product_name": "Business Laptop",
        "quantity": 500,
        "unit_price": 52000.0,
        "delivery_days": 10,
        "warranty_years": 3,
        "payment_terms": "Net 30 Days",
        "tax_percentage": 18.0,
        "additional_charges": 0.0,
        "grand_total": 30680000.0,
    }

    is_valid, expected_total, anomalies = validate_quotation_math(quote_a)
    assert is_valid
    assert expected_total == 30680000.0
    assert len(anomalies) == 0
