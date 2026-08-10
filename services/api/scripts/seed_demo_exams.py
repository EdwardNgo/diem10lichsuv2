import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TypeAlias

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from diem10_api.database import SessionLocal
from diem10_api.models import (
    Exam,
    ExamVersion,
    ExamVersionTopic,
    Question,
    QuestionOption,
    QuestionStatement,
    Topic,
)


@dataclass(frozen=True)
class DemoMultipleChoiceQuestion:
    body: str
    explanation: str
    options: tuple[tuple[str, bool], ...]


@dataclass(frozen=True)
class DemoTrueFalseQuestion:
    body: str
    source_text: str
    explanation: str
    statements: tuple[tuple[str, bool], ...]


DemoQuestion: TypeAlias = DemoMultipleChoiceQuestion | DemoTrueFalseQuestion


@dataclass(frozen=True)
class DemoExam:
    slug: str
    title: str
    summary: str
    topic_slug: str
    year: int
    difficulty: str
    duration_minutes: int
    status: str
    questions: tuple[DemoQuestion, ...]


TOPICS = (
    ("lich-su-viet-nam", "Lịch sử Việt Nam", None, 10),
    ("lich-su-the-gioi", "Lịch sử thế giới", None, 20),
    ("viet-nam-1945-1975", "Việt Nam 1945-1975", "lich-su-viet-nam", 11),
    ("doi-moi-1986", "Việt Nam thời kỳ Đổi mới", "lich-su-viet-nam", 12),
    ("chien-tranh-lanh", "Chiến tranh lạnh", "lich-su-the-gioi", 21),
    ("dong-nam-a", "Đông Nam Á", "lich-su-the-gioi", 22),
)


def _multiple_choice_questions(
    topic_name: str,
) -> tuple[DemoMultipleChoiceQuestion, ...]:
    questions: list[DemoMultipleChoiceQuestion] = []
    stems = (
        "Sự kiện tiêu biểu của {topic} ở mốc số {index} là gì?",
        "Nhận định nào đúng về {topic} trong giai đoạn ôn tập số {index}?",
        "Yếu tố nào có ý nghĩa nổi bật đối với {topic} ở câu {index}?",
        "Kết quả lịch sử nào gắn với {topic} ở nội dung số {index}?",
    )
    for index in range(1, 25):
        correct_position = ((index - 1) % 4) + 1
        options = tuple(
            (
                f"Phương án {label} cho nội dung {index}",
                position == correct_position,
            )
            for position, label in enumerate(("A", "B", "C", "D"), start=1)
        )
        questions.append(
            DemoMultipleChoiceQuestion(
                body=stems[index % len(stems)].format(
                    topic=topic_name,
                    index=index,
                ),
                explanation=(
                    f"Đáp án đúng là phương án {correct_position} vì phù hợp với "
                    f"trọng tâm {topic_name} ở nội dung {index}."
                ),
                options=options,
            )
        )
    return tuple(questions)


def _true_false_questions(topic_name: str) -> tuple[DemoTrueFalseQuestion, ...]:
    questions: list[DemoTrueFalseQuestion] = []
    patterns = (
        (True, False, True, False),
        (False, True, True, False),
        (True, True, False, False),
        (False, True, False, True),
    )
    for index in range(1, 5):
        statements = tuple(
            (
                f"Phát biểu {label.lower()} về tư liệu {index} của {topic_name}.",
                is_correct,
            )
            for label, is_correct in zip(("A", "B", "C", "D"), patterns[index - 1])
        )
        questions.append(
            DemoTrueFalseQuestion(
                body=(
                    f"Đọc tư liệu {index} và xác định tính đúng sai của các phát biểu."
                ),
                source_text=(
                    f"Tư liệu {index}: Nội dung tóm lược về {topic_name}, nêu bối "
                    "cảnh, lực lượng tham gia và ý nghĩa lịch sử để học sinh đối "
                    "chiếu từng phát biểu."
                ),
                explanation=(
                    f"Câu tư liệu {index} được chấm theo số phát biểu đúng; bỏ "
                    "trống một phát biểu được tính là sai."
                ),
                statements=statements,
            )
        )
    return tuple(questions)


def _demo_questions(topic_name: str) -> tuple[DemoQuestion, ...]:
    return (*_multiple_choice_questions(topic_name), *_true_false_questions(topic_name))


