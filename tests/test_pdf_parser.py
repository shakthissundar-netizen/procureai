"""Unit tests for PDF Parser module."""

import io
from pathlib import Path

import pytest

from document_processing.exceptions import (
    CorruptedDocumentError,
    DocumentNotFoundError,
    EmptyDocumentError,
)
from document_processing.pdf_parser import (
    PDFParser,
    _clean_extracted_text,
    extract_text_from_pdf,
    parse_pdf,
)


def test_pdf_extract_single_page(single_page_pdf_bytes: bytes):
    """Test extracting text from single page PDF in memory."""
    text = extract_text_from_pdf(single_page_pdf_bytes)
    assert "VENDOR QUOTATION" in text
    assert "Acme Tech Solutions" in text
    assert "ACM-1001" in text
    assert "Rs. 50,000" in text


def test_pdf_extract_multi_page(multi_page_pdf_bytes: bytes):
    """Test multi-page PDF extraction preserving all pages and delimiters."""
    result = parse_pdf(multi_page_pdf_bytes)
    assert result.page_count == 3
    assert len(result.pages) == 3
    assert "--- Page 1 ---" in result.text
    assert "--- Page 2 ---" in result.text
    assert "--- Page 3 ---" in result.text
    assert "Section 1: Quotation Part 1" in result.text
    assert "Commercial Grand Total: Rs. 25,000,000" in result.text
    assert not result.is_empty


def test_pdf_parse_result_structure(single_page_pdf_bytes: bytes):
    """Test structured attributes of PDFParseResult."""
    result = parse_pdf(single_page_pdf_bytes, filename="test_quote.pdf")
    assert result.filename == "test_quote.pdf"
    assert result.page_count == 1
    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert result.pages[0].char_count > 0
    assert result.pages[0].word_count > 0

    d = result.to_dict()
    assert d["filename"] == "test_quote.pdf"
    assert d["page_count"] == 1
    assert len(d["pages"]) == 1


def test_pdf_corrupted_bytes(corrupted_pdf_bytes: bytes):
    """Test corrupted PDF bytes raise CorruptedDocumentError."""
    with pytest.raises(CorruptedDocumentError):
        parse_pdf(corrupted_pdf_bytes)


def test_pdf_empty_bytes():
    """Test empty bytes raise EmptyDocumentError."""
    with pytest.raises(EmptyDocumentError):
        parse_pdf(b"")


def test_pdf_non_existent_file(tmp_path: Path):
    """Test non-existent file path raises DocumentNotFoundError."""
    missing_file = tmp_path / "non_existent_quote.pdf"
    with pytest.raises(DocumentNotFoundError):
        parse_pdf(missing_file)


def test_pdf_zero_byte_file(tmp_path: Path):
    """Test zero-byte physical file raises EmptyDocumentError."""
    zero_file = tmp_path / "empty.pdf"
    zero_file.write_bytes(b"")
    with pytest.raises(EmptyDocumentError):
        parse_pdf(zero_file)


def test_pdf_stream_input(single_page_pdf_bytes: bytes):
    """Test parsing from an io.BytesIO stream."""
    stream = io.BytesIO(single_page_pdf_bytes)
    result = parse_pdf(stream, filename="stream_quote.pdf")
    assert result.page_count == 1
    assert "Acme Tech Solutions" in result.text


def test_pdf_blank_page(empty_page_pdf_bytes: bytes):
    """Test PDF with blank page is marked as is_empty=True."""
    result = parse_pdf(empty_page_pdf_bytes)
    assert result.page_count == 1
    assert result.is_empty is True
    assert result.text == ""


def test_text_cleaner_utility():
    """Test _clean_extracted_text cleans whitespace and control characters."""
    raw = "  Line 1   \r\n\r\n\r\n\r\n  Line 2   with   spaces  \x00\x07\n\n  Line 3  "
    cleaned = _clean_extracted_text(raw)
    assert "\x00" not in cleaned
    assert "\x07" not in cleaned
    assert "Line 1" in cleaned
    assert "Line 2   with   spaces" in cleaned
    assert "Line 3" in cleaned
