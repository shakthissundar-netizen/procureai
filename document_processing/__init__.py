"""ProcureAI Document Processing Package.

Provides high-performance PDF & Excel extraction, data normalization,
and procurement anomaly detection.
"""

from document_processing.exceptions import (
    CorruptedDocumentError,
    DocumentNotFoundError,
    DocumentProcessingError,
    EmptyDocumentError,
    NormalizationError,
    PasswordProtectedError,
    UnsupportedFormatError,
)
from document_processing.excel_parser import (
    ExcelParser,
    extract_data_from_excel,
    extract_text_from_excel,
    parse_excel,
)
from document_processing.normalizer import (
    check_rfq_compliance,
    normalize_payment_terms,
    normalize_quotation,
    parse_currency_amount,
    parse_delivery_days,
    parse_quantity,
    parse_tax_percentage,
    parse_warranty_years,
    validate_quotation_math,
)
from document_processing.pdf_parser import (
    PDFParser,
    extract_text_from_pdf,
    parse_pdf,
)
from document_processing.types import (
    AnomalyReport,
    AnomalySeverity,
    AnomalyType,
    ExcelParseResult,
    PDFPageContent,
    PDFParseResult,
    QuotationDict,
)

__all__ = [
    # Types
    "QuotationDict",
    "AnomalyReport",
    "AnomalySeverity",
    "AnomalyType",
    "PDFParseResult",
    "PDFPageContent",
    "ExcelParseResult",
    # Parsers
    "PDFParser",
    "extract_text_from_pdf",
    "parse_pdf",
    "ExcelParser",
    "extract_data_from_excel",
    "extract_text_from_excel",
    "parse_excel",
    # Normalizer & Validation
    "normalize_quotation",
    "validate_quotation_math",
    "check_rfq_compliance",
    "parse_quantity",
    "parse_currency_amount",
    "parse_delivery_days",
    "parse_warranty_years",
    "parse_tax_percentage",
    "normalize_payment_terms",
    # Exceptions
    "DocumentProcessingError",
    "DocumentNotFoundError",
    "CorruptedDocumentError",
    "EmptyDocumentError",
    "UnsupportedFormatError",
    "PasswordProtectedError",
    "NormalizationError",
]
