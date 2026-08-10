from pathlib import Path

from diem10_api.parsers import parse_source
from diem10_api.parsers.manual_exam import parse_manual_exam_lines

REPO_ROOT = Path(__file__).resolve().parents[4]
MANUAL_EXAM_FIXTURE = next((REPO_ROOT / "parser-source/manual-exams").glob("*.docx"))


def test_manual_exam_fixture_parses_full_structure() -> None:
    content = MANUAL_EXAM_FIXTURE.read_bytes()
    draft = parse_source(
        content,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert draft.title == "ĐỀ SỐ 1"
    assert len(draft.part1_questions) == 24
    assert len(draft.part2_questions) == 4
    assert draft.is_safe_to_persist
    assert not draft.has_document_error

    first = draft.part1_questions[0]
    assert first.part_position == 1
    assert len(first.options) == 4
    assert first.options[0].is_correct is True
    assert first.options[1].is_correct is False

    last = draft.part1_questions[23]
    assert last.part_position == 24
    assert last.options[1].is_correct is True

    tf_first = draft.part2_questions[0]
    assert tf_first.part_position == 1
    assert tf_first.source_text.startswith('"')
    assert [statement.is_correct for statement in tf_first.statements] == [
        True,
        False,
        False,
        True,
    ]

    assert any(
        finding.field_path == "metadata.topic" and finding.severity == "warning"
        for finding in draft.findings
    )
    assert any(
        finding.field_path.endswith(".explanation") for finding in draft.findings
    )


def test_empty_document_fails_safe() -> None:
    draft = parse_manual_exam_lines([])
    assert draft.is_safe_to_persist is False
    assert draft.has_document_error
