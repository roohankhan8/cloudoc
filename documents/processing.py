import logging
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from .extraction import extract_invoice_fields
from .models import Document
from .storage import read_document

logger = logging.getLogger(__name__)


def process_document(document_id, attempts=1):
    document = Document.objects.filter(pk=document_id).first()
    if document is None or document.status in (Document.Status.PROCESSED, Document.Status.FAILED):
        return True

    Document.objects.filter(pk=document.pk).update(
        status=Document.Status.PROCESSING,
        processing_attempts=attempts,
        updated_at=timezone.now(),
    )
    try:
        if Path(document.original_filename).suffix.lower() != ".pdf":
            raise ValueError("Invoice extraction currently supports PDF files only.")
        extracted_data = extract_invoice_fields(read_document(document.object_key))
    except Exception as exc:
        is_final_attempt = attempts >= settings.SQS_MAX_RECEIVE_COUNT
        Document.objects.filter(pk=document.pk).update(
            status=Document.Status.FAILED if is_final_attempt else Document.Status.PENDING,
            processing_attempts=attempts,
            last_error=str(exc)[:4000],
            updated_at=timezone.now(),
        )
        logger.exception("Document %s processing attempt %s failed.", document_id, attempts)
        return False

    Document.objects.filter(pk=document.pk).update(
        status=Document.Status.PROCESSED,
        processing_attempts=attempts,
        last_error="",
        extracted_data=extracted_data,
        updated_at=timezone.now(),
    )
    logger.info("Processed document %s: %s", document_id, extracted_data)
    return True
