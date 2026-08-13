import { Suspense } from "react";

import { AttemptHistory } from "@/components/attempt-history";
import { SiteHeader } from "@/components/site-header";

export default function HistoryPage() {
  return (
    <div className="min-h-screen bg-[#f2fbff] text-[#123047]">
      <SiteHeader active="history" />

      <main className="mx-auto max-w-6xl px-5 py-12 sm:px-8">
        <p className="text-sm font-semibold tracking-[0.16em] text-[#0284c7]">
          LỊCH SỬ LÀM BÀI
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight">
          Xem lại kết quả đã hoàn thành
        </h1>
        <p className="mt-4 max-w-2xl leading-7 text-[#45667a]">
          Các lượt làm đã nộp hoặc hết giờ được lưu theo tài khoản của bạn, mới
          nhất ở trên cùng.
        </p>

        <section className="mt-8">
          <Suspense
            fallback={
              <div className="border border-[#bae6fd] bg-white p-8 text-[#45667a]">
                Đang chuẩn bị lịch sử...
              </div>
            }
          >
            <AttemptHistory />
          </Suspense>
        </section>
      </main>
    </div>
  );
}
