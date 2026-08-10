import hashlib
from urllib.parse import urlsplit, urlunsplit


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_token(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def safe_return_path(value: str | None, fallback: str = "/dashboard") -> str:
    if value is None:
        return fallback

    candidate = value.strip()
    if (
        candidate == ""
        or not candidate.startswith("/")
        or candidate.startswith("//")
        or "\\" in candidate
    ):
        return fallback

    parsed = urlsplit(candidate)
    if parsed.scheme or parsed.netloc:
        return fallback

    return urlunsplit(("", "", parsed.path or fallback, parsed.query, parsed.fragment))
