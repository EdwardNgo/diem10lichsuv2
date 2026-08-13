import re

from diem10_api.parsers.types import (
    ParsedExamDraft,
    ParsedMcOption,
    ParsedMcQuestion,
    ParsedTfQuestion,
    ParsedTfStatement,
    ParserFinding,
)

_PART1_HEADER = re.compile(r"^PHẦN\s+I\b", re.IGNORECASE)
_PART2_HEADER = re.compile(r"^PHẦN\s+II\b", re.IGNORECASE)
_ANSWER_HEADER = re.compile(r"^ĐÁP\s+ÁN\b", re.IGNORECASE)
_QUESTION = re.compile(r"^Câu\s+(\d+)\.\s*(.*)$", re.IGNORECASE)
_MC_OPTION = re.compile(r"^([A-D])\.\s*(.+)$", re.IGNORECASE)
_TF_STATEMENT = re.compile(r"^([a-d])\)\s*(.+)$", re.IGNORECASE)
_MC_ANSWER = re.compile(r"^(\d+)\.\s*([A-D])\s*$", re.IGNORECASE)
_TF_ANSWER = re.compile(r"^(Đúng|Sai)\s*$", re.IGNORECASE)
_PART1_ANSWERS = re.compile(r"^Phần\s+I\b", re.IGNORECASE)
_PART1_ANSWERS_MARKER = re.compile(r"^Phần\s+I\s*$", re.IGNORECASE)
_PART2_ANSWERS = re.compile(r"^Phần\s+II\b", re.IGNORECASE)
_CITATION = re.compile(r"^\(.+\)$")
_COLUMN_HEADER = re.compile(r"^[a-d](?:\s+[a-d]){3}$", re.IGNORECASE)
_TF_ANSWER_QUESTION = re.compile(r"^Câu\s+(\d+)\.?\s*$", re.IGNORECASE)


