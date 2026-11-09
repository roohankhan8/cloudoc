import logging

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .queue import queue_url
from .aws import aws_client

logger = logging.getLogger(__name__)


@require_GET
def health(request):
    database_status = "ok"
    queue_status = "ok"
    queue_depth = in_flight = None

    try:
        connection.ensure_connection()
    except Exception:
        database_status = "unavailable"
        logger.exception("Database health check failed", extra={"event": "health_check", "outcome": "database_unavailable"})

    try:
        attributes = aws_client("sqs").get_queue_attributes(
            QueueUrl=queue_url(),
            AttributeNames=["ApproximateNumberOfMessages", "ApproximateNumberOfMessagesNotVisible"],
        )["Attributes"]
        queue_depth = int(attributes.get("ApproximateNumberOfMessages", 0))
        in_flight = int(attributes.get("ApproximateNumberOfMessagesNotVisible", 0))
    except Exception:
        queue_status = "unavailable"
        logger.exception("Queue health check failed", extra={"event": "health_check", "outcome": "queue_unavailable"})

    healthy = database_status == queue_status == "ok"
    logger.info("Operational health check", extra={"event": "health_check", "outcome": "ok" if healthy else "degraded", "database": database_status, "queue": queue_status, "queue_depth": queue_depth, "in_flight": in_flight})
    return JsonResponse(
        {"status": "ok" if healthy else "degraded", "database": database_status, "queue": queue_status, "queue_depth": queue_depth, "in_flight": in_flight},
        status=200 if healthy else 503,
    )
