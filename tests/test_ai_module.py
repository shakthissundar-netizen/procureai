"""
Unit and Integration Tests for ProcureAI AI Module.
"""

import os
import unittest
from typing import Dict, Any

from ai.config import DEFAULT_WEIGHTS
from ai.validation import QuotationSchema, validate_quotation_data
from ai.extraction import (
    parse_llm_json,
    clean_json_response,
    extract_text_from_pdf,
    extract_quotation_data,
)
from ai.matching import match_quotation_requirements
from ai.anomaly import detect_anomalies
from ai.scoring import calculate_vendor_scores
from ai.explanation import generate_decision_explanation, generate_fallback_explanation


class TestProcureAIAIModule(unittest.TestCase):

    def setUp(self):
        self.rfq_requirements = {
            "max_delivery_days": 15,
            "min_warranty_years": 3.0,
            "target_unit_price": 50000.0,
            "required_quantity": 500,
            "required_product_specs": ["Intel i7", "16 GB RAM", "512 GB SSD"],
        }

        # Demo Vendors from Spec (Section 11)
        self.vendor_a = {
            "vendor_name": "Vendor A",
            "quotation_number": "QUO-A-101",
            "product_name": "Business Laptop i7 16GB 512GB SSD",
            "quantity": 500,
            "unit_price": 52000.0,
            "delivery_days": 10,
            "warranty_years": 3.0,
            "payment_terms": "Net 30 days",
            "tax_percentage": 18.0,
            "additional_charges": 0.0,
            "grand_total": 30680000.0,  # 500*52000*1.18 = 30,680,000
        }

        self.vendor_b = {
            "vendor_name": "Vendor B",
            "quotation_number": "QUO-B-202",
            "product_name": "Business Laptop i7 16GB 512GB SSD",
            "quantity": 500,
            "unit_price": 48500.0,
            "delivery_days": 25,  # Exceeds max 15 days
            "warranty_years": 5.0,
            "payment_terms": "Net 15 days",
            "tax_percentage": 18.0,
            "additional_charges": 0.0,
            "grand_total": 25000000.0,  # Deliberate mismatch: expected is 28,615,000
        }

        self.vendor_c = {
            "vendor_name": "Vendor C",
            "quotation_number": "QUO-C-303",
            "product_name": "Business Laptop i7 16GB 512GB SSD",
            "quantity": 500,
            "unit_price": 49800.0,
            "delivery_days": 12,
            "warranty_years": 3.0,
            "payment_terms": "Net 45 days",
            "tax_percentage": 18.0,
            "additional_charges": 0.0,
            "grand_total": 29382000.0,  # 500*49800*1.18 = 29,382,000
        }

    # 1. Extraction & Cleaning Tests
    def test_clean_json_response_markdown(self):
        raw = "Here is the extracted json:\n```json\n{\"vendor_name\": \"Acme Corp\", \"unit_price\": 100}\n```"
        cleaned = clean_json_response(raw)
        self.assertEqual(cleaned, '{"vendor_name": "Acme Corp", "unit_price": 100}')

    def test_parse_llm_json_malformed(self):
        malformed = "{\"vendor_name\": \"Acme Corp\", \"unit_price\": 100,}"
        data = parse_llm_json(malformed)
        self.assertEqual(data.get("vendor_name"), "Acme Corp")
        self.assertEqual(data.get("unit_price"), 100)

    # 2. Pydantic Validation Tests
    def test_validation_success(self):
        is_valid, schema_obj, errors = validate_quotation_data(self.vendor_a)
        self.assertTrue(is_valid)
        self.assertIsNotNone(schema_obj)
        self.assertEqual(len(errors), 0)
        self.assertEqual(schema_obj.vendor_name, "Vendor A")

    def test_validation_invalid_numeric(self):
        invalid_data = self.vendor_a.copy()
        invalid_data["unit_price"] = -500.0
        is_valid, schema_obj, errors = validate_quotation_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertTrue(any("Unit price must be greater than zero" in err or "greater than or equal to 0" in err for err in errors))

    # 3. Requirement Matching Tests
    def test_requirement_matching_vendor_a(self):
        matches = match_quotation_requirements(self.vendor_a, self.rfq_requirements)
        deliv_match = next(m for m in matches if m["requirement"] == "Maximum delivery")
        self.assertTrue(deliv_match["passed"])

    def test_requirement_matching_vendor_b_failed_delivery(self):
        matches = match_quotation_requirements(self.vendor_b, self.rfq_requirements)
        deliv_match = next(m for m in matches if m["requirement"] == "Maximum delivery")
        self.assertFalse(deliv_match["passed"])
        self.assertIn("exceeds delivery requirement", deliv_match["explanation"])

    # 4. Anomaly Detection Tests
    def test_anomaly_detection_delivery_violation(self):
        anomalies = detect_anomalies(self.vendor_b, self.rfq_requirements)
        types = [a["anomaly_type"] for a in anomalies]
        self.assertIn("DELIVERY_VIOLATION", types)

    def test_anomaly_detection_total_mismatch(self):
        anomalies = detect_anomalies(self.vendor_b, self.rfq_requirements)
        mismatch_anomaly = next((a for a in anomalies if a["anomaly_type"] == "PRICE_TOTAL_MISMATCH"), None)
        self.assertIsNotNone(mismatch_anomaly)
        self.assertEqual(mismatch_anomaly["severity"], "CRITICAL")
        self.assertIn("Discrepancy", mismatch_anomaly["message"])

    def test_anomaly_detection_warranty_violation(self):
        low_warranty_vendor = self.vendor_a.copy()
        low_warranty_vendor["warranty_years"] = 1.0
        anomalies = detect_anomalies(low_warranty_vendor, self.rfq_requirements)
        types = [a["anomaly_type"] for a in anomalies]
        self.assertIn("WARRANTY_VIOLATION", types)

    # 5. Deterministic Vendor Scoring Tests
    def test_vendor_scoring_ranks(self):
        items = [
            {"quotation": self.vendor_a, "anomalies": detect_anomalies(self.vendor_a, self.rfq_requirements)},
            {"quotation": self.vendor_b, "anomalies": detect_anomalies(self.vendor_b, self.rfq_requirements)},
            {"quotation": self.vendor_c, "anomalies": detect_anomalies(self.vendor_c, self.rfq_requirements)},
        ]

        scored = calculate_vendor_scores(items, self.rfq_requirements)
        self.assertEqual(len(scored), 3)

        winner = scored[0]
        # Vendor C should win with default weights
        self.assertEqual(winner["vendor_name"], "Vendor C")
        self.assertEqual(winner["rank"], 1)

        # Vendor B has critical anomalies so compliance is penalised
        b_score = next(v for v in scored if v["vendor_name"] == "Vendor B")
        self.assertLess(b_score["final_score"], winner["final_score"])

    # 6. Dynamic Weight Changes (What-If Analysis)
    def test_weight_changes_ranking_shift(self):
        items = [
            {"quotation": self.vendor_a, "anomalies": detect_anomalies(self.vendor_a, self.rfq_requirements)},
            {"quotation": self.vendor_b, "anomalies": detect_anomalies(self.vendor_b, self.rfq_requirements)},
            {"quotation": self.vendor_c, "anomalies": detect_anomalies(self.vendor_c, self.rfq_requirements)},
        ]

        # Shift weights aggressively to Price (75%)
        custom_weights = {
            "price": 0.75,
            "delivery": 0.05,
            "quality": 0.05,
            "warranty": 0.05,
            "payment": 0.05,
            "compliance": 0.05,
        }

        scored = calculate_vendor_scores(items, self.rfq_requirements, weights=custom_weights)
        # Verify ranking shifted or scores recalculated dynamically
        b_score = next(v for v in scored if v["vendor_name"] == "Vendor B")
        self.assertGreater(b_score["component_scores"]["price"], 95.0)

    # 7. Explanation Generator Tests
    def test_explanation_fallback(self):
        ranked = [
            {"vendor_name": "Vendor C", "final_score": 91.05, "component_scores": {"price": 97, "delivery": 83, "quality": 100}},
            {"vendor_name": "Vendor A", "final_score": 90.65, "component_scores": {"price": 93, "delivery": 100, "quality": 100}},
        ]
        anomalies = {"Vendor C": [], "Vendor A": []}
        exp = generate_fallback_explanation(ranked, anomalies)
        self.assertIn("Vendor C", exp["recommendation_explanation"])
        self.assertGreaterEqual(len(exp["key_reasons"]), 1)

    # 8. Real PDF Extraction Test (if demo file exists)
    def test_pdf_text_extraction(self):
        pdf_path = "demo_data/vendor_b_quotation.pdf"
        if os.path.exists(pdf_path):
            text = extract_text_from_pdf(pdf_path)
            self.assertTrue(len(text) > 0)
            self.assertIn("Quotation", text)


if __name__ == "__main__":
    unittest.main()
