from fastapi import Request


def extract_headers(request: Request) -> str:
    """
    Формирует строку служебных заголовков для журнала аудита.
    Исключает заголовок Authorization (безопасность).
    """
    safe_keys = {"user-agent", "content-type", "accept", "host", "origin", "referer"}
    parts = [
        f"method={request.method}",
        f"path={request.url.path}",
    ]
    for key, value in request.headers.items():
        if key.lower() in safe_keys:
            parts.append(f"{key}={value}")
    return "; ".join(parts)
