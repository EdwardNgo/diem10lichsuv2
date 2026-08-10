from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from diem10_api.core.security import hash_token, normalize_email
from diem10_api.models import AdminAllowlist, OAuthState, User, UserSession


class AuthRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_oauth_state(self, state_hash: str) -> OAuthState | None:
        return self._session.scalar(
            select(OAuthState).where(OAuthState.state_hash == state_hash)
        )

    def add_oauth_state(self, oauth_state: OAuthState) -> None:
        self._session.add(oauth_state)
        self._session.commit()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def flush(self) -> None:
        self._session.flush()

    def refresh(self, instance: object) -> None:
        self._session.refresh(instance)

    def get_user_by_google_subject(self, subject: str) -> User | None:
        return self._session.scalar(select(User).where(User.google_subject == subject))

    def add_user(self, user: User) -> User:
        self._session.add(user)
        return user

    def add_user_session(self, user_session: UserSession) -> None:
        self._session.add(user_session)

    def get_user_session_by_token(self, token: str) -> UserSession | None:
        return self._session.scalar(
            select(UserSession).where(UserSession.token_hash == hash_token(token))
        )

    def get_user_by_id(self, user_id: object) -> User | None:
        return self._session.scalar(select(User).where(User.id == user_id))

    def is_active_admin(self, email: str) -> bool:
        allowlist_id = self._session.scalar(
            select(AdminAllowlist.id)
            .where(AdminAllowlist.email == normalize_email(email))
            .where(AdminAllowlist.revoked_at.is_(None))
        )
        return allowlist_id is not None

    def update_last_seen(self, user_session: UserSession, seen_at: datetime) -> None:
        user_session.last_seen_at = seen_at
        self._session.commit()
