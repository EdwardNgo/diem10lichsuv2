import uuid
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from diem10_api.models import (
    Attempt,
    AttemptAnswer,
    AttemptQuestionResult,
    AttemptResult,
    AttemptStatementAnswer,
    Exam,
    ExamVersion,
    ExamVersionTopic,
    Question,
    QuestionOption,
    QuestionStatement,
    Topic,
    User,
)
from diem10_api.schemas.student_attempts import (
    AttemptDetail,
    AttemptHistoryPage,
    AttemptOption,
    AttemptQuestion,
    AttemptResultQuestion,
    AttemptResultResponse,
    AttemptResultStatement,
    AttemptSavedAnswer,
    AttemptSavedStatementAnswer,
    HistoryAttemptSummary,
    HistoryExamGroup,
    SaveAttemptAnswerRequest,
    SavedAttemptAnswer,
)

MCQ_POINT = Decimal("0.25")
TF_POINT_BY_CORRECT_COUNT = {
    0: Decimal("0.00"),
    1: Decimal("0.10"),
    2: Decimal("0.25"),
    3: Decimal("0.50"),
    4: Decimal("1.00"),
}
TWO_PLACES = Decimal("0.01")


def _now() -> datetime:
    return datetime.now(UTC)


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _is_attempt_expired(attempt: Attempt, now: datetime | None = None) -> bool:
    return (
        attempt.status == "in_progress"
        and attempt.paused_at is None
        and _ensure_aware(attempt.expires_at) <= (now or _now())
    )


def _resume_attempt(attempt: Attempt, now: datetime | None = None) -> bool:
    if attempt.status != "in_progress" or attempt.paused_at is None:
        return False
    resumed_at = now or _now()
    paused_at = _ensure_aware(attempt.paused_at)
    paused_duration = max(timedelta(0), resumed_at - paused_at)
    attempt.expires_at = _ensure_aware(attempt.expires_at) + paused_duration
    attempt.paused_at = None
    return True


def _score(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _as_float(value: Decimal) -> float:
    return float(_score(value))


def _published_exam_version_for_slug(
    session: Session,
    slug: str,
) -> tuple[Exam, ExamVersion] | None:
    row = session.execute(
        select(Exam, ExamVersion)
        .join(ExamVersion, ExamVersion.exam_id == Exam.id)
        .where(Exam.slug == slug)
        .where(Exam.deleted_at.is_(None))
        .where(ExamVersion.status == "published")
    ).one_or_none()
    if row is None:
        return None
    exam, version = row
    return exam, version


def _has_published_version_for_exam(
    session: Session,
    exam_id: uuid.UUID,
) -> bool:
    return (
        session.scalar(
            select(func.count())
            .select_from(ExamVersion)
            .join(Exam, Exam.id == ExamVersion.exam_id)
            .where(Exam.id == exam_id)
            .where(Exam.deleted_at.is_(None))
            .where(ExamVersion.status == "published")
        )
        or 0
    ) > 0


def _owned_attempt(
    session: Session,
    current_user: User,
    attempt_id: uuid.UUID,
) -> Attempt:
    attempt = session.scalar(
        select(Attempt)
        .where(Attempt.id == attempt_id)
        .where(Attempt.user_id == current_user.id)
    )
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return attempt


def _open_attempt_for_version(
    session: Session,
    current_user: User,
    version: ExamVersion,
) -> Attempt | None:
    return session.scalar(
        select(Attempt)
        .where(Attempt.user_id == current_user.id)
        .where(Attempt.exam_version_id == version.id)
        .where(Attempt.status == "in_progress")
        .order_by(Attempt.started_at.desc())
    )


def _next_attempt_number(
    session: Session,
    current_user: User,
    version: ExamVersion,
) -> int:
    existing_count = (
        session.scalar(
            select(func.count())
            .select_from(Attempt)
            .where(Attempt.user_id == current_user.id)
            .where(Attempt.exam_version_id == version.id)
        )
        or 0
    )
    return existing_count + 1


def _questions_for_version(session: Session, version_id: uuid.UUID) -> list[Question]:
    return list(
        session.scalars(
            select(Question)
            .where(Question.exam_version_id == version_id)
            .order_by(
                Question.part_number.asc(),
                Question.part_position.asc(),
                Question.position.asc(),
            )
        ).all()
    )


def _options_by_question_id(
    session: Session,
    question_ids: list[uuid.UUID],
) -> dict[uuid.UUID, list[QuestionOption]]:
    options_by_question_id: dict[uuid.UUID, list[QuestionOption]] = {
        question_id: [] for question_id in question_ids
    }
    if not question_ids:
        return options_by_question_id
    options = session.scalars(
        select(QuestionOption)
        .where(QuestionOption.question_id.in_(question_ids))
        .order_by(QuestionOption.question_id.asc(), QuestionOption.position.asc())
    ).all()
    for option in options:
        options_by_question_id[option.question_id].append(option)
    return options_by_question_id


def _statements_by_question_id(
    session: Session,
    question_ids: list[uuid.UUID],
) -> dict[uuid.UUID, list[QuestionStatement]]:
    statements_by_question_id: dict[uuid.UUID, list[QuestionStatement]] = {
        question_id: [] for question_id in question_ids
    }
    if not question_ids:
        return statements_by_question_id
    statements = session.scalars(
        select(QuestionStatement)
        .where(QuestionStatement.question_id.in_(question_ids))
        .order_by(
            QuestionStatement.question_id.asc(),
            QuestionStatement.position.asc(),
        )
    ).all()
    for statement in statements:
        statements_by_question_id[statement.question_id].append(statement)
    return statements_by_question_id


def _answer_for_question(
    session: Session,
    attempt: Attempt,
    question: Question,
) -> AttemptAnswer:
    answer = session.get(
        AttemptAnswer,
        {"attempt_id": attempt.id, "question_id": question.id},
    )
    if answer is None:
        answer = AttemptAnswer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_option_id=None,
            is_marked_for_review=False,
        )
        session.add(answer)
        session.flush()
    return answer


