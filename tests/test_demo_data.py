"""Verification tests for ProcureAI Demo Quotation Files and Procurement Scenario."""

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from document_processing.excel_parser import extract_data_from_excel, parse_excel
from document_processing.normalizer import (
    check_rfq_compliance,
    normalize_quotation,
    validate_quotation_math,
)
from document_processing.pdf_parser import extract_text_from_pdf, parse_pdf
from document_processing.types import AnomalyType, QuotationDict


def test_demo_files_exist_and_non_empty(demo_data_dir: Path):
    """Verify all 7 required demo quotation and specification files exist on disk."""
    expected_files = [
        "rfq_requirements.json",
        "vendor_a_quotation.pdf",
        "vendor_a_quotation.xlsx",
        "vendor_b_quotation.pdf",
        "vendor_b_quotation.xlsx",
        "vendor_c_quotation.pdf",
        "vendor_c_quotation.xlsx",
    ]

    for fname in expected_files:
        fpath = demo_data_dir / fname
        assert fpath.exists(), f"Missing required demo file: {fname}"
        assert fpath.stat().st_size > 0, f"Demo file is empty (0 bytes): {fname}"


def test_rfq_json_spec(demo_data_dir: Path):
    """Verify RFQ JSON specification matches requirements."""
    rfq_path = demo_data_dir / "rfq_requirements.json"
    with open(rfq_path, "r", encoding="utf-8") as f:
        rfq = json.load(f)

    assert rfq["quantity"] == 500
    assert rfq["target_unit_price"] == 50000.0
    assert rfq["max_delivery_days"] == 15
    assert rfq["min_warranty_years"] == 3
    assert "price" in rfq["scoring_weights"]


def test_vendor_a_pdf_and_excel(demo_data_dir: Path, standard_rfq: Dict[str, Any]):
    """Verify Vendor A (Apex Computech) PDF and Excel extraction and profile."""
    pdf_path = demo_data_dir / "vendor_a_quotation.pdf"
    excel_path = demo_data_dir / "vendor_a_quotation.xlsx"

    # PDF check
    pdf_res = parse_pdf(pdf_path)
    assert not pdf_res.is_empty
    assert "Apex Computech Solutions" in pdf_res.text
    assert "APX-2026-8801" in pdf_res.text
    assert "52,000" in pdf_res.text
    assert "10 Days" in pdf_res.text
    assert "3 Years" in pdf_res.text

    # Excel check
    excel_res = parse_excel(excel_path)
    assert not excel_res.is_empty
    assert "Apex Computech Solutions" in excel_res.text

    # Simulate normalized values
    quote_a: QuotationDict = {
        "vendor_name": "Apex Computech Solutions Ltd.",
        "quotation_number": "APX-2026-8801",
        "product_name": "Enterprise Business Laptop Pro 15",
        "quantity": 500,
        "unit_price": 52000.0,
        "delivery_days": 10,
        "warranty_years": 3,
        "payment_terms": "Net 30 Days",
        "tax_percentage": 18.0,
        "additional_charges": 0.0,
        "grand_total": 30680000.0,
    }

    # Math check
    is_valid, expected_total, math_anomalies = validate_quotation_math(quote_a)
    assert is_valid
    assert expected_total == 30680000.0
    assert len(math_anomalies) == 0

    # RFQ compliance
    rfq_anomalies = check_rfq_compliance(quote_a, standard_rfq)
    critical_violations = [a for a in rfq_anomalies if a.severity.value == "CRITICAL"]
    assert len(critical_violations) == 0  # Fully compliant with delivery & warranty


