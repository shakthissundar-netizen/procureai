"""Unit tests for Excel Parser module."""

import io
from pathlib import Path

import openpyxl
import pytest

from document_processing.exceptions import (
    CorruptedDocumentError,
    DocumentNotFoundError,
    EmptyDocumentError,
    UnsupportedFormatError,
)
from document_processing.excel_parser import (
    ExcelParser,
    extract_data_from_excel,
    extract_text_from_excel,
    parse_excel,
)


def test_excel_extract_standard_sheet(sample_excel_bytes: bytes):
    """Test extracting text and table data from single-sheet Excel workbook."""
    result = parse_excel(sample_excel_bytes, filename="quote.xlsx")
    assert result.sheet_names == ["Quote"]
    assert "Apex Computech Solutions" in result.text
    assert "APX-8801" in result.text
    assert "Business Laptop" in result.text
    assert not result.is_empty


def test_excel_extract_multi_sheet(multi_sheet_excel_bytes: bytes):
    """Test extracting multi-sheet Excel workbook."""
    result = parse_excel(multi_sheet_excel_bytes)
    assert len(result.sheet_names) == 2
    assert "Overview" in result.sheet_names
    assert "Financials" in result.sheet_names
    assert "NovaCore Technologies" in result.text
    assert "29382000" in result.text


def test_excel_data_dict_format(sample_excel_bytes: bytes):
    """Test extract_data_from_excel returns dictionary with raw tables."""
    data = extract_data_from_excel(sample_excel_bytes, filename="vendor.xlsx")
    assert "sheet_names" in data
    assert "text" in data
    assert "raw_tables" in data
    assert "Quote" in data["raw_tables"]
    assert len(data["raw_tables"]["Quote"]) > 0


def test_excel_corrupted_bytes(corrupted_excel_bytes: bytes):
    """Test corrupted Excel bytes raise CorruptedDocumentError."""
    with pytest.raises(CorruptedDocumentError):
        parse_excel(corrupted_excel_bytes)


def test_excel_empty_bytes():
    """Test empty bytes raise EmptyDocumentError."""
    with pytest.raises(EmptyDocumentError):
        parse_excel(b"")


def test_excel_non_existent_file(tmp_path: Path):
    """Test non-existent file raises DocumentNotFoundError."""
    missing = tmp_path / "missing.xlsx"
    with pytest.raises(DocumentNotFoundError):
        parse_excel(missing)


def test_excel_zero_byte_file(tmp_path: Path):
    """Test 0-byte file raises EmptyDocumentError."""
    zero_file = tmp_path / "empty.xlsx"
    zero_file.write_bytes(b"")
    with pytest.raises(EmptyDocumentError):
        parse_excel(zero_file)


def test_excel_unsupported_format(tmp_path: Path):
    """Test unsupported file extension raises UnsupportedFormatError."""
    txt_file = tmp_path / "quote.txt"
    txt_file.write_text("Hello world")
    with pytest.raises(UnsupportedFormatError):
        parse_excel(txt_file)


def test_excel_stream_input(sample_excel_bytes: bytes):
    """Test parsing from an io.BytesIO stream."""
    stream = io.BytesIO(sample_excel_bytes)
    result = parse_excel(stream, filename="stream_quote.xlsx")
    assert "Apex Computech Solutions" in result.text
    assert result.metadata["total_sheets"] == 1


def test_excel_empty_sheets():
    """Test Excel file with only empty sheet raises EmptyDocumentError."""
    wb = openpyxl.Workbook()
    # default sheet is empty
    buf = io.BytesIO()
    wb.save(buf)
    with pytest.raises(EmptyDocumentError):
        parse_excel(buf.getvalue())
