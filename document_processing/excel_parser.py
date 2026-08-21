"""Excel spreadsheet parsing module for ProcureAI using openpyxl and pandas.

Extracts tabular and key-value quotation data from .xlsx / .xls files,
formats spreadsheets into structured representations and clean text suitable for AI extraction.
"""

import io
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

import pandas as pd
import openpyxl

from document_processing.exceptions import (
    CorruptedDocumentError,
    DocumentNotFoundError,
    DocumentProcessingError,
    EmptyDocumentError,
    PasswordProtectedError,
    UnsupportedFormatError,
)
from document_processing.types import ExcelParseResult


def _clean_cell_value(val: Any) -> Any:
    """Clean cell value for consistent representation."""
    if val is None:
        return ""
    if isinstance(val, float) and pd.isna(val):
        return ""
    if isinstance(val, str):
        return val.strip()
    return val


class ExcelParser:
    """Parser for quotation Excel (.xlsx / .xls) spreadsheets."""

    def __init__(self, max_empty_rows_threshold: int = 100) -> None:
        self.max_empty_rows_threshold = max_empty_rows_threshold

    def parse(
        self, source: Union[str, Path, bytes, BinaryIO], filename: Optional[str] = None
    ) -> ExcelParseResult:
        """Parse an Excel workbook from file path, raw bytes, or stream.

        Args:
            source: File path (str/Path), raw bytes, or binary stream.
            filename: Optional filename hint.

        Returns:
            ExcelParseResult containing text representation, sheet names, raw tables, and metadata.

        Raises:
            DocumentNotFoundError: If the file does not exist.
            EmptyDocumentError: If the workbook or all sheets are empty.
            CorruptedDocumentError: If the file is not a valid Excel file.
            PasswordProtectedError: If the workbook is password protected.
        """
        source_name = filename
        excel_bytes: Optional[bytes] = None

        # 1. Resolve source to bytes / path
        if isinstance(source, (str, Path)):
            file_path = Path(source)
            source_name = source_name or file_path.name
            if not file_path.exists():
                raise DocumentNotFoundError(f"Excel file not found: {file_path}")

            suffix = file_path.suffix.lower()
            if suffix not in (".xlsx", ".xlsm", ".xltx", ".xltm", ".xls"):
                raise UnsupportedFormatError(f"Unsupported spreadsheet extension '{suffix}' in {file_path}")

            if file_path.stat().st_size == 0:
                raise EmptyDocumentError(f"Excel file is empty (0 bytes): {file_path}")

            try:
                with open(file_path, "rb") as f:
                    excel_bytes = f.read()
            except Exception as ex:
                raise CorruptedDocumentError(f"Failed to read file '{file_path}': {str(ex)}") from ex

        elif isinstance(source, bytes):
            if len(source) == 0:
                raise EmptyDocumentError("Excel byte stream is empty (0 bytes)")
            excel_bytes = source

        elif hasattr(source, "read"):
            data = source.read()
            if not data:
                raise EmptyDocumentError("Excel input stream is empty (0 bytes)")
            if isinstance(data, str):
                data = data.encode("utf-8")
            excel_bytes = data
        else:
            raise DocumentProcessingError(f"Unsupported source type: {type(source)}")

        # 2. Read with openpyxl and pandas
        stream = io.BytesIO(excel_bytes)

        try:
            # Check openpyxl loading first for validation / encryption detection
            wb = openpyxl.load_workbook(stream, data_only=True)
            sheet_names = wb.sheetnames
        except openpyxl.utils.exceptions.InvalidFileException as ex:
            raise CorruptedDocumentError(f"Invalid Excel format or corrupted workbook: {str(ex)}") from ex
        except Exception as ex:
            err_msg = str(ex).lower()
            if "encrypted" in err_msg or "password" in err_msg:
                raise PasswordProtectedError(f"Excel workbook is password protected: {str(ex)}") from ex
            raise CorruptedDocumentError(f"Failed to open Excel workbook: {str(ex)}") from ex

        if not sheet_names:
            raise EmptyDocumentError("Excel workbook contains no sheets")

        # 3. Process each sheet using pandas and openpyxl
        raw_tables: Dict[str, List[Dict[str, Any]]] = {}
        sheet_text_blocks: List[str] = []
        has_any_data = False

        stream.seek(0)
        excel_file = pd.ExcelFile(stream, engine="openpyxl")

        for sheet_name in sheet_names:
            sheet_ws = wb[sheet_name]
            # Extract raw cell rows to preserve header metadata / key-value forms
            row_values: List[List[Any]] = []
            for row in sheet_ws.iter_rows(values_only=True):
                cleaned_row = [_clean_cell_value(c) for c in row]
                if any(str(c).strip() != "" for c in cleaned_row):
                    row_values.append(cleaned_row)

            if not row_values:
                continue

            has_any_data = True

            # Format sheet text representation
            sheet_lines: List[str] = [f"=== Sheet: {sheet_name} ==="]

            for row in row_values:
                # Filter trailing empty strings
                while row and str(row[-1]).strip() == "":
                    row.pop()
                if row:
                    # Key-value detection (e.g. 2 non-empty items or labeled pairs)
                    line_str = " | ".join(str(c) for c in row if str(c).strip() != "")
                    sheet_lines.append(line_str)

            sheet_text_blocks.append("\n".join(sheet_lines))

            # Also read structured table with pandas
            try:
                df = excel_file.parse(sheet_name)
                df = df.dropna(how="all")
                # Fill NaN with empty string
                df = df.fillna("")
                records = df.to_dict(orient="records")
                raw_tables[sheet_name] = records
            except Exception:
                raw_tables[sheet_name] = []

        if not has_any_data:
            raise EmptyDocumentError("All sheets in Excel workbook are empty")

        combined_text = "\n\n".join(sheet_text_blocks).strip()

        return ExcelParseResult(
            text=combined_text,
            sheet_names=sheet_names,
            raw_tables=raw_tables,
            filename=source_name,
            metadata={"total_sheets": len(sheet_names)},
            is_empty=len(combined_text.strip()) == 0,
        )


def extract_data_from_excel(
    source: Union[str, Path, bytes, BinaryIO],
    filename: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience helper function extracting structured data and text from Excel.

    Args:
        source: File path, raw bytes, or stream.
        filename: Optional filename hint.

    Returns:
        Dictionary representation of ExcelParseResult.
    """
    parser = ExcelParser()
    result = parser.parse(source, filename=filename)
    return result.to_dict()


def extract_text_from_excel(
    source: Union[str, Path, bytes, BinaryIO],
    filename: Optional[str] = None,
) -> str:
    """Convenience helper function returning clean text formatted from Excel sheets.

    Args:
        source: File path, raw bytes, or stream.
        filename: Optional filename hint.

    Returns:
        Formatted text representation of the spreadsheet content.
    """
    parser = ExcelParser()
    result = parser.parse(source, filename=filename)
    return result.text


def parse_excel(
    source: Union[str, Path, bytes, BinaryIO],
    filename: Optional[str] = None,
) -> ExcelParseResult:
    """Convenience helper function returning the complete ExcelParseResult object."""
    parser = ExcelParser()
    return parser.parse(source, filename=filename)
