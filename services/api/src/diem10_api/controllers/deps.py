from fastapi import Depends, Request
from sqlalchemy.orm import Session

from diem10_api.database import get_session
from diem10_api.models import User
from diem10_api.services.auth_service import AuthService, AuthSettings, auth_settings


def get_auth_service(session: Session = Depends(get_session)) -> AuthService:
    return AuthService(session)


def get_current_user(
    request: Request,
    session: Session = Depends(get_session),
    settings: AuthSettings = Depends(auth_settings),
) -> User:
    service = AuthService(session)
    user, _ = service.load_current_session(request, settings)
    return user


def require_admin(
    request: Request,
    session: Session = Depends(get_session),
    settings: AuthSettings = Depends(auth_settings),
) -> User:
    service = AuthService(session)
    user, _ = service.load_current_session(request, settings)
    if service.resolve_user_role(user) != "admin":
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return user
