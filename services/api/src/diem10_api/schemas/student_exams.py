from typing import Literal

from pydantic import BaseModel

CompletionStatus = Literal["not_started", "in_progress", "completed"]


class StudentExam(BaseModel):
    slug: str
    title: str
    summary: str
    topic: str
    year: int | None
    difficulty: str
    duration_minutes: int
    question_count: int
    completion_status: CompletionStatus


class StudentExamPage(BaseModel):
    items: list[StudentExam]
    page: int
    page_size: int
    total: int


class StudentExamOption(BaseModel):
    id: str
    position: int
    body: str


class StudentExamQuestion(BaseModel):
    id: str
    position: int
    part_number: int
    part_position: int
    question_type: str
    body: str
    source_text: str | None
    options: list[StudentExamOption]
    statements: list[StudentExamOption]


class StudentActiveAttempt(BaseModel):
    id: str
    remaining_seconds: int


class StudentExamDetail(BaseModel):
    slug: str
    title: str
    summary: str
    topics: list[str]
    primary_topic: str
    year: int | None
    difficulty: str
    duration_minutes: int
    question_count: int
    completion_status: CompletionStatus
    active_attempt: StudentActiveAttempt | None
    questions: list[StudentExamQuestion]