def parse_manual_exam_lines(
    lines: list[str],
    *,
    fallback_title: str = "Bản nháp import",
) -> ParsedExamDraft:
    draft = ParsedExamDraft(
        title="",
        summary="",
        year=None,
        difficulty="Chưa phân loại",
        duration_minutes=50,
    )
    if not lines:
        draft.findings.append(
            ParserFinding(
                severity="error",
                field_path="_document",
                message="Tài liệu không có nội dung văn bản.",
            )
        )
        return draft

    state = "METADATA"
    title: str | None = None
    current_mc: ParsedMcQuestion | None = None
    current_tf: ParsedTfQuestion | None = None
    tf_source_lines: list[str] = []
    tf_collecting_source = False
    answer_section = ""
    tf_answer_index = 0
    tf_answer_values: list[bool] = []

    def flush_mc() -> None:
        nonlocal current_mc
        if current_mc is None:
            return
        if current_mc.body and len(current_mc.options) == 4:
            draft.part1_questions.append(current_mc)
        elif current_mc.body:
            draft.findings.append(
                ParserFinding(
                    severity="warning",
                    field_path=f"questions.part1[{current_mc.part_position}]",
                    message="Câu trắc nghiệm không đủ 4 phương án.",
                )
            )
        current_mc = None

    def flush_tf() -> None:
        nonlocal current_tf, tf_source_lines, tf_collecting_source
        if current_tf is None:
            return
        if tf_source_lines:
            current_tf.source_text = "\n".join(tf_source_lines).strip()
        if current_tf.body and len(current_tf.statements) == 4:
            draft.part2_questions.append(current_tf)
        elif current_tf.body:
            draft.findings.append(
                ParserFinding(
                    severity="error",
                    field_path=f"questions.part2[{current_tf.part_position}].statements",
                    message="Câu tư liệu không đủ 4 phát biểu.",
                    raw_value=str(len(current_tf.statements)),
                )
            )
        current_tf = None
        tf_source_lines = []
        tf_collecting_source = False

    for line in lines:
        if state in {"METADATA", "PART1", "PART2"} and _ANSWER_HEADER.match(line):
            flush_mc()
            flush_tf()
            state = "ANSWERS"
            answer_section = ""
            continue

        if state == "METADATA":
            if _PART1_HEADER.match(line):
                if title is None:
                    title = fallback_title
                draft.title = title
                state = "PART1"
                continue
            if _QUESTION.match(line):
                if title is None:
                    title = fallback_title
                draft.title = title
                state = "PART1"
            elif title is None:
                title = line
                continue
            else:
                continue

        if state == "PART1":
            if _PART2_HEADER.match(line):
                flush_mc()
                state = "PART2"
                continue
            question_match = _QUESTION.match(line)
            if question_match:
                flush_mc()
                part_position = int(question_match.group(1))
                current_mc = ParsedMcQuestion(
                    part_position=part_position,
                    body=question_match.group(2).strip(),
                )
                continue
            option_match = _MC_OPTION.match(line)
            if option_match and current_mc is not None:
                current_mc.options.append(
                    ParsedMcOption(
                        label=option_match.group(1).upper(),
                        body=option_match.group(2).strip(),
                    )
                )
            continue

        if state == "PART2":
            if _should_start_answers_part1(line, draft):
                flush_tf()
                state = "ANSWERS"
                answer_section = "PART1"
                continue
            mc_answer_match = _MC_ANSWER.match(line)
            if mc_answer_match and draft.part2_questions:
                flush_tf()
                state = "ANSWERS"
                answer_section = "PART1"
                question_number = int(mc_answer_match.group(1))
                letter = mc_answer_match.group(2).upper()
                matched = _apply_mc_answer(draft, question_number, letter)
                if not matched:
                    draft.findings.append(
                        ParserFinding(
                            severity="warning",
                            field_path=f"questions.part1[{question_number}].correct_option",
                            message="Không khớp câu hỏi với đáp án trích xuất.",
                            raw_value=letter,
                        )
                    )
                continue
            question_match = _QUESTION.match(line)
            if question_match:
                flush_tf()
                part_position = int(question_match.group(1))
                stem = question_match.group(2).strip()
                current_tf = ParsedTfQuestion(
                    part_position=part_position,
                    body=stem or "Cho đoạn tư liệu sau đây:",
                    source_text="",
                )
                tf_collecting_source = "tư liệu" in stem.lower()
                continue
            if current_tf is None:
                continue
            statement_match = _TF_STATEMENT.match(line)
            if statement_match:
                tf_collecting_source = False
                label = statement_match.group(1).lower()
                current_tf.statements.append(
                    ParsedTfStatement(
                        label=label,
                        body=statement_match.group(2).strip(),
                    )
                )
                continue
            if tf_collecting_source or (
                not current_tf.statements
                and (
                    line.startswith(('"', "("))
                    or _CITATION.match(line)
                )
            ):
                tf_source_lines.append(line)
                tf_collecting_source = True
            continue

        if state == "ANSWERS":
            if _PART1_ANSWERS.match(line):
                answer_section = "PART1"
                continue
            if _PART2_ANSWERS.match(line):
                answer_section = "PART2"
                tf_answer_index = 0
                continue
            if answer_section == "PART1":
                answer_match = _MC_ANSWER.match(line)
                if answer_match:
                    question_number = int(answer_match.group(1))
                    letter = answer_match.group(2).upper()
                    matched = _apply_mc_answer(draft, question_number, letter)
                    if not matched:
                        draft.findings.append(
                            ParserFinding(
                                severity="warning",
                                field_path=f"questions.part1[{question_number}].correct_option",
                                message="Không khớp câu hỏi với đáp án trích xuất.",
                                raw_value=letter,
                            )
                        )
                continue
            if answer_section == "PART2":
                if _COLUMN_HEADER.match(line.replace("/", " ")):
                    continue
                if line.lower() in {"a", "b", "c", "d"}:
                    continue
                question_match = _TF_ANSWER_QUESTION.match(line)
                if question_match:
                    tf_answer_index = int(question_match.group(1))
                    tf_answer_values = []
                    continue
                answer_match = _TF_ANSWER.match(line)
                if answer_match and tf_answer_index > 0:
                    tf_answer_values.append(answer_match.group(1).lower() == "đúng")
                    if len(tf_answer_values) == 4:
                        _apply_tf_answers(
                            draft,
                            tf_answer_index,
                            tf_answer_values,
                        )
                        tf_answer_values = []

    flush_mc()
    flush_tf()

    if not draft.title:
        draft.title = title or fallback_title

    _finalize_findings(draft)
    return draft


