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

# Таблица: тип события → уровень логирования
# Позволяет фильтровать события по уровню детализации
_EVENT_LEVELS: dict[str, int] = {
    # ERROR — критические сбои (попытки взлома, блокировки)
    "LOGIN_LOCKED":           logging.ERROR,
    "LOGIN_BLOCKED":          logging.ERROR,
    # WARNING — подозрительные действия
    "LOGIN_FAILED":           logging.WARNING,
    "CHANGE_PASSWORD_FAILED": logging.WARNING,
    # INFO — штатные события аудита
    "LOGIN_SUCCESS":          logging.INFO,
    "LOGOUT":                 logging.INFO,
    "CHANGE_PASSWORD_SUCCESS":logging.INFO,
    "USER_CREATED":           logging.INFO,
    "USER_UPDATED":           logging.INFO,
    "USER_UNLOCKED":          logging.INFO,
    "PASSWORD_RESET":         logging.INFO,
    "CALCULATION":            logging.INFO,
    # DEBUG — детальные технические события
    "API_REQUEST":            logging.DEBUG,
}


def _level_for(event_type: str) -> int:
    return _EVENT_LEVELS.get(event_type, logging.INFO)


def set_log_level(level_name: str):
    """
    Устанавливает уровень детализации журнала.
    Поддерживаемые значения: ALL, DEBUG, INFO, WARNING, ERROR.
    ALL — фиксируются абсолютно все события всех уровней.
    """
    if level_name == "ALL":
        numeric = logging.NOTSET  # 0 — пропускает всё
    else:
        numeric = getattr(logging, level_name, logging.INFO)

    app_logger.setLevel(numeric)
    for handler in app_logger.handlers:
        handler.setLevel(numeric)


def make_event(
    event_type: str,
    component: str,
    username: str | None = None,
    user_id: int | None = None,
    ip_address: str | None = None,
    details: str | None = None,
    headers: str | None = None,
) -> dict:
    """Формирует структурированную запись события (без паролей и PII)."""
    return {
        "event_id":   str(uuid.uuid4()),
        "timestamp":  datetime.utcnow().isoformat(),
        "event_type": event_type,
        "component":  component,
        "username":   username,
        "user_id":    user_id,
        "ip_address": ip_address,
        "details":    details,
        "headers":    headers,
    }


def log_event(
    event_type: str,
    component: str,
    username: str | None = None,
    user_id: int | None = None,
    ip_address: str | None = None,
    details: str | None = None,
    headers: str | None = None,
) -> dict:
    event = make_event(event_type, component, username, user_id,
                       ip_address, details, headers)
    level = _level_for(event_type)
    app_logger.log(
        level,
        "EVENT | id=%s | type=%s | component=%s | user=%s | ip=%s | headers=[%s] | %s",
        event["event_id"],
        event_type,
        component,
        username or "-",
        ip_address or "-",
        headers or "-",
        details or "",
    )
    return event