def test_vendor_b_pdf_and_excel_anomalies(demo_data_dir: Path, standard_rfq: Dict[str, Any]):
    """Verify Vendor B (BudgetByte) triggers delivery violation and grand total mismatch."""
    pdf_path = demo_data_dir / "vendor_b_quotation.pdf"
    excel_path = demo_data_dir / "vendor_b_quotation.xlsx"

    # PDF check
    pdf_res = parse_pdf(pdf_path)
    assert not pdf_res.is_empty
    assert "BudgetByte Infotech" in pdf_res.text
    assert "BB-QUO-2026-409" in pdf_res.text
    assert "48,500" in pdf_res.text
    assert "25 Days" in pdf_res.text
    assert "5 Years" in pdf_res.text

    # Excel check
    excel_res = parse_excel(excel_path)
    assert not excel_res.is_empty
    assert "BudgetByte Infotech" in excel_res.text

    # Normalized values
    quote_b: QuotationDict = {
        "vendor_name": "BudgetByte Infotech Pvt Ltd",
        "quotation_number": "BB-QUO-2026-409",
        "product_name": "BudgetBook Enterprise X500",
        "quantity": 500,
        "unit_price": 48500.0,
        "delivery_days": 25,
        "warranty_years": 5,
        "payment_terms": "Net 15 Days",
        "tax_percentage": 18.0,
        "additional_charges": 25000.0,
        "grand_total": 27500000.0,  # Deliberate mismatch
    }

    # Math anomaly check
    is_valid, expected_total, math_anomalies = validate_quotation_math(quote_b)
    assert not is_valid
    assert expected_total == 28640000.0  # 24.25M + 4.365M + 25k
    assert any(a.anomaly_type == AnomalyType.GRAND_TOTAL_MISMATCH for a in math_anomalies)

    # RFQ compliance check: triggers DELIVERY_VIOLATION
    rfq_anomalies = check_rfq_compliance(quote_b, standard_rfq)
    assert any(a.anomaly_type == AnomalyType.DELIVERY_VIOLATION for a in rfq_anomalies)
    assert any(a.anomaly_type == AnomalyType.ADDITIONAL_CHARGES_UNEXPECTED for a in rfq_anomalies)


def test_vendor_c_pdf_and_excel(demo_data_dir: Path, standard_rfq: Dict[str, Any]):
    """Verify Vendor C (NovaCore Technologies) represents the optimal overall trade-off."""
    pdf_path = demo_data_dir / "vendor_c_quotation.pdf"
    excel_path = demo_data_dir / "vendor_c_quotation.xlsx"

    # PDF check
    pdf_res = parse_pdf(pdf_path)
    assert not pdf_res.is_empty
    assert "NovaCore Technologies" in pdf_res.text
    assert "NC-2026-9942" in pdf_res.text
    assert "49,800" in pdf_res.text
    assert "12 Days" in pdf_res.text
    assert "3 Years" in pdf_res.text

    # Excel check
    excel_res = parse_excel(excel_path)
    assert not excel_res.is_empty
    assert "NovaCore Technologies" in excel_res.text

    # Normalized values
    quote_c: QuotationDict = {
        "vendor_name": "NovaCore Technologies India",
        "quotation_number": "NC-2026-9942",
        "product_name": "ThinkSmart EliteBook 15 Gen 4",
        "quantity": 500,
        "unit_price": 49800.0,
        "delivery_days": 12,
        "warranty_years": 3,
        "payment_terms": "Net 45 Days",
        "tax_percentage": 18.0,
        "additional_charges": 0.0,
        "grand_total": 29382000.0,
    }

    # Math check
    is_valid, expected_total, math_anomalies = validate_quotation_math(quote_c)
    assert is_valid
    assert expected_total == 29382000.0
    assert len(math_anomalies) == 0

    # RFQ compliance check
    rfq_anomalies = check_rfq_compliance(quote_c, standard_rfq)
    critical_violations = [a for a in rfq_anomalies if a.severity.value == "CRITICAL"]
    assert len(critical_violations) == 0

    # Check key winning trade-off metrics
    assert quote_c["unit_price"] < standard_rfq["target_unit_price"]  # Under target budget (49,800 < 50,000)
    assert quote_c["delivery_days"] <= standard_rfq["max_delivery_days"]  # Fast delivery (12 <= 15)
    assert quote_c["payment_terms"] == "Net 45 Days"  # Best cash flow terms
