from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from database.engine import SessionLocal
from services.audit_service import AuditService
from ё.middleware.headers import extract_headers


# Пути, которые не нужно фиксировать отдельно (уже покрыты бизнес-событиями)
_SKIP_PATHS = {"/docs", "/openapi.json", "/redoc", "/favicon.ico"}


class AuditRequestMiddleware(BaseHTTPMiddleware):
    """
    Фиксирует каждый входящий HTTP-запрос к API как событие API_REQUEST.
    Покрывает п. 3.3.1 ТЗ: «действия посредством запросов к API,
    включая информацию об аутентификации и авторизации».
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        path = request.url.path
        if any(path.startswith(p) for p in _SKIP_PATHS):
            return response

        try:
            ip = request.client.host if request.client else "unknown"
            hdrs = extract_headers(request)

            # Извлекаем имя пользователя из токена если есть (без валидации — только для журнала)
            username = None
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                try:
                    from auth.jwt_handler import decode_token
                    payload = decode_token(auth_header[7:])
                    username = payload.get("sub")
                except Exception:
                    pass

            details = f"method={request.method} path={path} status={response.status_code}"

            db = SessionLocal()
            try:
                AuditService(db).record(
                    "API_REQUEST", "api",
                    username=username,
                    ip_address=ip,
                    details=details,
                    headers=hdrs,
                )
            finally:
                db.close()
        except Exception:
            pass  # никогда не ломаем запрос из-за аудита

        return response
