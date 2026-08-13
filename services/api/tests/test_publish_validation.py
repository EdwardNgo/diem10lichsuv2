import uuid

from diem10_api.models import (
    ExamVersion,
    Question,
    QuestionOption,
    QuestionStatement,
    Topic,
)
from diem10_api.services.publish_validation import validate_draft_for_publish


def _mc_question(part_position: int) -> Question:
    return Question(
        exam_version_id="00000000-0000-0000-0000-000000000001",  # type: ignore[arg-type]
        position=part_position,
        part_number=1,
        part_position=part_position,
        question_type="multiple_choice",
        body=f"Câu {part_position}",
        source_text=None,
        explanation="",
    )


def _tf_question(part_position: int) -> Question:
    return Question(
        exam_version_id="00000000-0000-0000-0000-000000000001",  # type: ignore[arg-type]
        position=24 + part_position,
        part_number=2,
        part_position=part_position,
        question_type="true_false_group",
        body=f"Câu tư liệu {part_position}",
        source_text="Đoạn tư liệu mẫu",
        explanation="",
    )


def _mc_options(question_id: object) -> list[QuestionOption]:
    return [
        QuestionOption(
            question_id=question_id,  # type: ignore[arg-type]
            position=1,
            body="A",
            is_correct=True,
        ),
        QuestionOption(
            question_id=question_id,  # type: ignore[arg-type]
            position=2,
            body="B",
            is_correct=False,
        ),
        QuestionOption(
            question_id=question_id,  # type: ignore[arg-type]
            position=3,
            body="C",
            is_correct=False,
        ),
        QuestionOption(
            question_id=question_id,  # type: ignore[arg-type]
            position=4,
            body="D",
            is_correct=False,
        ),
    ]


def _tf_statements(question_id: object) -> list[QuestionStatement]:
    return [
        QuestionStatement(
            question_id=question_id,  # type: ignore[arg-type]
            position=index,
            body=f"Phát biểu {index}",
            is_correct=index % 2 == 1,
        )
        for index in range(1, 5)
    ]


def _valid_version() -> ExamVersion:
    return ExamVersion(
        exam_id="00000000-0000-0000-0000-000000000002",  # type: ignore[arg-type]
        version_number=1,
        status="draft",
        title="Đề kiểm tra",
        summary="Mô tả đề",
        year=2026,
        difficulty="Trung bình",
        duration_minutes=50,
        published_at=None,
    )


def _valid_topic() -> Topic:
    return Topic(
        id="00000000-0000-0000-0000-000000000003",  # type: ignore[arg-type]
        slug="lich-su-viet-nam",
        name="Lịch sử Việt Nam",
        sort_order=1,
        is_active=True,
    )


def test_valid_draft_passes_with_explanation_warnings_only() -> None:
    questions = [_mc_question(index) for index in range(1, 25)] + [
        _tf_question(index) for index in range(1, 5)
    ]
    for index, question in enumerate(questions, start=1):
        question.id = uuid.UUID(int=index)  # type: ignore[misc]
    options_by_question = {
        question.id: _mc_options(question.id) for question in questions[:24]
    }
    statements_by_question = {
        question.id: _tf_statements(question.id) for question in questions[24:]
    }

    result = validate_draft_for_publish(
        _valid_version(),
        questions=questions,
        options_by_question=options_by_question,
        statements_by_question=statements_by_question,
        primary_topic=_valid_topic(),
        unresolved_findings=[],
    )
    assert result.valid is True
    assert result.error_count == 0
    assert result.warning_count == 28


def test_missing_topic_and_summary_are_errors() -> None:
    version = _valid_version()
    version.summary = ""
    questions = [_mc_question(1)]
    question_id = 1
    questions[0].id = question_id  # type: ignore[misc]
    result = validate_draft_for_publish(
        version,
        questions=questions,
        options_by_question={question_id: _mc_options(question_id)},
        statements_by_question={},
        primary_topic=None,
        unresolved_findings=[],
    )
    assert result.valid is False
    paths = {issue.field_path for issue in result.errors}
    assert "metadata.summary" in paths
    assert "metadata.primary_topic_id" in paths
    assert "questions.part1.count" in paths


def test_mc_question_requires_single_correct_option() -> None:
    questions = [_mc_question(1)]
    question_id = 1
    questions[0].id = question_id  # type: ignore[misc]
    options = _mc_options(question_id)
    options[0].is_correct = True
    options[1].is_correct = True
    result = validate_draft_for_publish(
        _valid_version(),
        questions=questions,
        options_by_question={question_id: options},
        statements_by_question={},
        primary_topic=_valid_topic(),
        unresolved_findings=[],
    )
    assert any(
        issue.field_path == "questions.part1[1].correct_option"
        for issue in result.errors
    )


def test_unresolved_import_error_blocks_publish() -> None:
    from diem10_api.models import ImportFinding

    finding = ImportFinding(
        import_job_id="00000000-0000-0000-0000-000000000004",  # type: ignore[arg-type]
        severity="error",
        field_path="_document",
        message="Lỗi parser",
    )
    questions = [_mc_question(index) for index in range(1, 25)] + [
        _tf_question(index) for index in range(1, 5)
    ]
    for question in questions:
        question.id = question.part_position  # type: ignore[misc]
    options_by_question = {
        question.id: _mc_options(question.id) for question in questions[:24]
    }
    statements_by_question = {
        question.id: _tf_statements(question.id) for question in questions[24:]
    }
    result = validate_draft_for_publish(
        _valid_version(),
        questions=questions,
        options_by_question=options_by_question,
        statements_by_question=statements_by_question,
        primary_topic=_valid_topic(),
        unresolved_findings=[finding],
    )
    assert result.valid is False
    assert any(issue.severity == "error" for issue in result.errors)
