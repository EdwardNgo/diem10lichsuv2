import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from diem10_api.database import SessionLocal
from diem10_api.models import (
    Exam,
    ExamVersion,
    ExamVersionTopic,
    Question,
    QuestionOption,
    Topic,
)


@dataclass(frozen=True)
class DemoQuestion:
    body: str
    explanation: str
    options: tuple[tuple[str, bool], ...]


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


DEMO_EXAMS = (
    DemoExam(
        slug="tong-on-viet-nam-1945-1975",
        title="Tổng ôn Việt Nam 1945-1975",
        summary="Bộ câu hỏi trọng tâm về kháng chiến, xây dựng miền Bắc và thống nhất đất nước.",
        topic_slug="viet-nam-1945-1975",
        year=2026,
        difficulty="Trung bình",
        duration_minutes=50,
        status="published",
        questions=(
            DemoQuestion(
                body="Sự kiện nào mở đầu cho thắng lợi của Cách mạng tháng Tám năm 1945?",
                explanation="Câu này dùng để seed dữ liệu; lời giải không được lộ ở API chi tiết US-04.",
                options=(
                    ("Nhật đảo chính Pháp", False),
                    ("Tổng khởi nghĩa giành chính quyền", True),
                    ("Hiệp định Sơ bộ được ký kết", False),
                    ("Chiến dịch Biên giới bắt đầu", False),
                ),
            ),
            DemoQuestion(
                body="Hiệp định Giơnevơ năm 1954 liên quan trực tiếp đến cuộc kháng chiến nào?",
                explanation="Hiệp định Giơnevơ kết thúc cuộc kháng chiến chống Pháp ở Đông Dương.",
                options=(
                    ("Kháng chiến chống Pháp", True),
                    ("Kháng chiến chống Mỹ", False),
                    ("Chiến tranh bảo vệ biên giới", False),
                    ("Phong trào Cần Vương", False),
                ),
            ),
        ),
    ),
    DemoExam(
        slug="de-luyen-chien-tranh-lanh",
        title="Đề luyện Chiến tranh lạnh",
        summary="Ôn tập trật tự hai cực Ianta, các liên minh quân sự và xu thế hòa hoãn.",
        topic_slug="chien-tranh-lanh",
        year=2025,
        difficulty="Khó",
        duration_minutes=45,
        status="published",
        questions=(
            DemoQuestion(
                body="Trật tự thế giới hai cực Ianta hình thành sau sự kiện nào?",
                explanation="Trật tự hai cực Ianta được xác lập sau Hội nghị Ianta và sau Chiến tranh thế giới thứ hai.",
                options=(
                    ("Chiến tranh thế giới thứ nhất", False),
                    ("Hội nghị Ianta năm 1945", True),
                    ("Liên Xô tan rã", False),
                    ("ASEAN thành lập", False),
                ),
            ),
            DemoQuestion(
                body="Một đặc điểm nổi bật của Chiến tranh lạnh là gì?",
                explanation="Hai phe đối đầu căng thẳng nhưng không trực tiếp gây chiến tranh thế giới.",
                options=(
                    ("Đối đầu Đông-Tây kéo dài", True),
                    ("Không có chạy đua vũ trang", False),
                    ("Mọi nước đều trung lập", False),
                    ("Liên hợp quốc bị giải thể", False),
                ),
            ),
        ),
    ),
    DemoExam(
        slug="on-tap-dong-nam-a",
        title="Ôn tập Đông Nam Á sau 1945",
        summary="Tập trung quá trình giành độc lập, thành lập ASEAN và hợp tác khu vực.",
        topic_slug="dong-nam-a",
        year=2026,
        difficulty="Dễ",
        duration_minutes=35,
        status="published",
        questions=(
            DemoQuestion(
                body="ASEAN được thành lập vào năm nào?",
                explanation="ASEAN thành lập ngày 8/8/1967 tại Bangkok.",
                options=(
                    ("1955", False),
                    ("1967", True),
                    ("1975", False),
                    ("1995", False),
                ),
            ),
            DemoQuestion(
                body="Việt Nam gia nhập ASEAN vào năm nào?",
                explanation="Việt Nam trở thành thành viên ASEAN năm 1995.",
                options=(
                    ("1986", False),
                    ("1991", False),
                    ("1995", True),
                    ("2000", False),
                ),
            ),
        ),
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
        questions=(
            DemoQuestion(
                body="Đường lối Đổi mới được đề ra tại Đại hội nào của Đảng?",
                explanation="Đại hội VI năm 1986 đề ra đường lối Đổi mới.",
                options=(
                    ("Đại hội IV", False),
                    ("Đại hội V", False),
                    ("Đại hội VI", True),
                    ("Đại hội VII", False),
                ),
            ),
        ),
    ),
    DemoExam(
        slug="nhap-dang-ra-soat",
        title="Bản nháp đang rà soát",
        summary="Đề nháp dùng để chứng minh API public không trả nội dung chưa xuất bản.",
        topic_slug="lich-su-viet-nam",
        year=2026,
        difficulty="Dễ",
        duration_minutes=25,
        status="draft",
        questions=(
            DemoQuestion(
                body="Câu hỏi nháp không được public.",
                explanation="Nội dung nháp chỉ dành cho kiểm thử.",
                options=(("Đáp án nháp", True), ("Nhiễu", False)),
            ),
        ),
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

    for index, demo_question in enumerate(demo_exam.questions, start=1):
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
                body=demo_question.body,
                explanation=demo_question.explanation,
            )
            session.add(question)
            session.flush()
        question.body = demo_question.body
        question.explanation = demo_question.explanation

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
