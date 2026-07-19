import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import is_supported_password_hash
from app.models.timetable import GeneratedTimetable, GenerationStatus
from app.routers import (
    academic_year,
    auth,
    constraint,
    department,
    division,
    faculty,
    room,
    semester,
    subject,
    timetable,
)

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("campusflow")


def validate_runtime_configuration() -> None:
    if settings.LOGIN_RATE_LIMIT_ATTEMPTS < 1:
        raise RuntimeError("LOGIN_RATE_LIMIT_ATTEMPTS must be at least 1")
    if settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS < 1:
        raise RuntimeError("LOGIN_RATE_LIMIT_WINDOW_SECONDS must be at least 1")
    if settings.LOGIN_RATE_LIMIT_MAX_KEYS < 1:
        raise RuntimeError("LOGIN_RATE_LIMIT_MAX_KEYS must be at least 1")
    if settings.SOLVER_MAX_TIME_SECONDS < 1:
        raise RuntimeError("SOLVER_MAX_TIME_SECONDS must be at least 1")
    if settings.SOLVER_NUM_WORKERS < 0:
        raise RuntimeError("SOLVER_NUM_WORKERS cannot be negative")
    if settings.JWT_SECRET_KEY == "change-this-secret-in-production":
        message = "JWT_SECRET_KEY is using the insecure placeholder value"
        if settings.is_production:
            raise RuntimeError(message)
        logger.warning(message)
    if settings.is_production and len(settings.JWT_SECRET_KEY) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters in production")
    if settings.is_production and not settings.ADMIN_PASSWORD_HASH:
        raise RuntimeError("ADMIN_PASSWORD_HASH must be set in production")
    if settings.ADMIN_PASSWORD_HASH and not is_supported_password_hash(settings.ADMIN_PASSWORD_HASH):
        raise RuntimeError("ADMIN_PASSWORD_HASH must be a supported bcrypt hash")
    if not settings.CORS_ORIGINS:
        raise RuntimeError("CORS_ORIGINS must include at least one allowed origin")
    if settings.is_production and "*" in settings.CORS_ORIGINS:
        raise RuntimeError("CORS_ORIGINS cannot include '*' in production while credentials are enabled")


def mark_interrupted_timetable_runs_failed() -> None:
    db = SessionLocal()
    try:
        runs = (
            db.query(GeneratedTimetable)
            .filter(GeneratedTimetable.status.in_([GenerationStatus.PENDING, GenerationStatus.RUNNING]))
            .all()
        )
        if not runs:
            return
        for run in runs:
            run.status = GenerationStatus.FAILED
            run.message = "Generation was interrupted before completion. Please run the generator again."
        db.commit()
        logger.warning("Marked %d interrupted timetable generation run(s) as failed", len(runs))
    except Exception:
        db.rollback()
        logger.exception("Unable to reconcile interrupted timetable generation runs")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_runtime_configuration()
    mark_interrupted_timetable_runs_failed()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    message = detail
    data = None
    if isinstance(detail, dict):
        message = detail.get("message", "Request failed")
        data = {key: value for key, value in detail.items() if key != "message"} or None
    elif not isinstance(detail, str):
        message = "Request failed"
        data = detail
    if not isinstance(message, str):
        message = str(message)

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({"success": False, "message": message, "data": data}),
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"success": False, "message": "Validation error", "data": {"errors": exc.errors()}}),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "message": "Internal server error", "data": None},
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.info("Database integrity error on %s: %s", request.url.path, exc.orig)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"success": False, "message": "A record with these values already exists", "data": None},
    )


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}


app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(department.router, prefix=settings.API_V1_PREFIX)
app.include_router(academic_year.router, prefix=settings.API_V1_PREFIX)
app.include_router(semester.router, prefix=settings.API_V1_PREFIX)
app.include_router(division.router, prefix=settings.API_V1_PREFIX)
app.include_router(subject.router, prefix=settings.API_V1_PREFIX)
app.include_router(faculty.router, prefix=settings.API_V1_PREFIX)
app.include_router(room.router, prefix=settings.API_V1_PREFIX)
app.include_router(constraint.router, prefix=settings.API_V1_PREFIX)
app.include_router(timetable.router, prefix=settings.API_V1_PREFIX)
