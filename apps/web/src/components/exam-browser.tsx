"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { ExamCard, type ExamCardData } from "@/components/exam-card";
import { LoginRequiredDialog } from "@/components/login-required";

type ExamFilters = {
  topics: { slug: string; name: string }[];
  years: number[];
  difficulties: string[];
};

type BrowserState =
  | { kind: "loading" }
  | {
      kind: "ready";
      exams: ExamCardData[];
      total: number;
      page: number;
      pageSize: number;
      filters: ExamFilters;
      authenticated: boolean;
    }
  | { kind: "error"; message: string };

const pageSize = 9;

export function ExamBrowser() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [state, setState] = useState<BrowserState>({ kind: "loading" });
  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const [loginPrompt, setLoginPrompt] = useState<ExamCardData | null>(null);

  const queryString = useMemo(() => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("difficulty");
    return params.toString();
  }, [searchParams]);

  const loadExams = useCallback(async () => {
    try {
      setState({ kind: "loading" });
      const authResponse = await fetch("/v1/auth/me", {
        credentials: "same-origin",
      });
      const authenticated = authResponse.ok;
      const params = new URLSearchParams(queryString);
      params.set("page_size", pageSize.toString());
      params.delete("difficulty");

      const [filtersResponse, examsResponse] = await Promise.all([
        fetch("/v1/public/exams/filters"),
        fetch(
          `/${authenticated ? "v1/student/exams" : "v1/public/exams"}?${params.toString()}`,
          { credentials: "same-origin" },
        ),
      ]);

      if (!filtersResponse.ok || !examsResponse.ok) {
        throw new Error("Không thể tải kho đề.");
      }

      const filters: ExamFilters = await filtersResponse.json();
      const data: {
        items: ExamCardData[];
        page: number;
        page_size: number;
        total: number;
      } = await examsResponse.json();
      setState({
        kind: "ready",
        exams: data.items,
        total: data.total,
        page: data.page,
        pageSize: data.page_size,
        filters,
        authenticated,
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
      void loadExams();
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, [loadExams]);

  function updateQuery(nextValues: Record<string, string>) {
    const params = new URLSearchParams(queryString);
    Object.entries(nextValues).forEach(([key, value]) => {
      if (value.trim() === "") {
        params.delete(key);
      } else {
        params.set(key, value);
      }
    });
    params.delete("page");
    params.delete("difficulty");
    router.push(params.toString() ? `/exams?${params.toString()}` : "/exams");
  }

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    updateQuery({ search });
  }

  function changePage(page: number) {
    const params = new URLSearchParams(queryString);
    params.set("page", page.toString());
    router.push(`/exams?${params.toString()}`);
  }

  function clearFilters() {
    setSearch("");
    router.push("/exams");
  }

  if (state.kind === "loading") {
    return (
      <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }, (_, index) => (
          <div
            className="h-[17rem] animate-pulse rounded-2xl border border-[#dbeafe] bg-white"
            key={index}
          />
        ))}
      </div>
    );
  }

  if (state.kind === "error") {
    return (
      <div className="rounded-2xl border border-[#fecaca] bg-[#fff1f2] p-8">
        <p className="font-semibold text-[#7f1d1d]">{state.message}</p>
        <button
          className="mt-5 rounded-xl border border-[#991b1b] px-5 py-3 font-semibold"
          onClick={() => void loadExams()}
          type="button"
        >
          Thử lại
        </button>
      </div>
    );
  }

  const totalPages = Math.max(1, Math.ceil(state.total / state.pageSize));
  const hasActiveFilters =
    searchParams.get("search") !== null ||
    searchParams.get("topic") !== null ||
    searchParams.get("year") !== null;

  return (
    <div className="grid gap-8">
      <form
        className="grid gap-3 rounded-2xl border border-[#dbeafe] bg-white p-4 shadow-[0_8px_30px_rgba(2,132,199,0.05)] lg:grid-cols-[minmax(0,1fr)_180px_140px_auto]"
        onSubmit={(event) => submitSearch(event)}
      >
        <input
          className="min-h-12 rounded-xl border border-[#bae6fd] px-4 outline-none transition-colors focus:border-[#0284c7]"
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Tìm theo tiêu đề đề thi..."
          type="search"
          value={search}
        />
        <select
          className="min-h-12 rounded-xl border border-[#bae6fd] bg-white px-4"
          onChange={(event) => updateQuery({ topic: event.target.value })}
          value={searchParams.get("topic") ?? ""}
        >
          <option value="">Tất cả chủ đề</option>
          {state.filters.topics.map((topic) => (
            <option key={topic.slug} value={topic.slug}>
              {topic.name}
            </option>
          ))}
        </select>
        <select
          className="min-h-12 rounded-xl border border-[#bae6fd] bg-white px-4"
          onChange={(event) => updateQuery({ year: event.target.value })}
          value={searchParams.get("year") ?? ""}
        >
          <option value="">Tất cả năm</option>
          {state.filters.years.map((year) => (
            <option key={year} value={year.toString()}>
              {year}
            </option>
          ))}
        </select>
        <button
          className="rounded-xl bg-[#123047] px-5 py-3 font-semibold text-white transition-colors hover:bg-[#0284c7]"
          type="submit"
        >
          Tìm đề
        </button>
      </form>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-[#45667a]">
          {state.total === 0
            ? "Không có đề phù hợp"
            : `Hiển thị ${state.exams.length} / ${state.total} đề`}
        </p>
        {hasActiveFilters ? (
          <button
            className="rounded-full border border-[#bae6fd] px-4 py-2 text-sm font-semibold text-[#45667a] transition-colors hover:border-[#0284c7] hover:text-[#0284c7]"
            onClick={clearFilters}
            type="button"
          >
            Xóa bộ lọc
          </button>
        ) : null}
      </div>

      {state.exams.length === 0 ? (
        <div className="rounded-2xl border border-[#dbeafe] bg-white p-10 text-center">
          <p className="text-2xl font-semibold">Không tìm thấy đề phù hợp</p>
          <p className="mt-2 text-[#45667a]">
            Hãy thử từ khóa ngắn hơn hoặc xóa bộ lọc hiện tại.
          </p>
        </div>
      ) : (
        <div className="grid auto-rows-fr gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {state.exams.map((exam) => (
            <ExamCard
              authenticated={state.authenticated}
              exam={exam}
              key={exam.slug}
              onGuestSelect={setLoginPrompt}
            />
          ))}
        </div>
      )}

      <div className="flex items-center justify-between rounded-2xl border border-[#dbeafe] bg-white px-4 py-3 text-sm font-semibold text-[#45667a]">
        <button
          className="rounded-xl border border-[#bae6fd] px-4 py-2 transition-colors hover:border-[#0284c7] hover:text-[#0284c7] disabled:opacity-50"
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
          className="rounded-xl border border-[#bae6fd] px-4 py-2 transition-colors hover:border-[#0284c7] hover:text-[#0284c7] disabled:opacity-50"
          disabled={state.page >= totalPages}
          onClick={() => changePage(state.page + 1)}
          type="button"
        >
          Trang sau
        </button>
      </div>

      {loginPrompt === null ? null : (
        <LoginRequiredDialog
          body={`Sau khi đăng nhập, bạn sẽ quay lại đề "${loginPrompt.title}" và hệ thống có thể lưu trạng thái làm bài cho tài khoản của bạn.`}
          onCancel={() => setLoginPrompt(null)}
          returnTo={`/exams/${loginPrompt.slug}`}
          title="Đăng nhập để xem chi tiết đề"
        />
      )}
    </div>
  );
}
