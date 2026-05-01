import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from config.settings import settings


def create_access_token(user_id: int, username: str, role: str) -> tuple[str, str, datetime]:
    """Возвращает (token, jti, expires_at)."""
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "jti": jti,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti, expire


def decode_token(token: str) -> dict:
    """Бросает JWTError при невалидном токене."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
