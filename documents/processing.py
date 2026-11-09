import logging
import time
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from .extraction import extract_invoice_fields
from .models import Document
from .storage import read_document

logger = logging.getLogger(__name__)


def process_document(document_id, attempts=1, message_id=None):
    started = time.perf_counter()
    log_context = {"event": "document_processing", "document_id": str(document_id), "message_id": message_id, "attempts": attempts}
    document = Document.objects.filter(pk=document_id).first()
    if document is None or document.status in (Document.Status.PROCESSED, Document.Status.FAILED):
        logger.info("Document processing skipped", extra={**log_context, "outcome": "skipped", "duration_ms": round((time.perf_counter() - started) * 1000, 2)})
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
        outcome = "failed" if is_final_attempt else "retrying"
        logger.exception("Document processing attempt failed", extra={**log_context, "outcome": outcome, "duration_ms": round((time.perf_counter() - started) * 1000, 2)})
        return False

    Document.objects.filter(pk=document.pk).update(
        status=Document.Status.PROCESSED,
        processing_attempts=attempts,
        last_error="",
        extracted_data=extracted_data,
        updated_at=timezone.now(),
    )
    logger.info("Document processing completed", extra={**log_context, "outcome": "processed", "duration_ms": round((time.perf_counter() - started) * 1000, 2)})
    return True
