"""Type definitions for ProcureAI Document Processing module."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict


class QuotationDict(TypedDict):
    """Standardized quotation data structure matching Master Specification Section 5."""
    vendor_name: str
    quotation_number: str
    product_name: str
    quantity: int
    unit_price: float
    delivery_days: int
    warranty_years: int
    payment_terms: str
    tax_percentage: float
    additional_charges: float
    grand_total: float


class AnomalySeverity(str, Enum):
    """Severity levels for detected procurement anomalies."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AnomalyType(str, Enum):
    """Classification types for procurement anomalies."""
    DELIVERY_VIOLATION = "DELIVERY_VIOLATION"
    WARRANTY_VIOLATION = "WARRANTY_VIOLATION"
    GRAND_TOTAL_MISMATCH = "GRAND_TOTAL_MISMATCH"
    TAX_INCONSISTENCY = "TAX_INCONSISTENCY"
    ADDITIONAL_CHARGES_UNEXPECTED = "ADDITIONAL_CHARGES_UNEXPECTED"
    MISSING_FIELDS = "MISSING_FIELDS"
    PRICE_OUTLIER = "PRICE_OUTLIER"
    INVALID_DATA = "INVALID_DATA"


@dataclass
class AnomalyReport:
    """Individual anomaly flag report."""
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    field: str
    message: str
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity.value,
            "field": self.field,
            "message": self.message,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
        }


@dataclass
class PDFPageContent:
    """Extracted text and structure for a single PDF page."""
    page_number: int  # 1-indexed
    text: str
    char_count: int
    word_count: int


@dataclass
class PDFParseResult:
    """Complete result object returned by PDF parser."""
    text: str
    page_count: int
    pages: List[PDFPageContent] = field(default_factory=list)
    filename: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_empty: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "page_count": self.page_count,
            "pages": [
                {
                    "page_number": p.page_number,
                    "text": p.text,
                    "char_count": p.char_count,
                    "word_count": p.word_count,
                }
                for p in self.pages
            ],
            "filename": self.filename,
            "metadata": self.metadata,
            "is_empty": self.is_empty,
        }


@dataclass
class ExcelParseResult:
    """Complete result object returned by Excel parser."""
    text: str
    sheet_names: List[str]
    raw_tables: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    filename: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_empty: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "sheet_names": self.sheet_names,
            "raw_tables": self.raw_tables,
            "filename": self.filename,
            "metadata": self.metadata,
            "is_empty": self.is_empty,
        }
