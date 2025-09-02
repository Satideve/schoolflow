# backend/app/core/logging.py
"""
Structured logging setup.
"""
import logging
import sys
import json
from logging import LoggerAdapter

class RequestLoggerAdapter(LoggerAdapter):
    def process(self, msg, kwargs):
        extra = self.extra.copy()
        if "request_id" in extra:
            return f"[req:{extra['request_id']}] {msg}", kwargs
        return msg, kwargs

def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '{"ts":"%(asctime)s","level":"%(levelname)s","module":"%(module)s","msg":"%(message)s"}'
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [handler]

def get_logger(name: str, request_id: str | None = None) -> LoggerAdapter:
    base = logging.getLogger(name)
    adapter = RequestLoggerAdapter(base, {"request_id": request_id})
    return adapter
