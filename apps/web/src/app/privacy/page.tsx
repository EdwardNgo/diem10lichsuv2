import Link from "next/link";

import { SiteHeader } from "@/components/site-header";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#f2fbff] text-[#123047]">
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-5 py-12 sm:px-8">
        <p className="text-sm font-semibold tracking-[0.16em] text-[#0284c7]">
          CHÍNH SÁCH BẢO MẬT
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight">
          Dữ liệu dùng để lưu tiến độ học tập
        </h1>
        <div className="mt-8 grid gap-6 rounded-3xl border border-[#bae6fd] bg-white p-6 leading-7 text-[#45667a] sm:p-8">
          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Dữ liệu Google
            </h2>
            <p className="mt-3">
              Khi bạn tiếp tục với Google, ứng dụng chỉ yêu cầu quyền
              <code className="mx-1 rounded bg-[#e0f2fe] px-1 py-0.5">
                openid
              </code>
              ,
              <code className="mx-1 rounded bg-[#e0f2fe] px-1 py-0.5">
                email
              </code>
              và
              <code className="mx-1 rounded bg-[#e0f2fe] px-1 py-0.5">
                profile
              </code>
              để tạo hồ sơ gồm định danh Google, email, tên hiển thị và ảnh đại
              diện.
            </p>
          </section>
          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Dữ liệu học tập
            </h2>
            <p className="mt-3">
              Ứng dụng lưu lượt làm bài, đáp án đã chọn, thời điểm nộp và điểm
              để bạn xem lại lịch sử theo từng đề. Dữ liệu này không được dùng
              để hiển thị đáp án trước khi bạn hoàn thành lượt làm.
            </p>
          </section>
          <section>
            <h2 className="text-xl font-semibold text-[#123047]">
              Yêu cầu xóa dữ liệu
            </h2>
            <p className="mt-3">
              Nếu cần xóa hồ sơ hoặc lịch sử làm bài, hãy liên hệ quản trị viên
              hệ thống đang vận hành website. Yêu cầu sẽ được xử lý theo phạm vi
              dữ liệu của tài khoản Google đã xác minh.
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
