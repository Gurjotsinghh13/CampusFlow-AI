import time
from collections import defaultdict, deque

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

_failed_login_attempts: defaultdict[str, deque[float]] = defaultdict(deque)


def _client_key(request: Request, email: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}:{email.lower()}"


def _prune_attempts(attempts: deque[float], now: float) -> None:
    cutoff = now - settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    while attempts and attempts[0] < cutoff:
        attempts.popleft()


def _prune_rate_limit_store(now: float) -> None:
    for key in list(_failed_login_attempts.keys()):
        attempts = _failed_login_attempts[key]
        _prune_attempts(attempts, now)
        if not attempts:
            _failed_login_attempts.pop(key, None)


def _ensure_rate_limit_capacity(key: str, now: float) -> None:
    if key in _failed_login_attempts or len(_failed_login_attempts) < settings.LOGIN_RATE_LIMIT_MAX_KEYS:
        return
    _prune_rate_limit_store(now)
    while len(_failed_login_attempts) >= settings.LOGIN_RATE_LIMIT_MAX_KEYS:
        _failed_login_attempts.pop(next(iter(_failed_login_attempts)))


def _check_login_rate_limit(request: Request, email: str) -> str:
    key = _client_key(request, email)
    now = time.monotonic()
    _ensure_rate_limit_capacity(key, now)
    attempts = _failed_login_attempts[key]
    _prune_attempts(attempts, now)
    if len(attempts) >= settings.LOGIN_RATE_LIMIT_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
        )
    return key


def _record_failed_login(key: str) -> None:
    attempts = _failed_login_attempts[key]
    now = time.monotonic()
    _prune_attempts(attempts, now)
    attempts.append(now)


def _clear_failed_logins(key: str) -> None:
    _failed_login_attempts.pop(key, None)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request) -> TokenResponse:
    rate_limit_key = _check_login_rate_limit(request, payload.email)
    if payload.email.lower() != settings.ADMIN_EMAIL.lower() or not settings.ADMIN_PASSWORD_HASH:
        _record_failed_login(rate_limit_key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(payload.password, settings.ADMIN_PASSWORD_HASH):
        _record_failed_login(rate_limit_key)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    _clear_failed_logins(rate_limit_key)
    token = create_access_token(subject=settings.ADMIN_EMAIL)
    return TokenResponse(access_token=token, expires_in_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