def _saved_statement_answers(
    session: Session,
    attempt: Attempt,
    question_id: uuid.UUID | None = None,
) -> list[AttemptStatementAnswer]:
    query = select(AttemptStatementAnswer).where(
        AttemptStatementAnswer.attempt_id == attempt.id
    )
    if question_id is not None:
        query = query.where(AttemptStatementAnswer.question_id == question_id)
    return list(
        session.scalars(query.order_by(AttemptStatementAnswer.updated_at.asc())).all()
    )


def _attempt_detail(
    session: Session,
    current_user: User,
    attempt: Attempt,
) -> AttemptDetail:
    if _is_attempt_expired(attempt):
        _finalize_attempt(session, attempt, "expired_and_submitted")
        session.commit()
        session.refresh(attempt)

    row = session.execute(
        select(Exam, ExamVersion, Topic)
        .join(ExamVersion, ExamVersion.exam_id == Exam.id)
        .join(ExamVersionTopic, ExamVersionTopic.exam_version_id == ExamVersion.id)
        .join(Topic, Topic.id == ExamVersionTopic.topic_id)
        .where(ExamVersion.id == attempt.exam_version_id)
        .where(ExamVersionTopic.is_primary.is_(True))
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    exam, version, primary_topic = row
    questions = _questions_for_version(session, version.id)
    question_ids = [question.id for question in questions]
    options_by_question_id = _options_by_question_id(session, question_ids)
    statements_by_question_id = _statements_by_question_id(session, question_ids)
    answers = list(
        session.scalars(
            select(AttemptAnswer)
            .where(AttemptAnswer.attempt_id == attempt.id)
            .order_by(AttemptAnswer.updated_at.asc())
        ).all()
    )
    statement_answers = _saved_statement_answers(session, attempt)
    statement_answers_by_question_id: dict[uuid.UUID, list[AttemptStatementAnswer]] = {
        question.id: [] for question in questions
    }
    for statement_answer in statement_answers:
        statement_answers_by_question_id[statement_answer.question_id].append(
            statement_answer
        )

    saved_answers = [
        AttemptSavedAnswer(
            question_id=str(answer.question_id),
            selected_option_id=(
                str(answer.selected_option_id)
                if answer.selected_option_id is not None
                else None
            ),
            statement_answers=[
                AttemptSavedStatementAnswer(
                    statement_id=str(statement_answer.statement_id),
                    selected_value=statement_answer.selected_value,
                )
                for statement_answer in statement_answers_by_question_id.get(
                    answer.question_id, []
                )
            ],
            is_marked_for_review=answer.is_marked_for_review,
            updated_at=answer.updated_at,
        )
        for answer in answers
    ]
    answers_by_question_id = {answer.question_id: answer for answer in answers}
    statement_answer_values = {
        statement_answer.statement_id: statement_answer.selected_value
        for statement_answer in statement_answers
    }
    answered_count = 0
    for question in questions:
        if question.question_type == "multiple_choice":
            answer = answers_by_question_id.get(question.id)
            if answer is not None and answer.selected_option_id is not None:
                answered_count += 1
            continue
        statements = statements_by_question_id[question.id]
        if statements and all(
            statement_answer_values.get(statement.id) is not None
            for statement in statements
        ):
            answered_count += 1

    if attempt.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return AttemptDetail(
        id=str(attempt.id),
        slug=exam.slug,
        title=version.title,
        summary=version.summary,
        primary_topic=primary_topic.name,
        status=attempt.status,
        server_now=_now(),
        started_at=attempt.started_at,
        expires_at=attempt.expires_at,
        paused_at=attempt.paused_at,
        duration_minutes=version.duration_minutes,
        question_count=len(questions),
        answered_count=answered_count,
        questions=[
            AttemptQuestion(
                id=str(question.id),
                position=question.position,
                part_number=question.part_number,
                part_position=question.part_position,
                question_type=question.question_type,
                body=question.body,
                source_text=question.source_text,
                options=[
                    AttemptOption(
                        id=str(option.id),
                        position=option.position,
                        body=option.body,
                    )
                    for option in options_by_question_id[question.id]
                ],
                statements=[
                    AttemptOption(
                        id=str(statement.id),
                        position=statement.position,
                        body=statement.body,
                    )
                    for statement in statements_by_question_id[question.id]
                ],
            )
            for question in questions
        ],
        answers=saved_answers,
    )


def _finalize_attempt(
    session: Session,
    attempt: Attempt,
    final_status: str,
) -> AttemptResult:
    existing_result = session.get(AttemptResult, attempt.id)
    if existing_result is not None:
        return existing_result

    questions = _questions_for_version(session, attempt.exam_version_id)
    question_ids = [question.id for question in questions]
    options_by_question_id = _options_by_question_id(session, question_ids)
    statements_by_question_id = _statements_by_question_id(session, question_ids)
    answers = list(
        session.scalars(
            select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt.id)
        ).all()
    )
    answers_by_question_id = {answer.question_id: answer for answer in answers}
    statement_answers = _saved_statement_answers(session, attempt)
    statement_answer_values = {
        statement_answer.statement_id: statement_answer.selected_value
        for statement_answer in statement_answers
    }

    part1_score = Decimal("0.00")
    part2_score = Decimal("0.00")
    correct_count = 0
    incorrect_count = 0
    unanswered_count = 0
    for question in questions:
        if question.question_type == "multiple_choice":
            answer = answers_by_question_id.get(question.id)
            correct_option = next(
                (
                    option
                    for option in options_by_question_id[question.id]
                    if option.is_correct
                ),
                None,
            )
            selected_option_id = (
                answer.selected_option_id if answer is not None else None
            )
            is_correct = (
                correct_option is not None and selected_option_id == correct_option.id
            )
            earned_score = MCQ_POINT if is_correct else Decimal("0.00")
            part1_score += earned_score
            if selected_option_id is None:
                unanswered_count += 1
            elif is_correct:
                correct_count += 1
            else:
                incorrect_count += 1
            session.add(
                AttemptQuestionResult(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    part_number=question.part_number,
                    correct_count=1 if is_correct else 0,
                    total_count=1,
                    earned_score=_score(earned_score),
                    max_score=MCQ_POINT,
                )
            )
            continue

        statements = statements_by_question_id[question.id]
        statement_correct_count = sum(
            1
            for statement in statements
            if statement_answer_values.get(statement.id) is not None
            and statement_answer_values[statement.id] == statement.is_correct
        )
        selected_statement_count = sum(
            1
            for statement in statements
            if statement_answer_values.get(statement.id) is not None
        )
        earned_score = TF_POINT_BY_CORRECT_COUNT.get(
            statement_correct_count,
            Decimal("0.00"),
        )
        part2_score += earned_score
        if selected_statement_count < len(statements):
            unanswered_count += 1
        elif statement_correct_count == len(statements):
            correct_count += 1
        else:
            incorrect_count += 1
        session.add(
            AttemptQuestionResult(
                attempt_id=attempt.id,
                question_id=question.id,
                part_number=question.part_number,
                correct_count=statement_correct_count,
                total_count=len(statements),
                earned_score=_score(earned_score),
                max_score=Decimal("1.00"),
            )
        )

    now = _now()
    attempt.status = final_status
    attempt.paused_at = None
    attempt.submitted_at = now
    result = AttemptResult(
        attempt_id=attempt.id,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        unanswered_count=unanswered_count,
        part1_score=_score(part1_score),
        part2_score=_score(part2_score),
        score=_score(part1_score + part2_score),
        graded_at=now,
    )
    session.add(result)
    session.flush()
    return result


