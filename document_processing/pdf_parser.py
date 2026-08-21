"""PDF parsing module for ProcureAI using PyMuPDF (fitz).

Extracts clean, structured text and metadata from single-page and multi-page PDFs,
with robust handling for empty, corrupt, and password-protected files.
"""

import io
import os
import re
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError as err:
        raise ImportError("PyMuPDF (fitz) is required for PDF parsing. Install with `pip install pymupdf`.") from err

from document_processing.exceptions import (
    CorruptedDocumentError,
    DocumentNotFoundError,
    DocumentProcessingError,
    EmptyDocumentError,
    PasswordProtectedError,
)
from document_processing.types import PDFPageContent, PDFParseResult


def _clean_extracted_text(raw_text: str) -> str:
    """Clean and normalize extracted PDF text.

    - Removes null bytes and control characters (except newline, tab).
    - Normalizes multiple spaces while keeping line structure.
    - Strips leading and trailing whitespace from lines.
    - Limits consecutive blank lines to at most one.
    """
    if not raw_text:
        return ""

    # Remove null bytes and non-printable control characters (keep \n, \t, \r)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw_text)

    # Normalize line endings to \n
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # Clean whitespace line by line
    lines = [line.strip() for line in cleaned.split("\n")]

    # Remove excessive blank lines (more than 1 consecutive blank line)
    normalized_lines: List[str] = []
    prev_blank = False
    for line in lines:
        if not line:
            if not prev_blank:
                normalized_lines.append("")
                prev_blank = True
        else:
            normalized_lines.append(line)
            prev_blank = False

    return "\n".join(normalized_lines).strip()


class PDFParser:
    """PyMuPDF-based parser for quotation PDF documents."""

    def __init__(self, include_page_delimiters: bool = True) -> None:
        """Initialize PDF parser.

        Args:
            include_page_delimiters: If True and document has >1 page, inserts
                "--- Page X ---" headers between pages in the combined text.
        """
        self.include_page_delimiters = include_page_delimiters

    def parse(
        self, source: Union[str, Path, bytes, BinaryIO], filename: Optional[str] = None
    ) -> PDFParseResult:
        """Parse a PDF document from a file path, raw bytes, or stream.

        Args:
            source: File path (str/Path), raw PDF bytes, or binary stream.
            filename: Optional filename hint for metadata/reporting.

        Returns:
            PDFParseResult containing extracted text, pages, and metadata.

        Raises:
            DocumentNotFoundError: If the specified file path does not exist.
            EmptyDocumentError: If the document is 0 bytes or contains 0 pages.
            PasswordProtectedError: If the PDF is encrypted with a password.
            CorruptedDocumentError: If the PDF is damaged or unreadable.
        """
        doc: Optional[fitz.Document] = None
        source_name = filename

        try:
            # 1. Handle file path input
            if isinstance(source, (str, Path)):
                file_path = Path(source)
                source_name = source_name or file_path.name
                if not file_path.exists():
                    raise DocumentNotFoundError(f"PDF file not found: {file_path}")

                file_size = file_path.stat().st_size
                if file_size == 0:
                    raise EmptyDocumentError(f"PDF file is empty (0 bytes): {file_path}")

                try:
                    doc = fitz.open(str(file_path))
                except Exception as ex:
                    raise CorruptedDocumentError(
                        f"Failed to open PDF '{file_path}': {str(ex)}"
                    ) from ex

            # 2. Handle raw bytes input
            elif isinstance(source, bytes):
                if len(source) == 0:
                    raise EmptyDocumentError("PDF byte stream is empty (0 bytes)")
                try:
                    doc = fitz.open(stream=source, filetype="pdf")
                except Exception as ex:
                    raise CorruptedDocumentError(
                        f"Failed to parse PDF bytes: {str(ex)}"
                    ) from ex

            # 3. Handle binary stream input
            elif hasattr(source, "read"):
                stream_data = source.read()
                if not stream_data:
                    raise EmptyDocumentError("PDF input stream is empty (0 bytes)")
                if isinstance(stream_data, str):
                    stream_data = stream_data.encode("latin-1")
                try:
                    doc = fitz.open(stream=stream_data, filetype="pdf")
                except Exception as ex:
                    raise CorruptedDocumentError(
                        f"Failed to parse PDF stream: {str(ex)}"
                    ) from ex
            else:
                raise DocumentProcessingError(f"Unsupported source type: {type(source)}")

            # 4. Check for encryption / password protection
            if doc.is_encrypted:
                if not doc.authenticate(""):
                    raise PasswordProtectedError(
                        f"PDF document '{source_name or 'source'}' is password-protected"
                    )

            # 5. Check page count
            page_count = len(doc)
            if page_count == 0:
                raise EmptyDocumentError(
                    f"PDF document '{source_name or 'source'}' contains 0 pages"
                )

            # 6. Extract text per page
            pages_content: List[PDFPageContent] = []
            combined_texts: List[str] = []

            for page_idx in range(page_count):
                page = doc[page_idx]
                raw_text = page.get_text("text") or ""
                cleaned = _clean_extracted_text(raw_text)

                words = len(cleaned.split()) if cleaned else 0
                chars = len(cleaned)

                page_content = PDFPageContent(
                    page_number=page_idx + 1,
                    text=cleaned,
                    char_count=chars,
                    word_count=words,
                )
                pages_content.append(page_content)

                if page_count > 1 and self.include_page_delimiters:
                    combined_texts.append(f"--- Page {page_idx + 1} ---\n{cleaned}")
                else:
                    combined_texts.append(cleaned)

            combined_text = "\n\n".join(t for t in combined_texts if t).strip()
            is_empty = len(combined_text.strip()) == 0

            # 7. Extract document metadata
            doc_metadata: Dict[str, Any] = {}
            if doc.metadata:
                doc_metadata = {
                    "title": doc.metadata.get("title") or "",
                    "author": doc.metadata.get("author") or "",
                    "subject": doc.metadata.get("subject") or "",
                    "creator": doc.metadata.get("creator") or "",
                    "producer": doc.metadata.get("producer") or "",
                    "creationDate": doc.metadata.get("creationDate") or "",
                }

            return PDFParseResult(
                text=combined_text,
                page_count=page_count,
                pages=pages_content,
                filename=source_name,
                metadata=doc_metadata,
                is_empty=is_empty,
            )

        finally:
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass


def extract_text_from_pdf(
    source: Union[str, Path, bytes, BinaryIO],
    include_delimiters: bool = True,
    filename: Optional[str] = None,
) -> str:
    """Convenience helper function to extract clean text from a PDF.

    Args:
        source: File path, raw PDF bytes, or binary stream.
        include_delimiters: If True and multi-page, includes page delimiters.
        filename: Optional filename hint.

    Returns:
        Clean combined text string extracted from the PDF.

    Raises:
        DocumentNotFoundError, EmptyDocumentError, CorruptedDocumentError, PasswordProtectedError.
    """
    parser = PDFParser(include_page_delimiters=include_delimiters)
    result = parser.parse(source, filename=filename)
    return result.text


def parse_pdf(
    source: Union[str, Path, bytes, BinaryIO],
    filename: Optional[str] = None,
) -> PDFParseResult:
    """Convenience helper function returning the complete PDFParseResult.

    Args:
        source: File path, raw PDF bytes, or binary stream.
        filename: Optional filename hint.

    Returns:
        PDFParseResult object with .text, .pages, .metadata, and .page_count.
    """
    parser = PDFParser()
    return parser.parse(source, filename=filename)
