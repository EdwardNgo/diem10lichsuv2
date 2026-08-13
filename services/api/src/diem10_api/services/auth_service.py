import base64
import hashlib
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from urllib.parse import urlencode, urlsplit, urlunsplit

import httpx
import jwt
from fastapi import HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from diem10_api.core.logging import get_logger
from diem10_api.core.security import hash_token, normalize_email, safe_return_path
from diem10_api.models import OAuthState, User, UserSession
from diem10_api.repositories.auth_repository import AuthRepository
from diem10_api.schemas.auth import AuthMe, AuthUser, UserRole

logger = get_logger("auth_service")


class AuthProviderError(Exception):
    pass


@dataclass(frozen=True)
class AuthSettings:
    app_base_url: str
    google_client_id: str
    google_client_secret: str
    google_authorization_url: str
    google_token_url: str
    google_jwks_url: str
    session_cookie_name: str
    session_ttl_seconds: int
    oauth_state_ttl_seconds: int
    cookie_secure: bool


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def auth_settings() -> AuthSettings:
    app_base_url = os.getenv("APP_BASE_URL", "http://localhost:8080").rstrip("/")
    return AuthSettings(
        app_base_url=app_base_url,
        google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
        google_authorization_url=os.getenv(
            "GOOGLE_AUTHORIZATION_URL",
            "https://accounts.google.com/o/oauth2/v2/auth",
        ),
        google_token_url=os.getenv(
            "GOOGLE_TOKEN_URL",
            "https://oauth2.googleapis.com/token",
        ),
        google_jwks_url=os.getenv(
            "GOOGLE_JWKS_URL",
            "https://www.googleapis.com/oauth2/v3/certs",
        ),
        session_cookie_name=os.getenv("SESSION_COOKIE_NAME", "diem10_session"),
        session_ttl_seconds=int(os.getenv("SESSION_TTL_SECONDS", "604800")),
        oauth_state_ttl_seconds=int(os.getenv("OAUTH_STATE_TTL_SECONDS", "600")),
        cookie_secure=_bool_env(
            "SESSION_COOKIE_SECURE",
            app_base_url.startswith("https://"),
        ),
    )


def _now() -> datetime:
    return datetime.now(UTC)


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _redirect_uri(settings: AuthSettings) -> str:
    return f"{settings.app_base_url}/v1/auth/google/callback"


def _append_auth_error(return_to: str, error_code: str) -> str:
    parsed = urlsplit(return_to)
    query_items: list[str] = []
    if parsed.query:
        query_items.append(parsed.query)
    query_items.append(urlencode({"auth_error": error_code}))
    return urlunsplit(("", "", parsed.path, "&".join(query_items), parsed.fragment))


def _require_google_config(settings: AuthSettings) -> None:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login is not configured",
        )


def exchange_google_code(
    settings: AuthSettings,
    code: str,
    code_verifier: str,
) -> dict[str, Any]:
    response = httpx.post(
        settings.google_token_url,
        data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": _redirect_uri(settings),
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        },
        timeout=10,
    )
    if response.status_code != status.HTTP_200_OK:
        raise AuthProviderError("Google token exchange failed")

    data: object = response.json()
    if not isinstance(data, dict):
        raise AuthProviderError("Google token response is invalid")
    return cast(dict[str, Any], data)


def verify_google_id_token(settings: AuthSettings, id_token: str) -> dict[str, Any]:
    try:
        jwk_client = jwt.PyJWKClient(settings.google_jwks_url)
        signing_key = jwk_client.get_signing_key_from_jwt(id_token)
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.google_client_id,
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise AuthProviderError("Google id token is invalid") from exc

    issuer = claims.get("iss")
    if issuer not in {"https://accounts.google.com", "accounts.google.com"}:
        raise AuthProviderError("Google id token issuer is invalid")

    return claims


def _claim_string(claims: dict[str, Any], key: str) -> str | None:
    value = claims.get(key)
    if isinstance(value, str) and value.strip():
        return value
    return None


