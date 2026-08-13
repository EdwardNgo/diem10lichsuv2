"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { LoginRequiredPanel } from "@/components/login-required";

type CompletionStatus = "not_started" | "in_progress" | "completed";

type ExamDetailData = {
  slug: string;
  title: string;
  summary: string;
  topics: string[];
  primary_topic: string;
  year: number | null;
  difficulty: string;
  duration_minutes: number;
  question_count: number;
  completion_status: CompletionStatus;
  active_attempt: { id: string; remaining_seconds: number } | null;
  questions: {
    id: string;
    position: number;
    part_number: number;
    part_position: number;
    question_type: "multiple_choice" | "true_false_group";
    body: string;
    source_text: string | null;
    options: {
      id: string;
      position: number;
      body: string;
    }[];
    statements: {
      id: string;
      position: number;
      body: string;
    }[];
  }[];
};

type DetailState =
  | { kind: "loading" }
  | { kind: "login_required"; slug: string }
  | { kind: "unavailable" }
  | { kind: "ready"; exam: ExamDetailData }
  | { kind: "error"; message: string };

function statusText(status: CompletionStatus) {
  if (status === "in_progress") {
    return "Đang làm";
  }
  if (status === "completed") {
    return "Đã hoàn thành";
  }
  return "Chưa làm";
}

