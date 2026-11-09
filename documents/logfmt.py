import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    fields = ("event", "document_id", "message_id", "attempts", "outcome", "duration_ms", "owner_id", "queue_depth", "in_flight", "database", "queue")

    def format(self, record):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        entry.update({field: getattr(record, field) for field in self.fields if hasattr(record, field)})
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)
