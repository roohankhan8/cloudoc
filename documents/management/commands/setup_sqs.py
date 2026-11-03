import json

from django.conf import settings
from django.core.management.base import BaseCommand

from documents.aws import aws_client


class Command(BaseCommand):
    help = "Create the CloudDoc processing queue and its dead-letter queue."

    def handle(self, *args, **options):
        sqs = aws_client("sqs")
        dlq_url = sqs.create_queue(QueueName=settings.SQS_DLQ_NAME)["QueueUrl"]
        dlq_arn = sqs.get_queue_attributes(
            QueueUrl=dlq_url,
            AttributeNames=["QueueArn"],
        )["Attributes"]["QueueArn"]
        queue_url = sqs.create_queue(QueueName=settings.SQS_QUEUE_NAME)["QueueUrl"]
        sqs.set_queue_attributes(
            QueueUrl=queue_url,
            Attributes={
                "VisibilityTimeout": str(settings.SQS_VISIBILITY_TIMEOUT),
                "ReceiveMessageWaitTimeSeconds": str(settings.SQS_WAIT_TIME_SECONDS),
                "RedrivePolicy": json.dumps(
                    {
                        "deadLetterTargetArn": dlq_arn,
                        "maxReceiveCount": str(settings.SQS_MAX_RECEIVE_COUNT),
                    }
                ),
            },
        )
        self.stdout.write(self.style.SUCCESS(f"Processing queue ready: {queue_url}"))
        self.stdout.write(self.style.SUCCESS(f"Dead-letter queue ready: {dlq_url}"))
