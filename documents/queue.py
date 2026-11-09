import json
import logging

from django.conf import settings

from .aws import aws_client

logger = logging.getLogger(__name__)


def queue_url(queue_name=None):
    return aws_client("sqs").get_queue_url(QueueName=queue_name or settings.SQS_QUEUE_NAME)["QueueUrl"]


def enqueue_document(document_id):
    sqs = aws_client("sqs")
    response = sqs.send_message(
        QueueUrl=queue_url(),
        MessageBody=json.dumps({"document_id": str(document_id)}),
    )
    logger.info("Document queued", extra={"event": "document_queued", "document_id": str(document_id), "message_id": response.get("MessageId"), "outcome": "queued"})