DEMO_EXAMS = (
    DemoExam(
        slug="tong-on-viet-nam-1945-1975",
        title="Tổng ôn Việt Nam 1945-1975",
        summary=(
            "Bộ câu hỏi trọng tâm về kháng chiến, xây dựng miền Bắc và thống "
            "nhất đất nước."
        ),
        topic_slug="viet-nam-1945-1975",
        year=2026,
        difficulty="Trung bình",
        duration_minutes=50,
        status="published",
        questions=_demo_questions("Việt Nam 1945-1975"),
    ),
    DemoExam(
        slug="de-luyen-chien-tranh-lanh",
        title="Đề luyện Chiến tranh lạnh",
        summary=(
            "Ôn tập trật tự hai cực Ianta, các liên minh quân sự và xu thế hòa hoãn."
        ),
        topic_slug="chien-tranh-lanh",
        year=2025,
        difficulty="Khó",
        duration_minutes=45,
        status="published",
        questions=_demo_questions("Chiến tranh lạnh"),
    ),
    DemoExam(
        slug="on-tap-dong-nam-a",
        title="Ôn tập Đông Nam Á sau 1945",
        summary=(
            "Tập trung quá trình giành độc lập, thành lập ASEAN và hợp tác khu vực."
        ),
        topic_slug="dong-nam-a",
        year=2026,
        difficulty="Dễ",
        duration_minutes=35,
        status="published",
        questions=_demo_questions("Đông Nam Á sau 1945"),
    ),
    DemoExam(
        slug="de-nhanh-doi-moi-1986",
        title="Đề nhanh Việt Nam thời kỳ Đổi mới",
        summary="Kiểm tra các mốc và ý nghĩa của công cuộc Đổi mới từ năm 1986.",
        topic_slug="doi-moi-1986",
        year=2024,
        difficulty="Trung bình",
        duration_minutes=30,
        status="published",
        questions=_demo_questions("Việt Nam thời kỳ Đổi mới"),
    ),
    DemoExam(
        slug="nhap-dang-ra-soat",
        title="Bản nháp đang rà soát",
        summary=(
            "Đề nháp dùng để chứng minh API public không trả nội dung chưa xuất bản."
        ),
        topic_slug="lich-su-viet-nam",
        year=2026,
        difficulty="Dễ",
        duration_minutes=25,
        status="draft",
        questions=_demo_questions("Lịch sử Việt Nam"),
    ),
)


def upsert_topic(
    session: Session,
    slug: str,
    name: str,
    parent_id: uuid.UUID | None,
    sort_order: int,
) -> Topic:
    topic = session.scalar(select(Topic).where(Topic.slug == slug))
    if topic is None:
        topic = Topic(slug=slug, name=name, parent_id=parent_id, sort_order=sort_order)
        session.add(topic)
        session.flush()
        return topic

    topic.name = name
    topic.parent_id = parent_id
    topic.sort_order = sort_order
    topic.is_active = True
    return topic