def _result_response(
    session: Session,
    attempt: Attempt,
    result: AttemptResult,
) -> AttemptResultResponse:
    row = session.execute(
        select(Exam, ExamVersion)
        .join(ExamVersion, ExamVersion.exam_id == Exam.id)
        .where(ExamVersion.id == attempt.exam_version_id)
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    exam, version = row
    questions = _questions_for_version(session, attempt.exam_version_id)
    question_ids = [question.id for question in questions]
    options_by_question_id = _options_by_question_id(session, question_ids)
    statements_by_question_id = _statements_by_question_id(session, question_ids)
    answers = list(
        session.scalars(
            select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt.id)
        ).all()
    )
    answers_by_question_id = {answer.question_id: answer for answer in answers}
    statement_answers = _saved_statement_answers(session, attempt)
    statement_answer_values = {
        statement_answer.statement_id: statement_answer.selected_value
        for statement_answer in statement_answers
    }
    question_results = list(
        session.scalars(
            select(AttemptQuestionResult).where(
                AttemptQuestionResult.attempt_id == attempt.id
            )
        ).all()
    )
    question_results_by_id = {
        question_result.question_id: question_result
        for question_result in question_results
    }

    return AttemptResultResponse(
        attempt_id=str(attempt.id),
        slug=exam.slug,
        title=version.title,
        attempt_number=attempt.attempt_number,
        status=attempt.status,
        score=_as_float(result.score),
        part1_score=_as_float(result.part1_score),
        part2_score=_as_float(result.part2_score),
        correct_count=result.correct_count,
        incorrect_count=result.incorrect_count,
        unanswered_count=result.unanswered_count,
        started_at=attempt.started_at,
        submitted_at=attempt.submitted_at,
        graded_at=result.graded_at,
        can_retry=_has_published_version_for_exam(session, exam.id),
        questions=[
            AttemptResultQuestion(
                id=str(question.id),
                position=question.position,
                part_number=question.part_number,
                part_position=question.part_position,
                question_type=question.question_type,
                body=question.body,
                source_text=question.source_text,
                explanation=question.explanation,
                selected_option_id=(
                    str(answers_by_question_id[question.id].selected_option_id)
                    if question.id in answers_by_question_id
                    and answers_by_question_id[question.id].selected_option_id
                    is not None
                    else None
                ),
                correct_option_id=next(
                    (
                        str(option.id)
                        for option in options_by_question_id[question.id]
                        if option.is_correct
                    ),
                    None,
                ),
                options=[
                    AttemptOption(
                        id=str(option.id),
                        position=option.position,
                        body=option.body,
                    )
                    for option in options_by_question_id[question.id]
                ],
                statements=[
                    AttemptResultStatement(
                        id=str(statement.id),
                        position=statement.position,
                        body=statement.body,
                        selected_value=statement_answer_values.get(statement.id),
                        correct_value=statement.is_correct,
                        is_correct=(
                            statement_answer_values.get(statement.id) is not None
                            and statement_answer_values[statement.id]
                            == statement.is_correct
                        ),
                    )
                    for statement in statements_by_question_id[question.id]
                ],
                correct_count=question_results_by_id[question.id].correct_count,
                total_count=question_results_by_id[question.id].total_count,
                earned_score=_as_float(
                    question_results_by_id[question.id].earned_score
                ),
                max_score=_as_float(question_results_by_id[question.id].max_score),
            )
            for question in questions
        ],
    )


