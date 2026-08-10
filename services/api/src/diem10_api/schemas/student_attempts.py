import uuid
from datetime import datetime

from pydantic import BaseModel


class AttemptOption(BaseModel):
    id: str
    position: int
    body: str


class AttemptQuestion(BaseModel):
    id: str
    position: int
    part_number: int
    part_position: int
    question_type: str
    body: str
    source_text: str | None
    options: list[AttemptOption]
    statements: list[AttemptOption]


class AttemptSavedStatementAnswer(BaseModel):
    statement_id: str
    selected_value: bool | None


class AttemptSavedAnswer(BaseModel):
    question_id: str
    selected_option_id: str | None
    statement_answers: list[AttemptSavedStatementAnswer]
    is_marked_for_review: bool
    updated_at: datetime


class AttemptDetail(BaseModel):
    id: str
    slug: str
    title: str
    summary: str
    primary_topic: str
    status: str
    server_now: datetime
    started_at: datetime
    expires_at: datetime
    paused_at: datetime | None
    duration_minutes: int
    question_count: int
    answered_count: int
    questions: list[AttemptQuestion]
    answers: list[AttemptSavedAnswer]


class SaveStatementAnswerRequest(BaseModel):
    statement_id: uuid.UUID
    selected_value: bool | None = None


class SaveAttemptAnswerRequest(BaseModel):
    selected_option_id: uuid.UUID | None = None
    statement_answers: list[SaveStatementAnswerRequest] | None = None
    is_marked_for_review: bool = False


class SavedAttemptAnswer(BaseModel):
    question_id: str
    selected_option_id: str | None
    statement_answers: list[AttemptSavedStatementAnswer]
    is_marked_for_review: bool
    updated_at: datetime


class AttemptResultStatement(BaseModel):
    id: str
    position: int
    body: str
    selected_value: bool | None
    correct_value: bool
    is_correct: bool


class AttemptResultQuestion(BaseModel):
    id: str
    position: int
    part_number: int
    part_position: int
    question_type: str
    body: str
    source_text: str | None
    explanation: str
    selected_option_id: str | None
    correct_option_id: str | None
    options: list[AttemptOption]
    statements: list[AttemptResultStatement]
    correct_count: int
    total_count: int
    earned_score: float
    max_score: float


class AttemptResultResponse(BaseModel):
    attempt_id: str
    slug: str
    title: str
    attempt_number: int
    status: str
    score: float
    part1_score: float
    part2_score: float
    correct_count: int
    incorrect_count: int
    unanswered_count: int
    started_at: datetime
    submitted_at: datetime | None
    graded_at: datetime
    can_retry: bool
    questions: list[AttemptResultQuestion]


class HistoryAttemptSummary(BaseModel):
    attempt_id: str
    attempt_number: int
    status: str
    score: float
    correct_count: int
    incorrect_count: int
    unanswered_count: int
    submitted_at: datetime | None
    graded_at: datetime


class HistoryExamGroup(BaseModel):
    slug: str
    title: str
    attempt_count: int
    best_score: float
    latest_score: float
    latest_submitted_at: datetime | None
    can_retry: bool
    attempts: list[HistoryAttemptSummary]


class AttemptHistoryPage(BaseModel):
    items: list[HistoryExamGroup]
    page: int
    page_size: int
    total: int