def upsert_demo_exam(
    session: Session,
    demo_exam: DemoExam,
    topic: Topic,
    published_at: datetime | None,
) -> None:
    validate_demo_exam(demo_exam)
    exam = session.scalar(select(Exam).where(Exam.slug == demo_exam.slug))
    if exam is None:
        exam = Exam(slug=demo_exam.slug)
        session.add(exam)
        session.flush()

    version = session.scalar(
        select(ExamVersion).where(
            ExamVersion.exam_id == exam.id,
            ExamVersion.version_number == 1,
        )
    )
    if version is None:
        version = ExamVersion(
            exam_id=exam.id,
            version_number=1,
            status=demo_exam.status,
            title=demo_exam.title,
            summary=demo_exam.summary,
            year=demo_exam.year,
            difficulty=demo_exam.difficulty,
            duration_minutes=demo_exam.duration_minutes,
            published_at=published_at,
        )
        session.add(version)
        session.flush()

    version.status = demo_exam.status
    version.title = demo_exam.title
    version.summary = demo_exam.summary
    version.year = demo_exam.year
    version.difficulty = demo_exam.difficulty
    version.duration_minutes = demo_exam.duration_minutes
    version.published_at = published_at

    link = session.scalar(
        select(ExamVersionTopic).where(
            ExamVersionTopic.exam_version_id == version.id,
            ExamVersionTopic.topic_id == topic.id,
        )
    )
    if link is None:
        session.add(
            ExamVersionTopic(
                exam_version_id=version.id,
                topic_id=topic.id,
                is_primary=True,
            )
        )
    else:
        link.is_primary = True

    desired_positions = set(range(1, len(demo_exam.questions) + 1))
    extra_questions = session.scalars(
        select(Question).where(
            Question.exam_version_id == version.id,
            Question.position.not_in(desired_positions),
        )
    ).all()
    extra_question_ids = [question.id for question in extra_questions]
    if extra_question_ids:
        session.execute(
            delete(QuestionOption).where(
                QuestionOption.question_id.in_(extra_question_ids)
            )
        )
        session.execute(
            delete(QuestionStatement).where(
                QuestionStatement.question_id.in_(extra_question_ids)
            )
        )
        session.execute(delete(Question).where(Question.id.in_(extra_question_ids)))

    for index, demo_question in enumerate(demo_exam.questions, start=1):
        part_number = 1 if isinstance(demo_question, DemoMultipleChoiceQuestion) else 2
        part_position = index if part_number == 1 else index - 24
        question_type = (
            "multiple_choice"
            if isinstance(demo_question, DemoMultipleChoiceQuestion)
            else "true_false_group"
        )
        question = session.scalar(
            select(Question).where(
                Question.exam_version_id == version.id,
                Question.position == index,
            )
        )
        if question is None:
            question = Question(
                exam_version_id=version.id,
                position=index,
                part_number=part_number,
                part_position=part_position,
                question_type=question_type,
                body=demo_question.body,
                source_text=(
                    demo_question.source_text
                    if isinstance(demo_question, DemoTrueFalseQuestion)
                    else None
                ),
                explanation=demo_question.explanation,
            )
            session.add(question)
            session.flush()
        question.part_number = part_number
        question.part_position = part_position
        question.question_type = question_type
        question.body = demo_question.body
        question.source_text = (
            demo_question.source_text
            if isinstance(demo_question, DemoTrueFalseQuestion)
            else None
        )
        question.explanation = demo_question.explanation

        if isinstance(demo_question, DemoMultipleChoiceQuestion):
            session.execute(
                delete(QuestionStatement).where(
                    QuestionStatement.question_id == question.id
                )
            )
            for option_index, (body, is_correct) in enumerate(
                demo_question.options, start=1
            ):
                option = session.scalar(
                    select(QuestionOption).where(
                        QuestionOption.question_id == question.id,
                        QuestionOption.position == option_index,
                    )
                )
                if option is None:
                    option = QuestionOption(
                        question_id=question.id,
                        position=option_index,
                        body=body,
                        is_correct=is_correct,
                    )
                    session.add(option)
                option.body = body
                option.is_correct = is_correct
            session.execute(
                delete(QuestionOption).where(
                    QuestionOption.question_id == question.id,
                    QuestionOption.position > len(demo_question.options),
                )
            )
            continue

        session.execute(
            delete(QuestionOption).where(QuestionOption.question_id == question.id)
        )
        for statement_index, (body, is_correct) in enumerate(
            demo_question.statements,
            start=1,
        ):
            statement = session.scalar(
                select(QuestionStatement).where(
                    QuestionStatement.question_id == question.id,
                    QuestionStatement.position == statement_index,
                )
            )
            if statement is None:
                statement = QuestionStatement(
                    question_id=question.id,
                    position=statement_index,
                    body=body,
                    is_correct=is_correct,
                )
                session.add(statement)
            statement.body = body
            statement.is_correct = is_correct
        session.execute(
            delete(QuestionStatement).where(
                QuestionStatement.question_id == question.id,
                QuestionStatement.position > len(demo_question.statements),
            )
        )


def validate_demo_exam(demo_exam: DemoExam) -> None:
    mcq_questions = [
        question
        for question in demo_exam.questions
        if isinstance(question, DemoMultipleChoiceQuestion)
    ]
    true_false_questions = [
        question
        for question in demo_exam.questions
        if isinstance(question, DemoTrueFalseQuestion)
    ]
    if len(mcq_questions) != 24 or len(true_false_questions) != 4:
        raise ValueError(
            f"{demo_exam.slug} must have 24 MCQ and 4 true/false questions"
        )
    for question in mcq_questions:
        if len(question.options) != 4:
            raise ValueError(f"{demo_exam.slug} has an MCQ without 4 options")
        if sum(1 for _, is_correct in question.options if is_correct) != 1:
            raise ValueError(f"{demo_exam.slug} has an MCQ without exactly one answer")
    for question in true_false_questions:
        if not question.source_text.strip():
            raise ValueError(
                f"{demo_exam.slug} has a true/false question without source"
            )
        if len(question.statements) != 4:
            raise ValueError(
                f"{demo_exam.slug} has a true/false question without 4 statements"
            )


def seed_demo_exams() -> None:
    with SessionLocal() as session:
        topics_by_slug: dict[str, Topic] = {}
        for slug, name, parent_slug, sort_order in TOPICS:
            parent_id = (
                topics_by_slug[parent_slug].id if parent_slug is not None else None
            )
            topics_by_slug[slug] = upsert_topic(
                session=session,
                slug=slug,
                name=name,
                parent_id=parent_id,
                sort_order=sort_order,
            )

        now = datetime.now(UTC)
        for index, demo_exam in enumerate(DEMO_EXAMS):
            published_at = (
                now - timedelta(days=index) if demo_exam.status == "published" else None
            )
            upsert_demo_exam(
                session=session,
                demo_exam=demo_exam,
                topic=topics_by_slug[demo_exam.topic_slug],
                published_at=published_at,
            )

        session.commit()
        print(f"Seeded {len(DEMO_EXAMS)} demo exams and {len(TOPICS)} topics.")


if __name__ == "__main__":
    seed_demo_exams()
