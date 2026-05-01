import logging
import logging.handlers
import os
import uuid
from datetime import datetime

from config.settings import settings

os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)

_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_file_handler = logging.handlers.RotatingFileHandler(
    settings.LOG_FILE,
    maxBytes=settings.LOG_MAX_BYTES,
    backupCount=settings.LOG_BACKUP_COUNT,
    encoding="utf-8",
)
_file_handler.setFormatter(_formatter)

_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_formatter)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        logger.addHandler(_file_handler)
        logger.addHandler(_console_handler)
    return logger


app_logger = get_logger("tes_app")


def make_event(
    event_type: str,
    component: str,
    username: str | None = None,
    user_id: int | None = None,
    ip_address: str | None = None,
    details: str | None = None,
) -> dict:
    """Формирует структурированную запись события (без паролей и PII)."""
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "component": component,
        "username": username,
        "user_id": user_id,
        "ip_address": ip_address,
        "details": details,
    }


def log_event(
    event_type: str,
    component: str,
    username: str | None = None,
    user_id: int | None = None,
    ip_address: str | None = None,
    details: str | None = None,
) -> dict:
    event = make_event(event_type, component, username, user_id, ip_address, details)
    app_logger.info(
        "EVENT | id=%s | type=%s | component=%s | user=%s | ip=%s | %s",
        event["event_id"],
        event_type,
        component,
        username or "-",
        ip_address or "-",
        details or "",
    )
    return event
