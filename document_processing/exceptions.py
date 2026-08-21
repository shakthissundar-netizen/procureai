"""Custom exception hierarchy for ProcureAI Document Processing."""


class DocumentProcessingError(Exception):
    """Base exception for all document processing errors."""
    pass


class DocumentNotFoundError(DocumentProcessingError):
    """Raised when the specified document file does not exist."""
    pass


class CorruptedDocumentError(DocumentProcessingError):
    """Raised when a document is damaged, unreadable, or not a valid file format."""
    pass


class EmptyDocumentError(DocumentProcessingError):
    """Raised when a document has zero bytes or contains no pages/content."""
    pass


class UnsupportedFormatError(DocumentProcessingError):
    """Raised when a file format is not supported (e.g., unsupported extension)."""
    pass


class PasswordProtectedError(DocumentProcessingError):
    """Raised when a PDF or spreadsheet is encrypted / password-protected and cannot be read."""
    pass


class NormalizationError(DocumentProcessingError):
    """Raised when data cannot be coerced or normalized to standard schema."""
    pass
