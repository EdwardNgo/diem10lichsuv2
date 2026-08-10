from dataclasses import dataclass, field
from typing import Literal

FindingSeverity = Literal["warning", "error"]


@dataclass(frozen=True)
class ParserFinding:
    severity: FindingSeverity
    field_path: str
    message: str
    raw_value: str | None = None


@dataclass
class ParsedMcOption:
    label: str
    body: str
    is_correct: bool = False


@dataclass
class ParsedMcQuestion:
    part_position: int
    body: str
    options: list[ParsedMcOption] = field(default_factory=list)
    explanation: str = ""


@dataclass
class ParsedTfStatement:
    label: str
    body: str
    is_correct: bool | None = None


@dataclass
class ParsedTfQuestion:
    part_position: int
    body: str
    source_text: str
    statements: list[ParsedTfStatement] = field(default_factory=list)
    explanation: str = ""


@dataclass
class ParsedExamDraft:
    title: str
    summary: str
    year: int | None
    difficulty: str
    duration_minutes: int
    part1_questions: list[ParsedMcQuestion] = field(default_factory=list)
    part2_questions: list[ParsedTfQuestion] = field(default_factory=list)
    findings: list[ParserFinding] = field(default_factory=list)

    @property
    def has_document_error(self) -> bool:
        return any(
            finding.severity == "error" and finding.field_path == "_document"
            for finding in self.findings
        )

    @property
    def is_safe_to_persist(self) -> bool:
        total = len(self.part1_questions) + len(self.part2_questions)
        if total == 0 or self.has_document_error:
            return False
        return not any(
            finding.severity == "error"
            for finding in self.findings
            if finding.field_path != "_document"
        )
