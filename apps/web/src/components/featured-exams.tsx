"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ExamCard, type ExamCardData } from "@/components/exam-card";
import { LoginRequiredDialog } from "@/components/login-required";

type FeaturedState =
  | { kind: "loading" }
  | { kind: "ready"; exams: ExamCardData[]; total: number; authenticated: boolean }
  | { kind: "empty" }
  | { kind: "error" };

export function FeaturedExams() {
  const [state, setState] = useState<FeaturedState>({ kind: "loading" });
  const [loginPrompt, setLoginPrompt] = useState<ExamCardData | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadFeatured() {
      try {
        const authResponse = await fetch("/v1/auth/me", {
          credentials: "same-origin",
          signal: controller.signal,
        });
        const authenticated = authResponse.ok;

        const examsResponse = await fetch("/v1/public/exams?page_size=3", {
          signal: controller.signal,
        });
        if (!examsResponse.ok) {
          throw new Error("Không thể tải đề nổi bật.");
        }

        const data: {
          items: ExamCardData[];
          total: number;
        } = await examsResponse.json();

        if (data.items.length === 0) {
          setState({ kind: "empty" });
          return;
        }

        setState({
          kind: "ready",
          exams: data.items,
          total: data.total,
          authenticated,
        });
      } catch {
        if (controller.signal.aborted) {
          return;
        }
        setState({ kind: "error" });
      }
    }

    void loadFeatured();
    return () => controller.abort();
  }, []);

  if (state.kind === "loading") {
    return (
      <section
        aria-labelledby="featured-exams-heading"
        className="border-y border-[#bae6fd] bg-white"
        id="de-noi-bat"
      >
        <div className="mx-auto max-w-6xl px-5 py-14 sm:px-8">
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }, (_, index) => (
              <div
                className="h-[17rem] animate-pulse rounded-2xl border border-[#dbeafe] bg-[#f8fcff]"
                key={index}
              />
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (state.kind === "empty") {
    return null;
  }

  if (state.kind === "error") {
    return (
      <section
        aria-labelledby="featured-exams-heading"
        className="border-y border-[#bae6fd] bg-white"
        id="de-noi-bat"
      >
        <div className="mx-auto max-w-6xl px-5 py-14 sm:px-8">
          <p className="text-[#45667a]">
            Chưa tải được đề nổi bật. Bạn vẫn có thể vào{" "}
            <Link className="font-semibold text-[#0284c7]" href="/exams">
              kho đề
            </Link>
            .
          </p>
        </div>
      </section>
    );
  }

  return (
    <section
      aria-labelledby="featured-exams-heading"
      className="border-y border-[#bae6fd] bg-white"
      id="de-noi-bat"
    >
      <div className="mx-auto max-w-6xl px-5 py-14 sm:px-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm font-semibold tracking-[0.16em] text-[#0284c7]">
              KHO ĐỀ THẬT
            </p>
            <h2
              className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl"
              id="featured-exams-heading"
            >
              Đề nổi bật
            </h2>
            <p className="mt-2 max-w-xl text-[#45667a]">
              {state.total} đề đã xuất bản, bắt đầu luyện ngay hoặc khám phá
              thêm trong kho đề.
            </p>
          </div>
          <Link
            className="inline-flex min-h-11 items-center justify-center rounded-xl border border-[#bae6fd] px-5 py-2 text-sm font-semibold text-[#123047] transition-colors hover:border-[#0284c7] hover:text-[#0284c7]"
            href="/exams"
          >
            Xem tất cả ({state.total})
          </Link>
        </div>

        <div className="mt-8 grid auto-rows-fr gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {state.exams.map((exam) => (
            <ExamCard
              authenticated={state.authenticated}
              exam={exam}
              key={exam.slug}
              onGuestSelect={setLoginPrompt}
            />
          ))}
        </div>
      </div>

      {loginPrompt === null ? null : (
        <LoginRequiredDialog
          body={`Sau khi đăng nhập, bạn sẽ quay lại đề "${loginPrompt.title}".`}
          onCancel={() => setLoginPrompt(null)}
          returnTo={`/exams/${loginPrompt.slug}`}
          title="Đăng nhập để xem chi tiết đề"
        />
      )}
    </section>
  );
}
