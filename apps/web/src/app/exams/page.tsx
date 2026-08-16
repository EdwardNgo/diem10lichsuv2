import { Suspense } from "react";

import { ExamBrowser } from "@/components/exam-browser";
import { SiteHeader } from "@/components/site-header";

export default function ExamsPage() {
  return (
    <div className="min-h-screen bg-[#f2fbff] text-[#123047]">
      <SiteHeader />

      <main className="mx-auto max-w-6xl px-5 py-12 sm:px-8">
        <p className="text-sm font-semibold tracking-[0.16em] text-[#0284c7]">
          KHO ĐỀ THI THỬ
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight">
          Đề thi thử môn Lịch sử
        </h1>
        <p className="mt-4 max-w-2xl leading-7 text-[#45667a]">
          Lọc theo chủ đề và năm để tìm đúng phần cần ôn. Kho gồm đề tự biên
          soạn và đề tham khảo từ nguồn khác, theo cấu trúc kỳ thi tốt nghiệp
          THPT.
        </p>

        <section className="mt-8">
          <Suspense
            fallback={
              <div className="border border-[#bae6fd] bg-white p-8 text-[#45667a]">
                Đang chuẩn bị bộ lọc...
              </div>
            }
          >
            <ExamBrowser />
          </Suspense>
        </section>
      </main>
    </div>
  );
}
