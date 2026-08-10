from typing import Literal

from pydantic import BaseModel

UserRole = Literal["student", "admin"]


class AuthUser(BaseModel):
    id: str
    email: str
    display_name: str
    avatar_url: str | None
    role: UserRole


class AuthMe(BaseModel):
    user: AuthUser
