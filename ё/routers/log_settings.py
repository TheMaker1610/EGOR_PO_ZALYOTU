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
    log_level: str = Field(pattern="^(ALL|DEBUG|INFO|WARNING|ERROR)$")
    log_remote_url: str = ""


@router.get("/")
def get_log_settings(admin: User = Depends(require_admin)):
    import logging
    import logging_subsystem.logger as log_mod
    current_level = log_mod.app_logger.level
    if current_level == logging.NOTSET:
        level_name = "ALL"
    else:
        level_name = logging.getLevelName(current_level)
    return {
        "log_max_mb":         settings.LOG_MAX_BYTES // (1024 * 1024),
        "log_backup_count":   settings.LOG_BACKUP_COUNT,
        "log_retention_days": settings.LOG_RETENTION_DAYS,
        "log_level":          level_name,
        "log_remote_url":     settings.LOG_REMOTE_URL,
    }


@router.post("/")
def update_log_settings(
    body: LogSettingsUpdate,
    admin: User = Depends(require_admin),
):
    import logging_subsystem.logger as log_mod
    settings.LOG_MAX_BYTES = body.log_max_mb * 1024 * 1024
    settings.LOG_BACKUP_COUNT = body.log_backup_count
    settings.LOG_RETENTION_DAYS = body.log_retention_days
    settings.LOG_REMOTE_URL = body.log_remote_url

    # Применяем уровень детализации (включая ALL)
    log_mod.set_log_level(body.log_level)

    # Обновляем параметры ротации файла
    for handler in log_mod.app_logger.handlers:
        if hasattr(handler, "maxBytes"):
            handler.maxBytes = settings.LOG_MAX_BYTES
            handler.backupCount = settings.LOG_BACKUP_COUNT

    return {"detail": "Настройки журнала обновлены", "applied": body.model_dump()}
