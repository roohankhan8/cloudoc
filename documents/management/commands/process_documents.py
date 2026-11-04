import json
import logging
import uuid

from django.conf import settings
from django.core.management.base import BaseCommand

from documents.aws import aws_client
from documents.processing import process_document
from documents.queue import queue_url

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

        attempts = int(message.get("Attributes", {}).get("ApproximateReceiveCount", "1"))
        try:
            return process_document(document_id, attempts)
        except Exception:
            logger.exception("Document %s processing failed before it could be recorded.", document_id)
            return False
