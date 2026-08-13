from datetime import datetime

from pydantic import BaseModel, Field


class ValidationIssueResponse(BaseModel):
    severity: str
    field_path: str
    message: str
    question_id: str | None = None
    part_number: int | None = None
    part_position: int | None = None


class ValidationResultResponse(BaseModel):
    valid: bool
    errors: list[ValidationIssueResponse]
    warnings: list[ValidationIssueResponse]


class DraftSummary(BaseModel):
    id: str
    exam_id: str
    exam_slug: str
    title: str
    status: str
    updated_at: datetime
    part1_count: int
    part2_count: int
    import_warnings: int | None = None


class DraftPage(BaseModel):
    items: list[DraftSummary]
    page: int
    page_size: int
    total: int


class DraftQuestionOptionResponse(BaseModel):
    id: str
    position: int
    label: str
    body: str
    is_correct: bool


class DraftQuestionStatementResponse(BaseModel):
    id: str
    position: int
    label: str
    body: str
    is_correct: bool


class DraftQuestionImageResponse(BaseModel):
    asset_id: str
    mime_type: str
    download_url: str | None = None


class DraftQuestionResponse(BaseModel):
    id: str
    position: int
    part_number: int
    part_position: int
    question_type: str
    body: str
    source_text: str | None = None
    explanation: str
    options: list[DraftQuestionOptionResponse]
    statements: list[DraftQuestionStatementResponse]
    image: DraftQuestionImageResponse | None = None


class DraftImportFindingResponse(BaseModel):
    id: str
    severity: str
    field_path: str
    message: str
    resolved_at: datetime | None = None


class DraftImportContextResponse(BaseModel):
    import_job_id: str | None = None
    source_asset_id: str | None = None
    source_filename: str | None = None
    source_mime_type: str | None = None
    source_download_url: str | None = None
    findings: list[DraftImportFindingResponse]


class DraftDetailResponse(BaseModel):
    id: str
    exam_id: str
    exam_slug: str
    version_number: int
    status: str
    title: str
    summary: str
    year: int | None
    difficulty: str
    duration_minutes: int
    primary_topic_id: str | None
    primary_topic_name: str | None
    updated_at: datetime
    questions: list[DraftQuestionResponse]
    import_context: DraftImportContextResponse | None = None


class DraftMetadataUpdate(BaseModel):
    expected_updated_at: datetime
    title: str | None = Field(default=None, max_length=255)
    summary: str | None = None
    year: int | None = None
    difficulty: str | None = Field(default=None, max_length=50)
    duration_minutes: int | None = Field(default=None, gt=0)
    primary_topic_id: str | None = None


class DraftQuestionOptionInput(BaseModel):
    id: str | None = None
    position: int = Field(gt=0, le=4)
    body: str
    is_correct: bool = False


class DraftQuestionStatementInput(BaseModel):
    id: str | None = None
    position: int = Field(gt=0, le=4)
    body: str
    is_correct: bool


class DraftQuestionInput(BaseModel):
    id: str | None = None
    position: int = Field(gt=0)
    part_number: int = Field(ge=1, le=2)
    part_position: int = Field(gt=0)
    question_type: str
    body: str
    source_text: str | None = None
    explanation: str = ""
    options: list[DraftQuestionOptionInput] = Field(default_factory=list)
    statements: list[DraftQuestionStatementInput] = Field(default_factory=list)


class DraftQuestionsUpdate(BaseModel):
    expected_updated_at: datetime
    questions: list[DraftQuestionInput]


class DraftPublishRequest(BaseModel):
    expected_updated_at: datetime
    acknowledge_warnings: bool = False


class DraftPublishResponse(BaseModel):
    exam_id: str
    exam_slug: str
    version_id: str
    published_at: datetime


class QuestionImageUploadRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)
    checksum_sha256: str = Field(min_length=64, max_length=64)


class QuestionImageUploadUrl(BaseModel):
    object_key: str
    bucket: str
    upload_url: str
    method: str
    headers: dict[str, str]
    expires_in_seconds: int


class QuestionImageConfirmRequest(BaseModel):
    object_key: str = Field(min_length=1, max_length=2048)
    bucket: str = Field(min_length=1, max_length=255)
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(gt=0)
    checksum_sha256: str = Field(min_length=64, max_length=64)


class QuestionImageLinkRequest(BaseModel):
    asset_id: str


class ArchiveExamResponse(BaseModel):
    exam_id: str
    exam_slug: str
    archived_version_id: str


class AdminTopicOption(BaseModel):
    id: str
    slug: str
    name: str


class AdminTopicPage(BaseModel):
    items: list[AdminTopicOption]