def start_or_resume_attempt(
    session: Session,
    current_user: User,
    slug: str,
    restart: bool = False,
) -> AttemptDetail:
    row = _published_exam_version_for_slug(session, slug)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    _, version = row
    attempt = _open_attempt_for_version(session, current_user, version)
    if attempt is not None and _is_attempt_expired(attempt):
        _finalize_attempt(session, attempt, "expired_and_submitted")
        session.commit()
        attempt = None
    elif attempt is not None and restart:
        attempt.status = "abandoned"
        session.commit()
        attempt = None

    if attempt is not None and _resume_attempt(attempt):
        session.commit()
        session.refresh(attempt)

    if attempt is None:
        started_at = _now()
        attempt = Attempt(
            user_id=current_user.id,
            exam_version_id=version.id,
            status="in_progress",
            started_at=started_at,
            expires_at=started_at + timedelta(minutes=version.duration_minutes),
            paused_at=None,
            submitted_at=None,
            attempt_number=_next_attempt_number(session, current_user, version),
        )
        session.add(attempt)
        session.commit()
        session.refresh(attempt)

    return _attempt_detail(session, current_user, attempt)


def list_attempt_history(
    session: Session,
    current_user: User,
    page: int = 1,
    page_size: int = 12,
) -> AttemptHistoryPage:
    completed_statuses = ("submitted", "expired_and_submitted")
    rows = session.execute(
        select(Attempt, AttemptResult, ExamVersion, Exam)
        .join(AttemptResult, AttemptResult.attempt_id == Attempt.id)
        .join(ExamVersion, ExamVersion.id == Attempt.exam_version_id)
        .join(Exam, Exam.id == ExamVersion.exam_id)
        .where(Attempt.user_id == current_user.id)
        .where(Attempt.status.in_(completed_statuses))
        .order_by(
            Attempt.submitted_at.desc(),
            AttemptResult.graded_at.desc(),
        )
    ).all()
    grouped_attempts: dict[uuid.UUID, list[tuple[Attempt, AttemptResult]]] = {}
    exams_by_id: dict[uuid.UUID, Exam] = {}
    latest_versions_by_exam_id: dict[uuid.UUID, ExamVersion] = {}
    for attempt, result, version, exam in rows:
        if exam.id not in grouped_attempts:
            grouped_attempts[exam.id] = []
            exams_by_id[exam.id] = exam
            latest_versions_by_exam_id[exam.id] = version
        grouped_attempts[exam.id].append((attempt, result))

    exam_ids = list(grouped_attempts)
    paged_exam_ids = exam_ids[(page - 1) * page_size : page * page_size]
    retry_by_exam_id = {
        exam_id: _has_published_version_for_exam(session, exam_id)
        for exam_id in paged_exam_ids
    }
    return AttemptHistoryPage(
        items=[
            HistoryExamGroup(
                slug=exam.slug,
                title=version.title,
                attempt_count=len(attempts),
                best_score=max(_as_float(result.score) for _, result in attempts),
                latest_score=_as_float(attempts[0][1].score),
                latest_submitted_at=attempts[0][0].submitted_at,
                can_retry=retry_by_exam_id[exam_id],
                attempts=[
                    HistoryAttemptSummary(
                        attempt_id=str(attempt.id),
                        attempt_number=attempt.attempt_number,
                        status=attempt.status,
                        score=_as_float(result.score),
                        correct_count=result.correct_count,
                        incorrect_count=result.incorrect_count,
                        unanswered_count=result.unanswered_count,
                        submitted_at=attempt.submitted_at,
                        graded_at=result.graded_at,
                    )
                    for attempt, result in attempts
                ],
            )
            for exam_id in paged_exam_ids
            for exam in [exams_by_id[exam_id]]
            for version in [latest_versions_by_exam_id[exam_id]]
            for attempts in [grouped_attempts[exam_id]]
        ],
        page=page,
        page_size=page_size,
        total=len(grouped_attempts),
    )


