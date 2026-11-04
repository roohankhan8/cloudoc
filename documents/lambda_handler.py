import json
import logging
import os
import uuid

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from .processing import process_document

logger = logging.getLogger(__name__)


def handler(event, context):
    batch_item_failures = []
    for record in event.get("Records", []):
        try:
            document_id = uuid.UUID(json.loads(record["body"])["document_id"])
            attempts = int(record.get("attributes", {}).get("ApproximateReceiveCount", "1"))
            succeeded = process_document(document_id, attempts)
        except Exception:
            logger.exception("Could not process SQS message %s.", record.get("messageId"))
            succeeded = False
        if not succeeded:
            batch_item_failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": batch_item_failures}
