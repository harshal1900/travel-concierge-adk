"""Correlation IDs and one structured JSON log line per request."""

import json
import logging
import time
import uuid

from fastapi import Request

logger = logging.getLogger("request")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {"level": record.levelname, "logger": record.name, "message": record.getMessage()}
        payload.update(getattr(record, "fields", {}))
        if record.exc_info:
            payload["exc_type"] = record.exc_info[0].__name__  # type only; trace stays out of client responses
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


async def correlation_middleware(request: Request, call_next):
    correlation_id = uuid.uuid4().hex
    request.state.correlation_id = correlation_id
    request.state.log = {}
    started = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    finally:
        fields = {
            "correlation_id": correlation_id,
            "path": request.url.path,
            "status": status,
            "latency_ms": round((time.perf_counter() - started) * 1000),
            **request.state.log,
        }
        logger.info("request", extra={"fields": fields})