def get_attempt(
    session: Session,
    current_user: User,
    attempt_id: uuid.UUID,
) -> AttemptDetail:
    attempt = _owned_attempt(session, current_user, attempt_id)
    return _attempt_detail(session, current_user, attempt)


def resume_attempt(
    session: Session,
    current_user: User,
    attempt_id: uuid.UUID,
) -> AttemptDetail:
    attempt = _owned_attempt(session, current_user, attempt_id)
    if _is_attempt_expired(attempt):
        _finalize_attempt(session, attempt, "expired_and_submitted")
        session.commit()
        session.refresh(attempt)
        return _attempt_detail(session, current_user, attempt)
    if _resume_attempt(attempt):
        session.commit()
        session.refresh(attempt)
    return _attempt_detail(session, current_user, attempt)


def pause_attempt(
    session: Session,
    current_user: User,
    attempt_id: uuid.UUID,
) -> None:
    attempt = _owned_attempt(session, current_user, attempt_id)
    if attempt.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "attempt_closed"},
        )
    if _is_attempt_expired(attempt):
        _finalize_attempt(session, attempt, "expired_and_submitted")
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "attempt_expired"},
        )
    if attempt.paused_at is None:
        attempt.paused_at = _now()
        session.commit()


def save_attempt_answer(
    session: Session,
    current_user: User,
    attempt_id: uuid.UUID,
    question_id: uuid.UUID,
    payload: SaveAttemptAnswerRequest,
) -> SavedAttemptAnswer:
    attempt = _owned_attempt(session, current_user, attempt_id)
    if attempt.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "attempt_closed"},
        )
    if attempt.paused_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "attempt_paused"},
        )
    if _is_attempt_expired(attempt):
        _finalize_attempt(session, attempt, "expired_and_submitted")
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "attempt_expired"},
        )

    question = session.get(Question, question_id)
    if question is None or question.exam_version_id != attempt.exam_version_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if question.question_type == "multiple_choice":
        if payload.statement_answers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="statement answers are only valid for true/false questions",
            )
        if payload.selected_option_id is not None:
            option = session.get(QuestionOption, payload.selected_option_id)
            if option is None or option.question_id != question.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="selected option does not belong to question",
                )
        answer = _answer_for_question(session, attempt, question)
        answer.is_marked_for_review = payload.is_marked_for_review
        answer.updated_at = _now()
        answer.selected_option_id = payload.selected_option_id
    else:
        if payload.selected_option_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="selected option is only valid for multiple choice questions",
            )
        statement_answers = payload.statement_answers or []
        statements = _statements_by_question_id(session, [question.id])[question.id]
        statements_by_id = {statement.id: statement for statement in statements}
        for statement_answer in statement_answers:
            if statement_answer.statement_id not in statements_by_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="statement does not belong to question",
                )
        answer = _answer_for_question(session, attempt, question)
        answer.is_marked_for_review = payload.is_marked_for_review
        answer.updated_at = _now()
        for statement_answer in statement_answers:
            saved_statement_answer = session.get(
                AttemptStatementAnswer,
                {
                    "attempt_id": attempt.id,
                    "statement_id": statement_answer.statement_id,
                },
            )
            if saved_statement_answer is None:
                saved_statement_answer = AttemptStatementAnswer(
                    attempt_id=attempt.id,
                    question_id=question.id,
                    statement_id=statement_answer.statement_id,
                    selected_value=statement_answer.selected_value,
                )
                session.add(saved_statement_answer)
            else:
                saved_statement_answer.selected_value = statement_answer.selected_value
                saved_statement_answer.updated_at = _now()
        answer.selected_option_id = None

    session.commit()
    session.refresh(answer)
    return SavedAttemptAnswer(
        question_id=str(answer.question_id),
        selected_option_id=(
            str(answer.selected_option_id)
            if answer.selected_option_id is not None
            else None
        ),
        statement_answers=[
            AttemptSavedStatementAnswer(
                statement_id=str(statement_answer.statement_id),
                selected_value=statement_answer.selected_value,
            )
            for statement_answer in _saved_statement_answers(
                session,
                attempt,
                question.id,
            )
        ],
        is_marked_for_review=answer.is_marked_for_review,
        updated_at=answer.updated_at,
    )


