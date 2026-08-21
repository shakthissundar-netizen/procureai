"""Integration tests for ProcureAI Document Processing, Normalization, and AI pipeline."""

import time
from pathlib import Path
from typing import Any, Dict

import pytest

from document_processing.normalizer import (
    check_rfq_compliance,
    normalize_quotation,
    validate_quotation_math,
)
from document_processing.pdf_parser import extract_text_from_pdf, parse_pdf
from document_processing.types import AnomalyType, QuotationDict


def test_ai_pipeline_integration(
    sample_raw_ai_outputs: Dict[str, Dict[str, Any]], standard_rfq: Dict[str, Any]
):
    """Test full integration from raw AI extraction output to normalized dict and anomaly report."""
    results = {}

    for vendor_key, raw_dict in sample_raw_ai_outputs.items():
        # 1. Normalize raw AI dictionary
        norm_quote = normalize_quotation(raw_dict)

        # 2. Validate mathematics
        is_math_valid, expected_total, math_anomalies = validate_quotation_math(norm_quote)

        # 3. Check RFQ compliance
        rfq_anomalies = check_rfq_compliance(norm_quote, standard_rfq)

        all_anomalies = math_anomalies + rfq_anomalies

        results[vendor_key] = {
            "quote": norm_quote,
            "is_math_valid": is_math_valid,
            "expected_total": expected_total,
            "anomalies": all_anomalies,
        }

    # Verify Vendor A
    res_a = results["vendor_a"]
    assert res_a["is_math_valid"] is True
    assert res_a["quote"]["unit_price"] == 52000.0
    assert len(res_a["anomalies"]) == 0

    # Verify Vendor B (Has critical anomalies)
    res_b = results["vendor_b"]
    assert res_b["is_math_valid"] is False
    assert any(a.anomaly_type == AnomalyType.GRAND_TOTAL_MISMATCH for a in res_b["anomalies"])
    assert any(a.anomaly_type == AnomalyType.DELIVERY_VIOLATION for a in res_b["anomalies"])

    # Verify Vendor C (Winning trade-off)
    res_c = results["vendor_c"]
    assert res_c["is_math_valid"] is True
    assert res_c["quote"]["unit_price"] == 49800.0
    assert res_c["quote"]["payment_terms"] == "Net 45 Days"
    assert len([a for a in res_c["anomalies"] if a.severity.value == "CRITICAL"]) == 0


def test_pdf_extraction_to_normalization_flow(demo_data_dir: Path, standard_rfq: Dict[str, Any]):
    """Test extracting real PDF text and passing simulated parsed output to normalizer."""
    pdf_path = demo_data_dir / "vendor_c_quotation.pdf"
    raw_text = extract_text_from_pdf(pdf_path)

    assert "NovaCore Technologies" in raw_text
    assert "49,800.00" in raw_text

    # Simulate extracted key-value pairs from the PDF text
    extracted_data = {
        "vendor_name": "NovaCore Technologies India",
        "quotation_number": "NC-2026-9942",
        "product_name": "ThinkSmart EliteBook 15 Gen 4",
        "quantity": 500,
        "unit_price": "₹49,800.00",
        "delivery_days": "12 Days",
        "warranty_years": "3 Years",
        "payment_terms": "Net 45 Days",
        "tax_percentage": "18.0%",
        "additional_charges": "0.00",
        "grand_total": "₹29,382,000.00",
    }

    norm = normalize_quotation(extracted_data)
    assert norm["quantity"] == 500
    assert norm["unit_price"] == 49800.0
    assert norm["grand_total"] == 29382000.0

    is_valid, exp_total, anomalies = validate_quotation_math(norm)
    assert is_valid
    assert exp_total == 29382000.0


def test_performance_benchmark(demo_data_dir: Path):
    """Ensure PDF & Excel extraction execute extremely quickly for hackathon iterations."""
    start_time = time.time()

    # Parse all 3 PDFs
    for name in ["vendor_a_quotation.pdf", "vendor_b_quotation.pdf", "vendor_c_quotation.pdf"]:
        res = parse_pdf(demo_data_dir / name)
        assert not res.is_empty

    elapsed = time.time() - start_time
    # Parsing 3 multi-page PDFs should easily complete in less than 1.0 second
    assert elapsed < 1.5, f"PDF extraction took too long: {elapsed:.2f}s"
