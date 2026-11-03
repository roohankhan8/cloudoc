import json
import logging
import uuid

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from documents.aws import aws_client
from documents.models import Document
from documents.queue import queue_url
from documents.storage import verify_document_exists

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Continuously process documents from the SQS queue."

    def handle(self, *args, **options):
        sqs = aws_client("sqs")
        current_queue_url = queue_url()
        self.stdout.write(f"Polling {settings.SQS_QUEUE_NAME}; press Ctrl+C to stop.")

        while True:
            response = sqs.receive_message(
                QueueUrl=current_queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=settings.SQS_WAIT_TIME_SECONDS,
                VisibilityTimeout=settings.SQS_VISIBILITY_TIMEOUT,
                AttributeNames=["ApproximateReceiveCount"],
            )
            for message in response.get("Messages", []):
                if self.process_message(message):
                    sqs.delete_message(
                        QueueUrl=current_queue_url,
                        ReceiptHandle=message["ReceiptHandle"],
                    )

    def process_message(self, message):
        try:
            document_id = str(uuid.UUID(json.loads(message["Body"])["document_id"]))
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            logger.exception("Invalid document message; leaving it for SQS redrive.")
            return False

        try:
            document = Document.objects.get(pk=document_id)
        except Document.DoesNotExist:
            logger.warning("Document %s no longer exists; acknowledging message.", document_id)
            return True

        if document.status in (Document.Status.PROCESSED, Document.Status.FAILED):
            return True

        attempts = int(message.get("Attributes", {}).get("ApproximateReceiveCount", "1"))
        Document.objects.filter(pk=document.pk).update(
            status=Document.Status.PROCESSING,
            processing_attempts=attempts,
            updated_at=timezone.now(),
        )
        try:
            verify_document_exists(document.object_key)
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
            updated_at=timezone.now(),
        )
        self.stdout.write(f"Processed document {document_id}")
        return True
