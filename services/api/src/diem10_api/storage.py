import base64
import importlib
import os
import re
from dataclasses import dataclass
from pathlib import PurePath
from typing import Any

MAX_SOURCE_DOCUMENT_BYTES = 20 * 1024 * 1024
MAX_QUESTION_IMAGE_BYTES = 5 * 1024 * 1024
PRESIGNED_UPLOAD_TTL_SECONDS = 900
PRESIGNED_DOWNLOAD_TTL_SECONDS = 900
SOURCE_DOCUMENT_PREFIX = "source-documents/"
QUESTION_IMAGE_PREFIX = "question-images/"

SOURCE_DOCUMENT_MIME_BY_EXTENSION = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pdf": "application/pdf",
}

QUESTION_IMAGE_MIME_BY_EXTENSION = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


@dataclass(frozen=True)
class R2Settings:
    account_id: str
    access_key_id: str
    secret_access_key: str
    bucket_name: str

    @property
    def endpoint_url(self) -> str:
        return f"https://{self.account_id}.r2.cloudflarestorage.com"


class StorageConfigurationError(RuntimeError):
    pass


def get_r2_settings() -> R2Settings:
    account_id = os.getenv("R2_ACCOUNT_ID", "").strip()
    access_key_id = os.getenv("R2_ACCESS_KEY_ID", "").strip()
    secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY", "").strip()
    bucket_name = os.getenv("R2_BUCKET_NAME", "").strip()
    if not all([account_id, access_key_id, secret_access_key, bucket_name]):
        raise StorageConfigurationError("R2 storage is not configured")
    return R2Settings(
        account_id=account_id,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        bucket_name=bucket_name,
    )


def validate_source_document_metadata(
    filename: str,
    mime_type: str,
    size_bytes: int,
    checksum_sha256: str,
) -> str:
    extension = PurePath(filename).name.lower()
    suffix = PurePath(extension).suffix
    expected_mime_type = SOURCE_DOCUMENT_MIME_BY_EXTENSION.get(suffix)
    if expected_mime_type is None:
        raise ValueError("Unsupported source document extension")
    if mime_type != expected_mime_type:
        raise ValueError("MIME type does not match file extension")
    if size_bytes <= 0 or size_bytes > MAX_SOURCE_DOCUMENT_BYTES:
        raise ValueError("Source document size is outside the allowed range")
    normalized_checksum = checksum_sha256.lower()
    if re.fullmatch(r"[0-9a-f]{64}", normalized_checksum) is None:
        raise ValueError("checksum_sha256 must be a 64-character hex digest")
    return normalized_checksum


def sanitize_source_document_filename(filename: str) -> str:
    basename = PurePath(filename).name.strip()
    if not basename or basename in {".", ".."}:
        raise ValueError("Invalid filename")
    if "/" in basename or "\\" in basename or "\x00" in basename:
        raise ValueError("Invalid filename")
    if len(basename) > 255:
        raise ValueError("Filename is too long")
    return basename


def build_source_document_key(filename: str) -> str:
    safe_name = sanitize_source_document_filename(filename)
    suffix = PurePath(safe_name).suffix.lower()
    if suffix not in SOURCE_DOCUMENT_MIME_BY_EXTENSION:
        raise ValueError("Unsupported source document extension")
    return f"{SOURCE_DOCUMENT_PREFIX}{safe_name}"


def validate_question_image_metadata(
    filename: str,
    mime_type: str,
    size_bytes: int,
    checksum_sha256: str,
) -> str:
    extension = PurePath(filename).name.lower()
    suffix = PurePath(extension).suffix
    expected_mime_type = QUESTION_IMAGE_MIME_BY_EXTENSION.get(suffix)
    if expected_mime_type is None:
        raise ValueError("Unsupported question image extension")
    if mime_type != expected_mime_type:
        raise ValueError("MIME type does not match file extension")
    if size_bytes <= 0 or size_bytes > MAX_QUESTION_IMAGE_BYTES:
        raise ValueError("Question image size is outside the allowed range")
    normalized_checksum = checksum_sha256.lower()
    if re.fullmatch(r"[0-9a-f]{64}", normalized_checksum) is None:
        raise ValueError("checksum_sha256 must be a 64-character hex digest")
    return normalized_checksum


def build_question_image_key(filename: str) -> str:
    safe_name = sanitize_source_document_filename(filename)
    suffix = PurePath(safe_name).suffix.lower()
    if suffix not in QUESTION_IMAGE_MIME_BY_EXTENSION:
        raise ValueError("Unsupported question image extension")
    return f"{QUESTION_IMAGE_PREFIX}{safe_name}"


def checksum_hex_to_base64(checksum_sha256: str) -> str:
    return base64.b64encode(bytes.fromhex(checksum_sha256)).decode("ascii")


def create_presigned_source_upload(
    object_key: str,
    mime_type: str,
    checksum_sha256: str,
    settings: R2Settings,
) -> tuple[str, dict[str, str]]:
    checksum_header = checksum_hex_to_base64(checksum_sha256)
    boto3: Any = importlib.import_module("boto3")
    client = boto3.client(
        "s3",
        aws_access_key_id=settings.access_key_id,
        aws_secret_access_key=settings.secret_access_key,
        endpoint_url=settings.endpoint_url,
        region_name="auto",
    )
    upload_url: str = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.bucket_name,
            "Key": object_key,
            "ContentType": mime_type,
            "ChecksumSHA256": checksum_header,
        },
        ExpiresIn=PRESIGNED_UPLOAD_TTL_SECONDS,
        HttpMethod="PUT",
    )
    return upload_url, {
        "Content-Type": mime_type,
        "x-amz-checksum-sha256": checksum_header,
    }


def create_presigned_download(
    object_key: str,
    settings: R2Settings,
) -> str:
    boto3: Any = importlib.import_module("boto3")
    client = boto3.client(
        "s3",
        aws_access_key_id=settings.access_key_id,
        aws_secret_access_key=settings.secret_access_key,
        endpoint_url=settings.endpoint_url,
        region_name="auto",
    )
    download_url: str = client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.bucket_name,
            "Key": object_key,
        },
        ExpiresIn=PRESIGNED_DOWNLOAD_TTL_SECONDS,
        HttpMethod="GET",
    )
    return download_url


def create_presigned_question_image_upload(
    object_key: str,
    mime_type: str,
    checksum_sha256: str,
    settings: R2Settings,
) -> tuple[str, dict[str, str]]:
    return create_presigned_source_upload(
        object_key=object_key,
        mime_type=mime_type,
        checksum_sha256=checksum_sha256,
        settings=settings,
    )


def download_object(
    object_key: str,
    bucket: str,
    settings: R2Settings,
) -> bytes:
    boto3: Any = importlib.import_module("boto3")
    client = boto3.client(
        "s3",
        aws_access_key_id=settings.access_key_id,
        aws_secret_access_key=settings.secret_access_key,
        endpoint_url=settings.endpoint_url,
        region_name="auto",
    )
    response = client.get_object(Bucket=bucket, Key=object_key)
    body: bytes = response["Body"].read()
    return body