export function ExamDetail() {
  const params = useParams<{ slug: string }>();
  const router = useRouter();
  const slug = params.slug;
  const [state, setState] = useState<DetailState>({ kind: "loading" });
  const [isStarting, setIsStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const [resumePromptExam, setResumePromptExam] = useState<ExamDetailData | null>(
    null,
  );

  const loadExam = useCallback(async () => {
    try {
      setState({ kind: "loading" });
      const response = await fetch(`/v1/student/exams/${slug}`, {
        credentials: "same-origin",
      });
      if (response.status === 401) {
        setState({ kind: "login_required", slug });
        return;
      }
      if (response.status === 404) {
        setState({ kind: "unavailable" });
        return;
      }
      if (!response.ok) {
        throw new Error("Không thể tải chi tiết đề.");
      }

      const exam: ExamDetailData = await response.json();
      setState({ kind: "ready", exam });
    } catch (error) {
      setState({
        kind: "error",
        message: error instanceof Error ? error.message : "Có lỗi xảy ra.",
      });
    }
  }, [slug]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadExam();
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, [loadExam]);

  async function startAttempt(exam: ExamDetailData, restart = false) {
    if (!restart && exam.active_attempt !== null) {
      setResumePromptExam(exam);
      return;
    }
    try {
      setIsStarting(true);
      setStartError(null);
      const response = await fetch(
        `/v1/student/exams/${exam.slug}/attempts${restart ? "?restart=true" : ""}`,
        {
          credentials: "same-origin",
          method: "POST",
        },
      );
      if (response.status === 401) {
        setState({ kind: "login_required", slug: exam.slug });
        return;
      }
      if (!response.ok) {
        throw new Error("Không thể bắt đầu lượt làm.");
      }

      const attempt: { id: string } = await response.json();
      router.push(`/attempts/${attempt.id}`);
    } catch (error) {
      setStartError(error instanceof Error ? error.message : "Có lỗi xảy ra.");
    } finally {
      setIsStarting(false);
    }
  }

  function continueAttempt(exam: ExamDetailData) {
    if (exam.active_attempt === null) {
      void startAttempt(exam, true);
      return;
    }
    router.push(`/attempts/${exam.active_attempt.id}`);
  }

  if (state.kind === "loading") {
    return (
      <div className="border border-[#bae6fd] bg-white p-8 text-[#45667a]">
        Đang tải chi tiết đề...
      </div>
    );
  }

  if (state.kind === "login_required") {
    return (
      <LoginRequiredPanel
        body="Chi tiết đề và trạng thái làm bài gắn với tài khoản Google của bạn."
        returnTo={`/exams/${state.slug}`}
        title="Đăng nhập để xem đề"
      />
    );
  }

  if (state.kind === "unavailable") {
    return (
      <div className="border border-[#fecaca] bg-[#fff1f2] p-8">
        <h1 className="text-3xl font-semibold">Đề không còn khả dụng</h1>
        <p className="mt-3 max-w-xl leading-7 text-[#7f1d1d]">
          Đề có thể đã bị archive hoặc chưa được xuất bản.
        </p>
        <Link
          className="mt-6 inline-flex rounded-md border border-[#991b1b] px-5 py-3 font-semibold"
          href="/exams"
        >
          Quay lại kho đề
        </Link>
      </div>
    );
  }

  if (state.kind === "error") {
    return (
      <div className="border border-[#fecaca] bg-[#fff1f2] p-8">
        <p className="font-semibold text-[#7f1d1d]">{state.message}</p>
        <button
          className="mt-5 rounded-md border border-[#991b1b] px-5 py-3 font-semibold"
          onClick={() => void loadExam()}
          type="button"
        >
          Thử lại
        </button>
      </div>
    );
  }

  return (
    <article className="grid gap-8">
      <section className="border border-[#bae6fd] bg-white p-6 sm:p-8">
        <div className="flex flex-wrap gap-2 text-xs font-semibold uppercase tracking-[0.12em]">
          <span className="bg-[#e0f2fe] px-3 py-1 text-[#0284c7]">
            {statusText(state.exam.completion_status)}
          </span>
          <span className="border border-[#bae6fd] px-3 py-1 text-[#45667a]">
            {state.exam.year ?? "Tổng ôn"}
          </span>
        </div>
        <h1 className="mt-5 text-4xl font-semibold tracking-tight">
          {state.exam.title}
        </h1>
        <p className="mt-4 max-w-3xl leading-7 text-[#45667a]">
          {state.exam.summary}
        </p>
        <dl className="mt-6 grid gap-4 text-sm text-[#45667a] sm:grid-cols-3">
          <div className="border-t border-[#bae6fd] pt-4">
            <dt className="font-semibold text-[#123047]">Chủ đề chính</dt>
            <dd>{state.exam.primary_topic}</dd>
          </div>
          <div className="border-t border-[#bae6fd] pt-4">
            <dt className="font-semibold text-[#123047]">Số câu</dt>
            <dd>{state.exam.question_count} câu (24 ABCD + 4 Đúng/Sai)</dd>
          </div>
          <div className="border-t border-[#bae6fd] pt-4">
            <dt className="font-semibold text-[#123047]">Thời lượng</dt>
            <dd>{state.exam.duration_minutes} phút</dd>
          </div>
        </dl>
        <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-center">
          <button
            className="rounded-md bg-[#123047] px-5 py-3 font-semibold text-white hover:bg-[#0284c7] disabled:cursor-wait disabled:opacity-70"
            disabled={isStarting}
            onClick={() => void startAttempt(state.exam)}
            type="button"
          >
            {isStarting
              ? "Đang chuẩn bị..."
              : state.exam.completion_status === "in_progress"
                ? "Tiếp tục làm bài"
                : "Bắt đầu làm bài"}
          </button>
          {startError === null ? null : (
            <p className="text-sm font-semibold text-[#991b1b]">{startError}</p>
          )}
        </div>
      </section>

      {resumePromptExam === null ? null : (
        <ResumeAttemptPopup
          exam={resumePromptExam}
          isStarting={isStarting}
          onCancel={() => setResumePromptExam(null)}
          onContinue={() => continueAttempt(resumePromptExam)}
          onRestart={() => void startAttempt(resumePromptExam, true)}
        />
      )}

      <section className="grid gap-4">
        <div>
          <p className="text-sm font-semibold tracking-[0.16em] text-[#0284c7]">
            XEM TRƯỚC CÂU HỎI
          </p>
          <h2 className="mt-2 text-2xl font-semibold">
            Không hiển thị đáp án đúng hoặc lời giải
          </h2>
        </div>
        {state.exam.questions.map((question) => (
          <section
            className="border border-[#bae6fd] bg-white p-5"
            key={question.id}
          >
            <h3 className="font-semibold">
              Phần {question.part_number} - Câu {question.position}. {question.body}
            </h3>
            {question.source_text === null ? null : (
              <div className="mt-4 border border-[#bae6fd] bg-[#f0f9ff] p-4 leading-7 text-[#123047]">
                {question.source_text}
              </div>
            )}
            <ol className="mt-4 grid gap-2">
              {(question.question_type === "multiple_choice"
                ? question.options
                : question.statements
              ).map((item) => (
                <li
                  className="border border-[#bae6fd] px-4 py-3 text-[#45667a]"
                  key={item.id}
                >
                  {item.position}. {item.body}
                </li>
              ))}
            </ol>
          </section>
        ))}
      </section>
    </article>
  );
}

function ResumeAttemptPopup({
  exam,
  isStarting,
  onCancel,
  onContinue,
  onRestart,
}: {
  exam: ExamDetailData;
  isStarting: boolean;
  onCancel: () => void;
  onContinue: () => void;
  onRestart: () => void;
}) {
  const remainingSeconds = exam.active_attempt?.remaining_seconds ?? 0;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-[#123047]/40 px-5">
      <section className="w-full max-w-md border border-[#bae6fd] bg-white p-6 shadow-xl">
        <p className="text-sm font-semibold tracking-[0.14em] text-[#0284c7]">
          LƯỢT LÀM ĐANG DỞ
        </p>
        <h2 className="mt-3 text-2xl font-semibold">Tiếp tục bài trước?</h2>
        <p className="mt-3 leading-7 text-[#45667a]">
          Lần trước bạn còn {formatRemaining(remainingSeconds)}. Bạn muốn tiếp
          tục lượt làm cũ hay làm lại từ đầu?
        </p>
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <button
            className="rounded-md border border-[#bae6fd] px-4 py-2 font-semibold text-[#45667a]"
            disabled={isStarting}
            onClick={onCancel}
            type="button"
          >
            Để sau
          </button>
          <button
            className="rounded-md border border-[#0284c7] px-4 py-2 font-semibold text-[#0284c7]"
            disabled={isStarting}
            onClick={onRestart}
            type="button"
          >
            Làm lại
          </button>
          <button
            className="rounded-md bg-[#0284c7] px-4 py-2 font-semibold text-white disabled:opacity-50"
            disabled={isStarting}
            onClick={onContinue}
            type="button"
          >
            Tiếp tục
          </button>
        </div>
      </section>
    </div>
  );
}

function formatRemaining(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60)
    .toString()
    .padStart(2, "0");
  const seconds = (totalSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}