def submit_attempt(
    session: Session,
    current_user: User,
    attempt_id: uuid.UUID,
) -> AttemptResultResponse:
    attempt = _owned_attempt(session, current_user, attempt_id)
    if attempt.status == "abandoned":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "attempt_abandoned"},
        )
    if attempt.status == "in_progress":
        final_status = (
            "expired_and_submitted" if _is_attempt_expired(attempt) else "submitted"
        )
        result = _finalize_attempt(session, attempt, final_status)
        session.commit()
        session.refresh(attempt)
        session.refresh(result)
        return _result_response(session, attempt, result)

    result = session.get(AttemptResult, attempt.id)
    if result is None:
        result = _finalize_attempt(session, attempt, attempt.status)
        session.commit()
        session.refresh(result)
    return _result_response(session, attempt, result)


def get_attempt_result(
    session: Session,
    current_user: User,
    attempt_id: uuid.UUID,
) -> AttemptResultResponse:
    attempt = _owned_attempt(session, current_user, attempt_id)
    if attempt.status == "abandoned":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "attempt_abandoned"},
        )
    if attempt.status == "in_progress":
        if not _is_attempt_expired(attempt):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "attempt_in_progress"},
            )
        result = _finalize_attempt(session, attempt, "expired_and_submitted")
        session.commit()
        session.refresh(attempt)
        session.refresh(result)
        return _result_response(session, attempt, result)

    result = session.get(AttemptResult, attempt.id)
    if result is None:
        result = _finalize_attempt(session, attempt, attempt.status)
        session.commit()
        session.refresh(result)
    return _result_response(session, attempt, result)


