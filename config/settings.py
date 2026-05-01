from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "super-secret-key-change-in-production-32chars!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DATABASE_URL: str = "sqlite:///./tes.db"

    MAX_FAILED_ATTEMPTS: int = 3
    LOCKOUT_MINUTES: int = 15

    LOG_FILE: str = "logs/tes_audit.log"
    LOG_MAX_BYTES: int = 5 * 1024 * 1024  # 5 MB
    LOG_BACKUP_COUNT: int = 5
    LOG_RETENTION_DAYS: int = 30
    LOG_REMOTE_URL: str = ""  # Пустая строка — удалённая отправка отключена

    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_DEFAULT: str = "60/minute"


settings = Settings()
