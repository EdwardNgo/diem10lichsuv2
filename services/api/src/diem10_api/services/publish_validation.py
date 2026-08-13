from dataclasses import dataclass, field
from typing import Literal

from diem10_api.models import (
    ExamVersion,
    ImportFinding,
    Question,
    QuestionOption,
    QuestionStatement,
    Topic,
)

ValidationSeverity = Literal["error", "warning"]
UNSET_DIFFICULTY = "Chưa phân loại"
ALLOWED_DIFFICULTIES = frozenset({"Dễ", "Trung bình", "Khó"})


@dataclass(frozen=True)
class ValidationIssue:
    severity: ValidationSeverity
    field_path: str
    message: str
    question_id: str | None = None
    part_number: int | None = None
    part_position: int | None = None


@dataclass
class ValidationResult:
    valid: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)


def validate_draft_for_publish(
    version: ExamVersion,
    *,
    questions: list[Question],
    options_by_question: dict[object, list[QuestionOption]],
    statements_by_question: dict[object, list[QuestionStatement]],
    primary_topic: Topic | None,
    unresolved_findings: list[ImportFinding],
) -> ValidationResult:
    result = ValidationResult(valid=True)
    _validate_metadata(version, primary_topic, result)
    _validate_questions(questions, options_by_question, statements_by_question, result)
    _validate_import_findings(unresolved_findings, result)
    result.valid = result.error_count == 0
    return result


def _add_issue(
    result: ValidationResult,
    *,
    severity: ValidationSeverity,
    field_path: str,
    message: str,
    question_id: object | None = None,
    part_number: int | None = None,
    part_position: int | None = None,
) -> None:
    issue = ValidationIssue(
        severity=severity,
        field_path=field_path,
        message=message,
        question_id=str(question_id) if question_id is not None else None,
        part_number=part_number,
        part_position=part_position,
    )
    if severity == "error":
        result.errors.append(issue)
    else:
        result.warnings.append(issue)


def _validate_metadata(
    version: ExamVersion,
    primary_topic: Topic | None,
    result: ValidationResult,
) -> None:
    if not version.title.strip():
        _add_issue(
            result,
            severity="error",
            field_path="metadata.title",
            message="Tiêu đề không được để trống",
        )
    if not version.summary.strip():
        _add_issue(
            result,
            severity="error",
            field_path="metadata.summary",
            message="Mô tả không được để trống",
        )
    if version.duration_minutes <= 0:
        _add_issue(
            result,
            severity="error",
            field_path="metadata.duration_minutes",
            message="Thời lượng phải lớn hơn 0",
        )
    difficulty = version.difficulty.strip()
    if not difficulty or difficulty == UNSET_DIFFICULTY:
        _add_issue(
            result,
            severity="error",
            field_path="metadata.difficulty",
            message="Mức độ phải được chọn",
        )
    elif difficulty not in ALLOWED_DIFFICULTIES:
        _add_issue(
            result,
            severity="error",
            field_path="metadata.difficulty",
            message="Mức độ phải là Dễ, Trung bình hoặc Khó",
        )
    if primary_topic is None or not primary_topic.is_active:
        _add_issue(
            result,
            severity="error",
            field_path="metadata.primary_topic_id",
            message="Phải chọn chủ đề chính",
        )
    if version.year is None:
        _add_issue(
            result,
            severity="warning",
            field_path="metadata.year",
            message="Chưa có năm thi",
        )


def _validate_questions(
    questions: list[Question],
    options_by_question: dict[object, list[QuestionOption]],
    statements_by_question: dict[object, list[QuestionStatement]],
    result: ValidationResult,
) -> None:
    part1 = [question for question in questions if question.part_number == 1]
    part2 = [question for question in questions if question.part_number == 2]

    if len(part1) != 24:
        _add_issue(
            result,
            severity="error",
            field_path="questions.part1.count",
            message=f"Phần I phải có đúng 24 câu (hiện có {len(part1)})",
        )
    if len(part2) != 4:
        _add_issue(
            result,
            severity="error",
            field_path="questions.part2.count",
            message=f"Phần II phải có đúng 4 câu (hiện có {len(part2)})",
        )

    for question in part1:
        _validate_mc_question(
            question,
            options_by_question.get(question.id, []),
            result,
        )
    for question in part2:
        _validate_tf_question(
            question,
            statements_by_question.get(question.id, []),
            result,
        )


