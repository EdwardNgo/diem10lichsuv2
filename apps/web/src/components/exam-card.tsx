import Link from "next/link";

type CompletionStatus = "not_started" | "in_progress" | "completed";

export type ExamCardData = {
  slug: string;
  title: string;
  summary: string;
  topic: string;
  year: number | null;
  duration_minutes: number;
  question_count: number;
  completion_status?: CompletionStatus;
};

function statusText(status: CompletionStatus | undefined) {
  if (status === "in_progress") {
    return "Đang làm dở";
  }
  if (status === "completed") {
    return "Đã hoàn thành";
  }
  return "Chưa làm";
}

function statusTone(status: CompletionStatus | undefined) {
  if (status === "in_progress") {
    return "text-[#0369a1]";
  }
  if (status === "completed") {
    return "text-[#166534]";
  }
  return "text-[#64748b]";
}

type ExamCardProps = {
  exam: ExamCardData;
  authenticated: boolean;
  onGuestSelect?: (exam: ExamCardData) => void;
};

export function ExamCard({ exam, authenticated, onGuestSelect }: ExamCardProps) {
  const actionClassName =
    "inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-[#123047] px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#0284c7] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#0284c7]";

  return (
    <article className="group flex h-full flex-col overflow-hidden rounded-2xl border border-[#dbeafe] bg-white shadow-[0_8px_30px_rgba(2,132,199,0.06)] transition-all duration-200 hover:-translate-y-0.5 hover:border-[#0284c7] hover:shadow-[0_20px_48px_rgba(2,132,199,0.14)]">
      <div className="border-b border-[#e0f2fe] bg-[linear-gradient(180deg,#f8fcff_0%,#ffffff_100%)] px-5 pb-4 pt-5">
        <div className="flex min-h-8 items-center justify-between gap-3">
          <span className="truncate rounded-full bg-[#e0f2fe] px-3 py-1 text-xs font-semibold text-[#0369a1]">
            {exam.topic}
          </span>
          <span className="shrink-0 rounded-full border border-[#bae6fd] bg-white px-3 py-1 text-xs font-semibold text-[#45667a]">
            {exam.year ?? "Tổng ôn"}
          </span>
        </div>
        <p
          className={`mt-3 min-h-5 text-xs font-semibold ${statusTone(exam.completion_status)}`}
        >
          {authenticated ? statusText(exam.completion_status) : "\u00a0"}
        </p>
      </div>

      <div className="flex flex-1 flex-col px-5 pb-5 pt-4">
        <h2 className="min-h-[3.5rem] line-clamp-2 text-xl font-semibold leading-snug tracking-tight text-[#123047]">
          {exam.title}
        </h2>
        <p className="mt-2 min-h-[4rem] line-clamp-3 text-sm leading-6 text-[#45667a]">
          {exam.summary.trim() === ""
            ? "Đề thi thử môn Lịch sử, theo cấu trúc kỳ thi tốt nghiệp THPT."
            : exam.summary}
        </p>
        <p className="mt-3 text-xs font-semibold text-[#64748b]">
          {exam.duration_minutes} phút
        </p>

        <div className="mt-auto border-t border-[#e0f2fe] pt-4">
          {authenticated ? (
            <Link className={actionClassName} href={`/exams/${exam.slug}`}>
              Xem chi tiết
            </Link>
          ) : (
            <button
              className={actionClassName}
              onClick={() => onGuestSelect?.(exam)}
              type="button"
            >
              Xem chi tiết
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
