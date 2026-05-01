from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from auth.dependencies import require_admin
from config.settings import settings
from database.models import User

router = APIRouter(prefix="/log-settings", tags=["log-settings"])


class LogSettingsUpdate(BaseModel):
    log_max_mb: int = Field(ge=1, le=500)
    log_backup_count: int = Field(ge=1, le=50)
    log_retention_days: int = Field(ge=1, le=3650)
    log_level: str = Field(pattern="^(DEBUG|INFO|WARNING|ERROR)$")
    log_remote_url: str = ""


@router.get("/")
def get_log_settings(admin: User = Depends(require_admin)):
    return {
        "log_max_mb":        settings.LOG_MAX_BYTES // (1024 * 1024),
        "log_backup_count":  settings.LOG_BACKUP_COUNT,
        "log_retention_days": settings.LOG_RETENTION_DAYS,
        "log_level":         "INFO",
        "log_remote_url":    settings.LOG_REMOTE_URL,
    }


@router.post("/")
def update_log_settings(
    body: LogSettingsUpdate,
    admin: User = Depends(require_admin),
):
    import logging
    settings.LOG_MAX_BYTES = body.log_max_mb * 1024 * 1024
    settings.LOG_BACKUP_COUNT = body.log_backup_count
    settings.LOG_RETENTION_DAYS = body.log_retention_days
    settings.LOG_REMOTE_URL = body.log_remote_url

    # Применяем уровень детализации ко всем логгерам приложения
    level = getattr(logging, body.log_level, logging.INFO)
    import logging_subsystem.logger as log_mod
    log_mod.app_logger.setLevel(level)
    for handler in log_mod.app_logger.handlers:
        handler.setLevel(level)
        # Обновляем RotatingFileHandler с новыми параметрами ротации
        if hasattr(handler, "maxBytes"):
            handler.maxBytes = settings.LOG_MAX_BYTES
            handler.backupCount = settings.LOG_BACKUP_COUNT

    return {"detail": "Настройки журнала обновлены", "applied": body.model_dump()}
