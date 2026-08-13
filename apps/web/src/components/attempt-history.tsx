"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { LoginRequiredPanel } from "@/components/login-required";

type HistoryAttemptSummary = {
  attempt_id: string;
  attempt_number: number;
  status: string;
  score: number;
  correct_count: number;
  incorrect_count: number;
  unanswered_count: number;
  submitted_at: string | null;
  graded_at: string;
};

type HistoryExamGroup = {
  slug: string;
  title: string;
  attempt_count: number;
  best_score: number;
  latest_score: number;
  latest_submitted_at: string | null;
  can_retry: boolean;
  attempts: HistoryAttemptSummary[];
};

type HistoryState =
  | { kind: "loading" }
  | { kind: "login_required" }
  | {
      kind: "ready";
      items: HistoryExamGroup[];
      page: number;
      pageSize: number;
      total: number;
    }
  | { kind: "error"; message: string };

const pageSize = 10;

function formatScore(score: number) {
  return Number(score.toFixed(2)).toString();
}

function formatDate(value: string | null) {
  if (value === null) {
    return "Chưa ghi thời điểm";
  }
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function statusText(status: string) {
  return status === "expired_and_submitted" ? "Hết giờ" : "Đã nộp";
}

export function AttemptHistory() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [state, setState] = useState<HistoryState>({ kind: "loading" });
  const [expandedSlug, setExpandedSlug] = useState<string | null>(null);
  const queryString = useMemo(() => searchParams.toString(), [searchParams]);

  const loadHistory = useCallback(async () => {
    try {
      setState({ kind: "loading" });
      const params = new URLSearchParams(queryString);
      params.set("page_size", pageSize.toString());
      const response = await fetch(`/v1/student/attempts?${params.toString()}`, {
        credentials: "same-origin",
      });
      if (response.status === 401) {
        setState({ kind: "login_required" });
        return;
      }
      if (!response.ok) {
        throw new Error("Không thể tải lịch sử làm bài.");
      }
      const data: {
        items: HistoryExamGroup[];
        page: number;
        page_size: number;
        total: number;
      } = await response.json();
      setState({
        kind: "ready",
        items: data.items,
        page: data.page,
        pageSize: data.page_size,
        total: data.total,
      });
    } catch (error) {
      setState({
        kind: "error",
        message: error instanceof Error ? error.message : "Có lỗi xảy ra.",
      });
    }
  }, [queryString]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadHistory();
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, [loadHistory]);

  function changePage(page: number) {
    const params = new URLSearchParams(queryString);
    params.set("page", page.toString());
    router.push(`/history?${params.toString()}`);
  }

  if (state.kind === "loading") {
    return (
      <div className="border border-[#bae6fd] bg-white p-8 text-[#45667a]">
        Đang tải lịch sử làm bài...
      </div>
    );
  }

  if (state.kind === "login_required") {
    return (
      <LoginRequiredPanel
        body="Lịch sử làm bài được lưu theo tài khoản Google của bạn."
        returnTo="/history"
        title="Đăng nhập để xem lịch sử"
      />
    );
  }

  if (state.kind === "error") {
    return (
      <div className="border border-[#fecaca] bg-[#fff1f2] p-8">
        <p className="font-semibold text-[#7f1d1d]">{state.message}</p>
        <button
          className="mt-5 rounded-md border border-[#991b1b] px-5 py-3 font-semibold"
          onClick={() => void loadHistory()}
          type="button"
        >
          Thử lại
        </button>
      </div>
    );
  }

  const totalPages = Math.max(1, Math.ceil(state.total / state.pageSize));

  if (state.items.length === 0) {
    return (
      <div className="border border-[#bae6fd] bg-white p-8">
        <h1 className="text-3xl font-semibold">Chưa có lượt làm hoàn thành</h1>
        <p className="mt-3 max-w-xl leading-7 text-[#45667a]">
          Khi bạn nộp bài hoặc hết giờ, kết quả sẽ xuất hiện tại đây.
        </p>
        <Link
          className="mt-6 inline-flex rounded-md bg-[#123047] px-5 py-3 font-semibold text-white hover:bg-[#0284c7]"
          href="/exams"
        >
          Tìm đề để luyện
        </Link>
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      <div className="grid gap-4">
        {state.items.map((exam) => (
          <article
            className="border border-[#bae6fd] bg-white"
            key={exam.slug}
          >
            <button
              aria-expanded={expandedSlug === exam.slug}
              className="grid w-full gap-4 p-5 text-left transition-colors hover:bg-[#f8fdff] md:grid-cols-[1fr_auto]"
              onClick={() =>
                setExpandedSlug((current) =>
                  current === exam.slug ? null : exam.slug,
                )
              }
              type="button"
            >
              <div>
                <div className="flex flex-wrap gap-2 text-xs font-semibold uppercase tracking-[0.12em]">
                  <span className="bg-[#e0f2fe] px-3 py-1 text-[#0284c7]">
                    {exam.attempt_count} lượt làm
                  </span>
                  {!exam.can_retry ? (
                    <span className="border border-[#facc15] bg-[#fef9c3] px-3 py-1 text-[#854d0e]">
                      Không thể làm lại
                    </span>
                  ) : null}
                </div>
                <h2 className="mt-4 text-xl font-semibold tracking-tight">
                  {exam.title}
                </h2>
                <p className="mt-2 text-sm text-[#45667a]">
                  Lần gần nhất {formatDate(exam.latest_submitted_at)}
                </p>
              </div>
              <div className="grid gap-3 text-sm text-[#45667a] sm:grid-cols-2 md:min-w-72">
                <div>
                  <p className="text-3xl font-semibold text-[#123047]">
                    {formatScore(exam.best_score)}
                  </p>
                  <p>điểm cao nhất</p>
                </div>
                <div>
                  <p className="text-3xl font-semibold text-[#0369a1]">
                    {formatScore(exam.latest_score)}
                  </p>
                  <p>điểm gần nhất</p>
                </div>
              </div>
            </button>

            {expandedSlug === exam.slug ? (
              <div className="border-t border-[#bae6fd] p-5">
                <div className="grid gap-3">
                  {exam.attempts.map((attempt) => (
                    <div
                      className="grid gap-3 border border-[#bae6fd] bg-[#f8fdff] p-4 md:grid-cols-[1fr_auto]"
                      key={attempt.attempt_id}
                    >
                      <div>
                        <div className="flex flex-wrap gap-2 text-xs font-semibold uppercase tracking-[0.12em]">
                          <span className="bg-white px-3 py-1 text-[#0284c7]">
                            {statusText(attempt.status)}
                          </span>
                          <span className="border border-[#bae6fd] bg-white px-3 py-1 text-[#45667a]">
                            Lần {attempt.attempt_number}
                          </span>
                        </div>
                        <p className="mt-3 text-sm text-[#45667a]">
                          Hoàn thành lúc {formatDate(attempt.submitted_at)}
                        </p>
                      </div>
                      <div className="grid gap-3 text-sm text-[#45667a] sm:grid-cols-4 md:min-w-[28rem]">
                        <div>
                          <p className="text-2xl font-semibold text-[#123047]">
                            {formatScore(attempt.score)}
                          </p>
                          <p>điểm</p>
                        </div>
                        <div>
                          <p className="text-xl font-semibold text-[#166534]">
                            {attempt.correct_count}
                          </p>
                          <p>đúng</p>
                        </div>
                        <div>
                          <p className="text-xl font-semibold text-[#991b1b]">
                            {attempt.incorrect_count}
                          </p>
                          <p>sai</p>
                        </div>
                        <div>
                          <p className="text-xl font-semibold text-[#854d0e]">
                            {attempt.unanswered_count}
                          </p>
                          <p>bỏ trống</p>
                        </div>
                      </div>
                      <Link
                        className="inline-flex min-h-10 items-center justify-center rounded-md bg-[#123047] px-4 py-2 font-semibold text-white hover:bg-[#0284c7] md:col-start-2"
                        href={`/attempts/${attempt.attempt_id}`}
                      >
                        Xem kết quả
                      </Link>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </article>
        ))}
      </div>

      <div className="flex items-center justify-between border border-[#bae6fd] bg-white p-4 text-sm font-semibold text-[#45667a]">
        <button
          className="rounded-md border border-[#bae6fd] px-4 py-2 disabled:opacity-50"
          disabled={state.page <= 1}
          onClick={() => changePage(state.page - 1)}
          type="button"
        >
          Trang trước
        </button>
        <span>
          Trang {state.page}/{totalPages}
        </span>
        <button
          className="rounded-md border border-[#bae6fd] px-4 py-2 disabled:opacity-50"
          disabled={state.page >= totalPages}
          onClick={() => changePage(state.page + 1)}
          type="button"
        >
          Trang sau
        </button>
      </div>
    </div>
  );
}
