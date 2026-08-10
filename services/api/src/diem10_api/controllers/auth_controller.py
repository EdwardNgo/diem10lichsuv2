from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from diem10_api.controllers.deps import get_current_user
from diem10_api.database import get_session
from diem10_api.models import User
from diem10_api.schemas.auth import AuthMe
from diem10_api.services.auth_service import AuthService, AuthSettings, auth_settings

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.get("/google")
def start_google_login(
    return_to: str | None = Query(default=None, max_length=2048),
    session: Session = Depends(get_session),
    settings: AuthSettings = Depends(auth_settings),
) -> RedirectResponse:
    return AuthService(session).start_google_login(return_to, settings)


@router.get("/google/callback")
def google_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    session: Session = Depends(get_session),
    settings: AuthSettings = Depends(auth_settings),
) -> RedirectResponse:
    return AuthService(session).google_callback(
        request,
        code,
        state,
        error,
        settings,
    )


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
    settings: AuthSettings = Depends(auth_settings),
) -> dict[str, bool]:
    return AuthService(session).logout(request, response, settings)


@router.get("/me", response_model=AuthMe)
def me(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AuthMe:
    return AuthService(session).me(current_user)
