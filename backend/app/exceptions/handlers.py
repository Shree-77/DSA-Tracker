"""Centralized FastAPI exception handlers.

Guarantees a consistent error envelope for the Flutter client:

    {
      "error": {
        "code": "VALIDATION_ERROR",
        "message": "...",
        "details": {}
      }
    }
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions.errors import AppError

logger = logging.getLogger("dsa_tracker")


def _envelope(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the FastAPI application."""

    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        logger.info("AppError %s: %s", exc.code, exc.message)
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(RequestValidationError)
    async def _handle_request_validation(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_envelope(
                "VALIDATION_ERROR",
                "Request validation failed",
                {"errors": exc.errors()},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_exception(
        _: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(code, str(exc.detail)),
        )

    @app.exception_handler(SQLAlchemyError)
    async def _handle_db_error(_: Request, exc: SQLAlchemyError) -> JSONResponse:
        # Never expose raw DB errors to the client.
        logger.exception("Database error: %s", exc)
        return JSONResponse(
            status_code=500,
            content=_envelope("DATABASE_ERROR", "A database error occurred"),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content=_envelope("INTERNAL_ERROR", "An unexpected error occurred"),
        )
