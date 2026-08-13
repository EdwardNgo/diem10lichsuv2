import Link from "next/link";

import { SiteHeader } from "@/components/site-header";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-[#f2fbff] text-[#123047]">
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-5 py-12 sm:px-8">
        <p className="text-sm font-semibold tracking-[0.16em] text-[#0284c7]">
          ĐIỀU KHOẢN SỬ DỤNG
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight">
          Sử dụng Điểm 10 Lịch sử để ôn tập
        </h1>
        <div className="mt-8 grid gap-6 rounded-3xl border border-[#bae6fd] bg-white p-6 leading-7 text-[#45667a] sm:p-8">
          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Tài khoản đăng nhập
            </h2>
            <p className="mt-3">
              Bạn cần dùng tài khoản Google có email đã xác minh để lưu lượt làm
              và xem lại lịch sử học tập. Bạn chịu trách nhiệm bảo vệ quyền truy
              cập vào tài khoản Google của mình.
            </p>
          </section>
          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Nội dung ôn tập
            </h2>
            <p className="mt-3">
              Đề thi, câu hỏi, đáp án và lời giải chỉ phục vụ mục đích học tập.
              Không sao chép, phân phối lại hoặc dùng nội dung để gây nhiễu hệ
              thống.
            </p>
          </section>
          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Hành vi an toàn
            </h2>
            <p className="mt-3">
              Không cố truy cập tài khoản, lượt làm, đề nháp hoặc khu vực quản
              trị không thuộc quyền của bạn. Backend luôn kiểm tra phân quyền
              cho các hành động đặc quyền.
            </p>
          </section>
        </div>
        <Link
          className="mt-8 inline-flex font-semibold text-[#0284c7]"
          href="/login"
        >
          Quay lại đăng nhập
        </Link>
      </main>
    </div>
  );
}
