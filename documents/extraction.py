import re
from io import BytesIO

from pypdf import PdfReader


def extract_invoice_fields(pdf_bytes):
    text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf_bytes)).pages)
    if not text.strip():
        raise ValueError("PDF contains no extractable text; scanned PDFs need OCR.")

    def find(pattern):
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else None

    fields = {
        "invoice_number": find(r"^\s*Invoice\s*(?:Number|No\.?|#)\s*[:#-]?\s*([A-Z0-9][A-Z0-9./-]*)\s*$"),
        "invoice_date": find(r"^\s*Invoice\s+Date\s*[:#-]?\s*(.{1,40}?)\s*$"),
        "total_amount": find(r"^\s*(?:Grand\s+)?(?:Total|Amount\s+Due)\s*[:#-]?\s*((?:(?:USD|PKR|Rs\.?|[$£€])\s*)?[0-9][0-9,]*(?:\.\d{2})?)\s*$"),
    }
    if not any(fields.values()):
        raise ValueError("No invoice fields found; check the PDF text and expected labels.")
    return fields