def _should_start_answers_part1(line: str, draft: ParsedExamDraft) -> bool:
    if not _PART1_ANSWERS_MARKER.match(line):
        return False
    return bool(draft.part1_questions or draft.part2_questions)


def _apply_mc_answer(
    draft: ParsedExamDraft,
    question_number: int,
    letter: str,
) -> bool:
    for question in draft.part1_questions:
        if question.part_position != question_number:
            continue
        found = False
        for option in question.options:
            option.is_correct = option.label == letter
            if option.is_correct:
                found = True
        if not found:
            draft.findings.append(
                ParserFinding(
                    severity="warning",
                    field_path=f"questions.part1[{question_number}].correct_option",
                    message="Đáp án đúng không khớp phương án đã trích xuất.",
                    raw_value=letter,
                )
            )
        return True
    return False


def _apply_tf_answers(
    draft: ParsedExamDraft,
    question_number: int,
    values: list[bool],
) -> None:
    for question in draft.part2_questions:
        if question.part_position != question_number:
            continue
        if len(question.statements) != 4:
            return
        for statement, is_correct in zip(question.statements, values, strict=True):
            statement.is_correct = is_correct
        return
    draft.findings.append(
        ParserFinding(
            severity="warning",
            field_path=f"questions.part2[{question_number}].answers",
            message="Không khớp câu tư liệu với đáp án trích xuất.",
        )
    )


def _finalize_findings(draft: ParsedExamDraft) -> None:
    if not draft.part1_questions and not draft.part2_questions:
        draft.findings.append(
            ParserFinding(
                severity="error",
                field_path="_document",
                message="Không nhận diện được cấu trúc đề thủ công.",
            )
        )
        return

    if len(draft.part1_questions) != 24:
        draft.findings.append(
            ParserFinding(
                severity="warning",
                field_path="questions.part1.count",
                message="Phần I không đủ 24 câu trắc nghiệm.",
                raw_value=str(len(draft.part1_questions)),
            )
        )
    if len(draft.part2_questions) != 4:
        draft.findings.append(
            ParserFinding(
                severity="warning",
                field_path="questions.part2.count",
                message="Phần II không đủ 4 câu tư liệu.",
                raw_value=str(len(draft.part2_questions)),
            )
        )

    for question in draft.part1_questions:
        if not any(option.is_correct for option in question.options):
            draft.findings.append(
                ParserFinding(
                    severity="warning",
                    field_path=f"questions.part1[{question.part_position}].correct_option",
                    message="Thiếu đáp án đúng cho câu trắc nghiệm.",
                )
            )
        draft.findings.append(
            ParserFinding(
                severity="warning",
                field_path=f"questions.part1[{question.part_position}].explanation",
                message="Thiếu lời giải; cần bổ sung trước khi xuất bản.",
            )
        )

    for question in draft.part2_questions:
        if not question.source_text:
            draft.findings.append(
                ParserFinding(
                    severity="warning",
                    field_path=f"questions.part2[{question.part_position}].source_text",
                    message="Thiếu hoặc không trích xuất được đoạn tư liệu.",
                )
            )
        if question.statements and any(
            statement.is_correct is None for statement in question.statements
        ):
            draft.findings.append(
                ParserFinding(
                    severity="warning",
                    field_path=f"questions.part2[{question.part_position}].answers",
                    message="Thiếu đáp án Đúng/Sai cho câu tư liệu.",
                )
            )
        draft.findings.append(
            ParserFinding(
                severity="warning",
                field_path=f"questions.part2[{question.part_position}].explanation",
                message="Thiếu lời giải; cần bổ sung trước khi xuất bản.",
            )
        )

    draft.findings.extend(
        [
            ParserFinding(
                severity="warning",
                field_path="metadata.summary",
                message="Thiếu mô tả đề; cần bổ sung trước khi xuất bản.",
            ),
            ParserFinding(
                severity="warning",
                field_path="metadata.topic",
                message="Chưa gán chủ đề; cần chọn trong editor.",
            ),
            ParserFinding(
                severity="warning",
                field_path="metadata.year",
                message="Chưa xác định năm đề; cần bổ sung trong editor.",
            ),
        ]
    )