class AuthService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = AuthRepository(session)

    def load_current_session(
        self,
        request: Request,
        settings: AuthSettings,
    ) -> tuple[User, UserSession]:
        token = request.cookies.get(settings.session_cookie_name)
        if token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        user_session = self._repo.get_user_session_by_token(token)
        if user_session is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        now = _now()
        if (
            user_session.revoked_at is not None
            or _ensure_aware(user_session.expires_at) <= now
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        user = self._repo.get_user_by_id(user_session.user_id)
        if user is None or user.status != "active":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        self._repo.update_last_seen(user_session, now)
        return user, user_session

    def resolve_user_role(self, user: User) -> UserRole:
        if self._repo.is_active_admin(user.email):
            return "admin"
        return "student"

    def start_google_login(
        self,
        return_to: str | None,
        settings: AuthSettings,
    ) -> RedirectResponse:
        _require_google_config(settings)

        state = secrets.token_urlsafe(32)
        code_verifier = secrets.token_urlsafe(64)
        oauth_state = OAuthState(
            state_hash=hash_token(state),
            code_verifier=code_verifier,
            return_to=safe_return_path(return_to),
            expires_at=_now() + timedelta(seconds=settings.oauth_state_ttl_seconds),
        )
        self._repo.add_oauth_state(oauth_state)
        logger.info("auth.google.started", return_to=oauth_state.return_to)

        params = urlencode(
            {
                "client_id": settings.google_client_id,
                "redirect_uri": _redirect_uri(settings),
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "code_challenge": _code_challenge(code_verifier),
                "code_challenge_method": "S256",
                "prompt": "select_account",
            }
        )
        return RedirectResponse(f"{settings.google_authorization_url}?{params}")

    def google_callback(
        self,
        request: Request,
        code: str | None,
        state: str | None,
        error: str | None,
        settings: AuthSettings,
    ) -> RedirectResponse:
        fallback = "/exams"
        if state is None:
            logger.warning("auth.google.callback.invalid_state", reason="missing_state")
            return RedirectResponse(
                _append_auth_error(fallback, "invalid_state"), status_code=303
            )

        oauth_state = self._repo.get_oauth_state(hash_token(state))
        if (
            oauth_state is None
            or oauth_state.used_at is not None
            or _ensure_aware(oauth_state.expires_at) <= _now()
        ):
            logger.warning(
                "auth.google.callback.invalid_state", reason="state_not_found"
            )
            return RedirectResponse(
                _append_auth_error(fallback, "invalid_state"), status_code=303
            )

        oauth_state.used_at = _now()
        self._repo.commit()
        return_to = safe_return_path(oauth_state.return_to)

        if error is not None:
            logger.info("auth.google.callback.cancelled")
            return RedirectResponse(
                _append_auth_error(return_to, "cancelled"), status_code=303
            )
        if code is None:
            return RedirectResponse(
                _append_auth_error(return_to, "missing_code"), status_code=303
            )

        try:
            token_response = exchange_google_code(
                settings, code, oauth_state.code_verifier
            )
            id_token = token_response.get("id_token")
            if not isinstance(id_token, str):
                raise AuthProviderError("Google id token is missing")
            claims = verify_google_id_token(settings, id_token)
        except AuthProviderError:
            logger.warning("auth.google.callback.provider_error")
            return RedirectResponse(
                _append_auth_error(return_to, "provider_error"), status_code=303
            )

        subject = _claim_string(claims, "sub")
        email = _claim_string(claims, "email")
        if (
            subject is None
            or email is None
            or claims.get("email_verified") is not True
        ):
            return RedirectResponse(
                _append_auth_error(return_to, "invalid_profile"), status_code=303
            )

        email = normalize_email(email)
        display_name = _claim_string(claims, "name") or email
        avatar_url = _claim_string(claims, "picture")
        login_time = _now()
        user = self._repo.get_user_by_google_subject(subject)
        if user is None:
            user = User(
                google_subject=subject,
                email=email,
                display_name=display_name,
                avatar_url=avatar_url,
                last_login_at=login_time,
            )
            self._repo.add_user(user)
        else:
            user.email = email
            user.display_name = display_name
            user.avatar_url = avatar_url
            user.last_login_at = login_time

        try:
            self._repo.flush()
        except IntegrityError:
            self._repo.rollback()
            return RedirectResponse(
                _append_auth_error(return_to, "account_conflict"), status_code=303
            )

        session_token = secrets.token_urlsafe(48)
        expires_at = login_time + timedelta(seconds=settings.session_ttl_seconds)
        user_session = UserSession(
            user_id=user.id,
            token_hash=hash_token(session_token),
            expires_at=expires_at,
            ip_address=request.client.host if request.client is not None else None,
            user_agent=request.headers.get("user-agent"),
        )
        self._repo.add_user_session(user_session)

        try:
            self._repo.commit()
        except IntegrityError:
            self._repo.rollback()
            return RedirectResponse(
                _append_auth_error(return_to, "account_conflict"), status_code=303
            )

        logger.info("auth.google.callback.success", user_id=str(user.id), email=email)
        response = RedirectResponse(return_to, status_code=303)
        response.set_cookie(
            settings.session_cookie_name,
            session_token,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="lax",
            max_age=settings.session_ttl_seconds,
            path="/",
        )
        return response

    def logout(
        self,
        request: Request,
        response: Response,
        settings: AuthSettings,
    ) -> dict[str, bool]:
        token = request.cookies.get(settings.session_cookie_name)
        if token is not None:
            user_session = self._repo.get_user_session_by_token(token)
            if user_session is not None and user_session.revoked_at is None:
                user_session.revoked_at = _now()
                self._repo.commit()
                logger.info("auth.logout", user_id=str(user_session.user_id))

        response.delete_cookie(
            settings.session_cookie_name,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="lax",
            path="/",
        )
        return {"ok": True}

    def me(self, user: User) -> AuthMe:
        return AuthMe(
            user=AuthUser(
                id=str(user.id),
                email=user.email,
                display_name=user.display_name,
                avatar_url=user.avatar_url,
                role=self.resolve_user_role(user),
            )
        )
