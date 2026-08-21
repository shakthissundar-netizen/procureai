"""Unit tests for Quotation Normalizer module."""

import pytest

from document_processing.normalizer import (
    normalize_payment_terms,
    normalize_quotation,
    parse_currency_amount,
    parse_delivery_days,
    parse_quantity,
    parse_tax_percentage,
    parse_warranty_years,
)


def test_parse_currency_amount():
    """Test parsing diverse currency string formats into float."""
    assert parse_currency_amount("₹ 52,000.00") == 52000.0
    assert parse_currency_amount("Rs. 48,500.50/-") == 48500.50
    assert parse_currency_amount("49800 INR") == 49800.0
    assert parse_currency_amount("$50,000") == 50000.0
    assert parse_currency_amount(52000) == 52000.0
    assert parse_currency_amount("Free") == 0.0
    assert parse_currency_amount("N/A") == 0.0
    assert parse_currency_amount(None, default=100.0) == 100.0


def test_parse_quantity():
    """Test parsing quantity strings into integers."""
    assert parse_quantity("500 units") == 500
    assert parse_quantity("500") == 500
    assert parse_quantity(500) == 500
    assert parse_quantity(500.0) == 500
    assert parse_quantity("invalid", default=10) == 10
    assert parse_quantity(None, default=0) == 0


def test_parse_delivery_days():
    """Test parsing delivery expressions into day counts."""
    assert parse_delivery_days(10) == 10
    assert parse_delivery_days("10 days") == 10
    assert parse_delivery_days("10 Days") == 10
    assert parse_delivery_days("25 business days") == 25
    assert parse_delivery_days("2 weeks") == 14
    assert parse_delivery_days("1 month") == 30
    assert parse_delivery_days("10-15 days") == 15  # Upper bound
    assert parse_delivery_days("within 12 days") == 12
    assert parse_delivery_days(None, default=0) == 0


def test_parse_warranty_years():
    """Test parsing warranty duration into year counts."""
    assert parse_warranty_years(3) == 3
    assert parse_warranty_years("3 years") == 3
    assert parse_warranty_years("3 yrs") == 3
    assert parse_warranty_years("36 months") == 3
    assert parse_warranty_years("60 months") == 5
    assert parse_warranty_years("5 Years Onsite") == 5
    assert parse_warranty_years("24 mos") == 2
    assert parse_warranty_years(None, default=0) == 0


def test_parse_tax_percentage():
    """Test parsing tax percentage representations."""
    assert parse_tax_percentage(18) == 18.0
    assert parse_tax_percentage("18%") == 18.0
    assert parse_tax_percentage("18.0%") == 18.0
    assert parse_tax_percentage(0.18) == 18.0  # Decimal ratio
    assert parse_tax_percentage("0") == 0.0
    assert parse_tax_percentage(None) == 0.0


def test_normalize_payment_terms():
    """Test standardizing payment terms."""
    assert normalize_payment_terms("30-day payment") == "Net 30 Days"
    assert normalize_payment_terms("Net 30") == "Net 30 Days"
    assert normalize_payment_terms("15-day payment") == "Net 15 Days"
    assert normalize_payment_terms("45 days credit") == "Net 45 Days"
    assert normalize_payment_terms("100% advance") == "100% Advance"
    assert normalize_payment_terms("Immediate on delivery") == "Payment on Delivery"
    assert normalize_payment_terms("Custom 90 Days") == "Custom 90 Days"
    assert normalize_payment_terms(None) == ""


def test_normalize_quotation_full():
    """Test full quotation normalization from heterogeneous dictionary."""
    raw = {
        "Vendor Name": "  Apex Computech Solutions Ltd.  ",
        "Quote_No": "APX-2026-8801",
        "Item_Description": "Enterprise Laptop Pro 15",
        "Qty": "500 units",
        "Unit_Price": "₹ 52,000.00",
        "Lead_Time": "10 days",
        "Warranty_Period": "36 months",
        "Payment_Term": "30 days",
        "GST_Rate": "18%",
        "Shipping_Charges": "0",
        "Total_Amount": "₹ 30,680,000.00",
    }

    norm = normalize_quotation(raw)
    assert norm["vendor_name"] == "Apex Computech Solutions Ltd."
    assert norm["quotation_number"] == "APX-2026-8801"
    assert norm["product_name"] == "Enterprise Laptop Pro 15"
    assert norm["quantity"] == 500
    assert norm["unit_price"] == 52000.0
    assert norm["delivery_days"] == 10
    assert norm["warranty_years"] == 3
    assert norm["payment_terms"] == "Net 30 Days"
    assert norm["tax_percentage"] == 18.0
    assert norm["additional_charges"] == 0.0
    assert norm["grand_total"] == 30680000.0


def test_normalize_quotation_missing_fields():
    """Test normalizing quotation when some fields are missing or None."""
    raw = {
        "vendor": "Partial Vendor",
        "unit_price": "25000",
    }
    norm = normalize_quotation(raw)
    assert norm["vendor_name"] == "Partial Vendor"
    assert norm["unit_price"] == 25000.0
    assert norm["quantity"] == 0
    assert norm["delivery_days"] == 0
    assert norm["warranty_years"] == 0
    assert norm["payment_terms"] == ""
    assert norm["tax_percentage"] == 0.0
    assert norm["additional_charges"] == 0.0
    assert norm["grand_total"] == 0.0


def test_normalize_empty_input():
    """Test normalizing empty dictionary or non-dict input."""
    norm = normalize_quotation({})
    assert norm["vendor_name"] == ""
    assert norm["quantity"] == 0
    assert norm["grand_total"] == 0.0
