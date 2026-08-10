from pydantic import BaseModel


class PublicExam(BaseModel):
    slug: str
    title: str
    summary: str
    topic: str
    year: int | None
    difficulty: str
    duration_minutes: int
    question_count: int


class PublicExamPage(BaseModel):
    items: list[PublicExam]
    page: int
    page_size: int
    total: int


class PublicExamTopicFilter(BaseModel):
    slug: str
    name: str


class PublicExamFilters(BaseModel):
    topics: list[PublicExamTopicFilter]
    years: list[int]
    difficulties: list[str]
