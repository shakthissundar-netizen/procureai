"""
Validation module for extracted quotation data using Pydantic.
"""

from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseModel, Field, ValidationError, field_validator


class QuotationSchema(BaseModel):
    vendor_name: str = Field(..., description="Name of the vendor issuing the quotation")
    quotation_number: str = Field(..., description="Quotation reference or invoice number")
    product_name: str = Field(..., description="Name or description of the product/service")
    quantity: int = Field(..., ge=0, description="Quantity offered")
    unit_price: float = Field(..., ge=0.0, description="Price per unit in local currency")
    delivery_days: int = Field(..., ge=0, description="Estimated delivery time in days")
    warranty_years: float = Field(..., ge=0.0, description="Warranty duration in years")
    payment_terms: str = Field(..., description="Payment terms description (e.g. Net 30, 30 days)")
    tax_percentage: float = Field(..., ge=0.0, le=100.0, description="Applicable tax/GST percentage")
    additional_charges: float = Field(..., ge=0.0, description="Any shipping, handling, or extra fees")
    grand_total: float = Field(..., ge=0.0, description="Total quoted price including taxes and charges")

    @field_validator("vendor_name", "product_name", "quotation_number", "payment_terms", mode="before")
    @classmethod
    def sanitize_strings(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v).strip()

    @field_validator("quantity", "delivery_days", mode="before")
    @classmethod
    def parse_int_fields(cls, v: Any) -> int:
        if v is None or v == "":
            return 0
        if isinstance(v, (int, float)):
            return max(0, int(v))
        try:
            cleaned = "".join([c for c in str(v) if c.isdigit()])
            return int(cleaned) if cleaned else 0
        except Exception:
            return 0

    @field_validator("unit_price", "warranty_years", "tax_percentage", "additional_charges", "grand_total", mode="before")
    @classmethod
    def parse_float_fields(cls, v: Any) -> float:
        if v is None or v == "":
            return 0.0
        if isinstance(v, (int, float)):
            return max(0.0, float(v))
        try:
            cleaned = str(v).replace(",", "").replace("₹", "").replace("$", "").replace("%", "").strip()
            val = float(cleaned)
            return max(0.0, val)
        except Exception:
            return 0.0


def validate_quotation_data(data: Dict[str, Any]) -> Tuple[bool, Optional[QuotationSchema], List[str]]:
    """
    Validates dictionary against QuotationSchema.
    
    Returns:
        (is_valid: bool, validated_schema: Optional[QuotationSchema], errors: List[str])
    """
    errors: List[str] = []
    if not isinstance(data, dict):
        return False, None, ["Input quotation data must be a dictionary"]

    try:
        schema_obj = QuotationSchema(**data)
        
        # Additional domain validation checks
        if not schema_obj.vendor_name:
            errors.append("Vendor name is empty or missing")
        if schema_obj.quantity <= 0:
            errors.append("Quantity must be greater than zero")
        if schema_obj.unit_price <= 0:
            errors.append("Unit price must be greater than zero")
        if schema_obj.delivery_days > 365:
            errors.append(f"Delivery timeframe ({schema_obj.delivery_days} days) exceeds 1 year")
        if schema_obj.warranty_years > 30:
            errors.append(f"Warranty period ({schema_obj.warranty_years} years) is suspiciously long")

        is_valid = len(errors) == 0
        return is_valid, schema_obj, errors

    except ValidationError as ve:
        for err in ve.errors():
            field = " -> ".join([str(loc) for loc in err["loc"]])
            msg = err["msg"]
            errors.append(f"Field '{field}': {msg}")
        return False, None, errors
    except Exception as e:
        return False, None, [f"Unexpected validation error: {str(e)}"]