class StudentAttemptService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def start_or_resume_attempt(
        self,
        current_user: User,
        slug: str,
        restart: bool = False,
    ) -> AttemptDetail:
        return start_or_resume_attempt(self._session, current_user, slug, restart)

    def list_attempt_history(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 12,
    ) -> AttemptHistoryPage:
        return list_attempt_history(self._session, current_user, page, page_size)

    def get_attempt(self, current_user: User, attempt_id: uuid.UUID) -> AttemptDetail:
        return get_attempt(self._session, current_user, attempt_id)

    def resume_attempt(
        self, current_user: User, attempt_id: uuid.UUID
    ) -> AttemptDetail:
        return resume_attempt(self._session, current_user, attempt_id)

    def pause_attempt(self, current_user: User, attempt_id: uuid.UUID) -> None:
        return pause_attempt(self._session, current_user, attempt_id)

    def save_attempt_answer(
        self,
        current_user: User,
        attempt_id: uuid.UUID,
        question_id: uuid.UUID,
        payload: SaveAttemptAnswerRequest,
    ) -> SavedAttemptAnswer:
        return save_attempt_answer(
            self._session,
            current_user,
            attempt_id,
            question_id,
            payload,
        )

    def submit_attempt(
        self,
        current_user: User,
        attempt_id: uuid.UUID,
    ) -> AttemptResultResponse:
        return submit_attempt(self._session, current_user, attempt_id)

    def get_attempt_result(
        self,
        current_user: User,
        attempt_id: uuid.UUID,
    ) -> AttemptResultResponse:
        return get_attempt_result(self._session, current_user, attempt_id)