def _validate_mc_question(
    question: Question,
    options: list[QuestionOption],
    result: ValidationResult,
) -> None:
    prefix = f"questions.part1[{question.part_position}]"
    if question.question_type != "multiple_choice":
        _add_issue(
            result,
            severity="error",
            field_path=f"{prefix}.question_type",
            message="Câu Phần I phải là trắc nghiệm ABCD",
            question_id=question.id,
            part_number=1,
            part_position=question.part_position,
        )
        return
    if not question.body.strip():
        _add_issue(
            result,
            severity="error",
            field_path=f"{prefix}.body",
            message="Nội dung câu hỏi không được để trống",
            question_id=question.id,
            part_number=1,
            part_position=question.part_position,
        )
    if len(options) != 4:
        _add_issue(
            result,
            severity="error",
            field_path=f"{prefix}.options.count",
            message=f"Phải có đúng 4 lựa chọn (hiện có {len(options)})",
            question_id=question.id,
            part_number=1,
            part_position=question.part_position,
        )
    correct_count = sum(1 for option in options if option.is_correct)
    if correct_count != 1:
        _add_issue(
            result,
            severity="error",
            field_path=f"{prefix}.correct_option",
            message="Phải chọn đúng một đáp án đúng",
            question_id=question.id,
            part_number=1,
            part_position=question.part_position,
        )
    for option in options:
        if not option.body.strip():
            _add_issue(
                result,
                severity="error",
                field_path=f"{prefix}.options[{option.position}]",
                message="Nội dung lựa chọn không được để trống",
                question_id=question.id,
                part_number=1,
                part_position=question.part_position,
            )
    if not question.explanation.strip():
        _add_issue(
            result,
            severity="warning",
            field_path=f"{prefix}.explanation",
            message="Chưa có lời giải",
            question_id=question.id,
            part_number=1,
            part_position=question.part_position,
        )


def _validate_tf_question(
    question: Question,
    statements: list[QuestionStatement],
    result: ValidationResult,
) -> None:
    prefix = f"questions.part2[{question.part_position}]"
    if question.question_type != "true_false_group":
        _add_issue(
            result,
            severity="error",
            field_path=f"{prefix}.question_type",
            message="Câu Phần II phải là câu tư liệu Đúng/Sai",
            question_id=question.id,
            part_number=2,
            part_position=question.part_position,
        )
        return
    if not (question.source_text or "").strip():
        _add_issue(
            result,
            severity="error",
            field_path=f"{prefix}.source_text",
            message="Phải có đoạn tư liệu",
            question_id=question.id,
            part_number=2,
            part_position=question.part_position,
        )
    if len(statements) != 4:
        _add_issue(
            result,
            severity="error",
            field_path=f"{prefix}.statements.count",
            message=f"Phải có đúng 4 phát biểu (hiện có {len(statements)})",
            question_id=question.id,
            part_number=2,
            part_position=question.part_position,
        )
    for statement in statements:
        if not statement.body.strip():
            _add_issue(
                result,
                severity="error",
                field_path=f"{prefix}.statements[{statement.position}]",
                message="Nội dung phát biểu không được để trống",
                question_id=question.id,
                part_number=2,
                part_position=question.part_position,
            )
    if not question.explanation.strip():
        _add_issue(
            result,
            severity="warning",
            field_path=f"{prefix}.explanation",
            message="Chưa có lời giải",
            question_id=question.id,
            part_number=2,
            part_position=question.part_position,
        )


def _validate_import_findings(
    unresolved_findings: list[ImportFinding],
    result: ValidationResult,
) -> None:
    for finding in unresolved_findings:
        if finding.resolved_at is not None:
            continue
        severity: ValidationSeverity = (
            "error" if finding.severity == "error" else "warning"
        )
        _add_issue(
            result,
            severity=severity,
            field_path=finding.field_path,
            message=finding.message,
        )
