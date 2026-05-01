from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from database.engine import init_db
from ё.middleware import limiter
from ё.routers import auth_router, calc_router, users_router, audit_router, log_settings_router


def create_app() -> FastAPI:
    init_db()

    app = FastAPI(title="ТЭС Оптимизация", version="1.0.0")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(calc_router)
    app.include_router(users_router)
    app.include_router(audit_router)
    app.include_router(log_settings_router)

    return app


app = create_app()
