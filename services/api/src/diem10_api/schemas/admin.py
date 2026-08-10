from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from diem10_api.core.security import normalize_email


class AdminProbe(BaseModel):
    ok: bool


class AllowlistEntry(BaseModel):
    id: str
    email: str
    added_by_user_id: str | None
    created_at: datetime
    revoked_at: datetime | None


class AllowlistGrantRequest(BaseModel):
    email: str = Field(max_length=320)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = normalize_email(value)
        if "@" not in normalized:
            raise ValueError("email must contain @")
        return normalized


class AllowlistPage(BaseModel):
    items: list[AllowlistEntry]


class SourceDocumentUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)
    checksum_sha256: str = Field(min_length=64, max_length=64)


class SourceDocumentUploadUrl(BaseModel):
    object_key: str
    bucket: str
    upload_url: str
    method: str
    headers: dict[str, str]
    expires_in_seconds: int


class SourceDocumentConfirmRequest(BaseModel):
    object_key: str = Field(min_length=1, max_length=2048)
    bucket: str = Field(min_length=1, max_length=255)
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)
    checksum_sha256: str = Field(min_length=64, max_length=64)


class AssetResponse(BaseModel):
    id: str
    object_key: str
    bucket: str
    mime_type: str
    size_bytes: int
    checksum_sha256: str
    asset_kind: str
    uploaded_by_user_id: str
    created_at: datetime


class SourceDocumentPage(BaseModel):
    items: list[AssetResponse]


class ImportRequest(BaseModel):
    idempotency_key: str | None = Field(default=None, max_length=128)


class ImportFindingResponse(BaseModel):
    severity: str
    field_path: str
    message: str
    raw_value: str | None = None


class ImportSummary(BaseModel):
    part1_count: int
    part2_count: int
    warnings: int
    errors: int


class ImportJobResponse(BaseModel):
    import_job_id: str
    exam_version_id: str | None
    status: str
    error_code: str | None = None
    findings: list[ImportFindingResponse]
    summary: ImportSummary
