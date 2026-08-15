"use client";

import { useEffect, useState } from "react";

import { LoginModal } from "@/components/login-modal";

type PublicExam = {
  slug: string;
  title: string;
  summary: string;
  topic: string;
  year: number | null;
  difficulty: string;
  duration_minutes: number;
  question_count: number;
};

type ExamState =
  | { kind: "loading" }
  | { kind: "ready"; exams: PublicExam[]; total: number }
  | { kind: "error" };

const initialState: ExamState = { kind: "loading" };

function averageDuration(exams: PublicExam[]): number {
  if (exams.length === 0) {
    return 0;
  }

  const totalDuration = exams.reduce(
    (total, exam) => total + exam.duration_minutes,
    0,
  );
  return Math.round(totalDuration / exams.length);
}

function featuredQuestionCount(exams: PublicExam[]): number {
  return exams.reduce((total, exam) => total + exam.question_count, 0);
}

export function TodaysExam() {
  const [state, setState] = useState<ExamState>(initialState);
  const [reloadKey, setReloadKey] = useState(0);
  const [loginReturnTo, setLoginReturnTo] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadExam() {
      try {
        const response = await fetch("/v1/public/exams?page_size=4", {
          signal: controller.signal,
        });
        if (!response.ok) {
          throw new Error("Không thể tải đề");
        }
        const data: { items: PublicExam[]; total: number } =
          await response.json();
        setState({ kind: "ready", exams: data.items, total: data.total });
      } catch {
        if (!controller.signal.aborted) {
          setState({ kind: "error" });
        }
      }
    }

    void loadExam();
    return () => controller.abort();
  }, [reloadKey]);

  let content = null;

  if (state.kind === "loading") {
    content = (
      <div
        aria-live="polite"
        className="border border-[#bae6fd] bg-white p-5 sm:p-6"
      >
        <p className="text-sm font-semibold text-[#0284c7]">ĐANG TẢI KHO ĐỀ</p>
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          {["Đề đã xuất bản", "Câu hỏi nổi bật", "Phút trung bình"].map(
            (label) => (
              <div
                className="border border-[#bae6fd] bg-[#f2fbff] p-4"
                key={label}
              >
                <p className="h-7 w-16 bg-[#bae6fd]" />
                <p className="mt-3 text-xs font-semibold uppercase tracking-[0.12em] text-[#45667a]">
                  {label}
                </p>
              </div>
            ),
          )}
        </div>
      </div>
    );
  } else if (state.kind === "error") {
    content = (
      <div
        aria-live="polite"
        className="border border-[#d9b8b1] bg-[#f9efed] p-6 sm:p-8"
      >
        <p className="font-semibold">Chưa thể tải kho đề</p>
        <p className="mt-2 text-sm leading-6 text-[#6e4038]">
          Hãy kiểm tra kết nối rồi thử lại sau. Bạn vẫn có thể đăng nhập để
          chuẩn bị ôn tập.
        </p>
        <div className="mt-5 flex flex-col gap-3 sm:flex-row">
          <button
            className="inline-flex min-h-11 items-center justify-center rounded-md border border-[#a15042] px-5 py-2 font-semibold"
            onClick={() => {
              setState(initialState);
              setReloadKey((current) => current + 1);
            }}
            type="button"
          >
            Thử lại
          </button>
          <button
            className="inline-flex min-h-11 items-center justify-center rounded-md bg-[#123047] px-5 py-2 font-semibold text-white"
            onClick={() => setLoginReturnTo("/exams")}
            type="button"
          >
            Đăng nhập
          </button>
        </div>
      </div>
    );
  } else if (state.exams.length === 0) {
    content = (
      <div className="border border-[#bae6fd] bg-white p-6 sm:p-8">
        <p className="text-sm font-semibold text-[#0284c7]">CHƯA CÓ ĐỀ ĐỂ LÀM</p>
        <p className="mt-2 max-w-md text-lg font-semibold leading-7">
          Nội dung sẽ chỉ hiển thị sau khi admin hoàn tất rà soát và xuất bản.
        </p>
        <button
          className="mt-5 inline-flex min-h-11 items-center justify-center rounded-md bg-[#123047] px-5 py-2 font-semibold text-white hover:bg-[#0284c7]"
          onClick={() => setLoginReturnTo("/exams")}
          type="button"
        >
          Đăng nhập
        </button>
      </div>
    );
  } else {
    const duration = averageDuration(state.exams);
    const questionCount = featuredQuestionCount(state.exams);

    content = (
      <div className="space-y-4" aria-live="polite">
        <dl className="grid border border-[#bae6fd] bg-white sm:grid-cols-3">
          {[
            ["Đề đã xuất bản", state.total.toString()],
            ["Câu trong đề nổi bật", questionCount.toString()],
            ["Phút trung bình", duration.toString()],
          ].map(([label, value]) => (
            <div
              className="border-b border-[#bae6fd] p-5 last:border-b-0 sm:border-b-0 sm:border-r sm:last:border-r-0"
              key={label}
            >
              <dt className="text-xs font-semibold uppercase tracking-[0.12em] text-[#45667a]">
                {label}
              </dt>
              <dd className="mt-2 text-3xl font-semibold tracking-tight text-[#123047]">
                {value}
              </dd>
            </div>
          ))}
        </dl>

        {state.exams.map((exam) => (
          <article
            className="grid gap-5 border border-[#bae6fd] bg-white p-5 transition-colors hover:border-[#0284c7] sm:p-6 lg:grid-cols-[1fr_auto] lg:items-center"
            key={exam.slug}
          >
            <div>
              <div className="flex flex-wrap gap-2 text-xs font-semibold uppercase tracking-[0.12em]">
                <span className="bg-[#e0f2fe] px-3 py-1 text-[#0284c7]">
                  Đã xuất bản
                </span>
                {exam.year === null ? null : (
                  <span className="border border-[#bae6fd] px-3 py-1 text-[#45667a]">
                    {exam.year}
                  </span>
                )}
              </div>
              <h3 className="mt-3 text-xl font-semibold tracking-tight sm:text-2xl">
                {exam.title}
              </h3>
              <p className="mt-2 max-w-2xl leading-7 text-[#45667a]">
                {exam.summary}
              </p>
              <dl className="mt-5 grid gap-3 text-sm text-[#45667a] sm:grid-cols-3">
                <div className="border-t border-[#bae6fd] pt-3">
                  <dt className="font-semibold text-[#123047]">Chuyên đề</dt>
                  <dd className="mt-1">{exam.topic}</dd>
                </div>
                <div className="border-t border-[#bae6fd] pt-3">
                  <dt className="font-semibold text-[#123047]">Số câu</dt>
                  <dd className="mt-1">{exam.question_count} câu</dd>
                </div>
                <div className="border-t border-[#bae6fd] pt-3">
                  <dt className="font-semibold text-[#123047]">Thời lượng</dt>
                  <dd className="mt-1">{exam.duration_minutes} phút</dd>
                </div>
              </dl>
            </div>
            <button
              className="inline-flex min-h-11 items-center justify-center rounded-md bg-[#123047] px-5 py-2 font-semibold text-white hover:bg-[#0284c7] lg:min-w-32"
              onClick={() => setLoginReturnTo(`/exams/${exam.slug}`)}
              type="button"
            >
              Làm bài
            </button>
          </article>
        ))}
      </div>
    );
  }

  return (
    <>
      {content}
      <LoginModal
        onClose={() => setLoginReturnTo(null)}
        open={loginReturnTo !== null}
        returnTo={loginReturnTo ?? "/exams"}
      />
    </>
  );
}
