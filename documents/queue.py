import json

from django.conf import settings

from .aws import aws_client


def queue_url(queue_name=None):
    return aws_client("sqs").get_queue_url(QueueName=queue_name or settings.SQS_QUEUE_NAME)["QueueUrl"]


def enqueue_document(document_id):
    sqs = aws_client("sqs")
    sqs.send_message(
        QueueUrl=queue_url(),
        MessageBody=json.dumps({"document_id": str(document_id)}),
    )
