import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return request_id_var.get()


def set_request_id(request_id: str | None) -> None:
    request_id_var.set(request_id)


def new_request_id() -> str:
    request_id = str(uuid.uuid4())
    set_request_id(request_id)
    return request_id
