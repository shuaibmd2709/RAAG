import io
from pypdf import PdfReader


class ScannedPdfError(Exception):
    """PDF has no extractable text (probably a scan or photo)."""


def extract_text(pdf_bytes: bytes, min_chars_per_page: int = 40) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = [(p.extract_text() or "") for p in reader.pages]
    text = "\n".join(pages).strip()
    if len(text) < min_chars_per_page * max(len(pages), 1):
        raise ScannedPdfError(
            "No selectable text found. This looks like a scanned/image PDF; OCR is not supported yet."
        )
    return text