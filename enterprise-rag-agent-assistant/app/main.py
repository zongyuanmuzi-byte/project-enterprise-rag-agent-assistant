from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.config import settings, validate_settings
from app.database.db import init_db
from app.utils.logger import app_logger
from app.api.documents import router as documents_router
from app.api.agent import router as agent_router
from app.api.feedback import router as feedback_router


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    validate_settings()
    init_db()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Enterprise RAG Agent Assistant - Engineering Foundation Stage",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(documents_router)
    app.include_router(agent_router)
    app.include_router(feedback_router)

    register_exception_handlers(app)

    app_logger.info(
        "Application started | app_name=%s | app_env=%s",
        settings.app_name,
        settings.app_env,
    )

    return app


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers.

    These handlers make API error responses more consistent.
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        app_logger.error(
            "path=%s | status_code=%s | error_message=%s",
            request.url.path,
            exc.status_code,
            exc.detail,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "request_id": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        app_logger.error(
            "path=%s | status_code=%s | error_message=%s",
            request.url.path,
            422,
            str(exc),
        )

        return JSONResponse(
            status_code=422,
            content={
                "detail": "Request validation failed. Please check your input.",
                "request_id": None,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        app_logger.error(
            "path=%s | status_code=%s | error_message=%s",
            request.url.path,
            500,
            str(exc),
        )

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error.",
                "request_id": None,
            },
        )


app = create_app()
