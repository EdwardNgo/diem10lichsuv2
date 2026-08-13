import Link from "next/link";

import { FeaturedExams } from "@/components/featured-exams";
import { LandingSteps } from "@/components/landing-steps";
import { SiteHeader } from "@/components/site-header";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#f2fbff] text-[#123047]">
      <a
        className="absolute left-4 top-4 z-10 -translate-y-20 rounded-md bg-[#123047] px-4 py-3 text-sm font-semibold text-white transition-transform focus:translate-y-0"
        href="#noi-dung-chinh"
      >
        Bỏ qua điều hướng
      </a>
      <SiteHeader active="home" />

      <main id="noi-dung-chinh">
        <section className="mx-auto grid max-w-6xl gap-12 px-5 py-20 sm:px-8 lg:grid-cols-[1.04fr_0.96fr] lg:py-24">
          <div className="max-w-2xl">
            <p className="mb-5 text-sm font-semibold tracking-[0.16em] text-[#0284c7]">
              ÔN THI THPT QUỐC GIA
            </p>
            <h1 className="text-4xl font-semibold leading-tight tracking-tight sm:text-6xl">
              Luyện đề Lịch sử theo đúng nhịp thi.
            </h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-[#45667a] sm:text-lg sm:leading-8">
              Làm bài có thời gian, tự lưu đáp án và xem lại lời giải sau khi
              nộp. Mỗi lần luyện đều được giữ trong lịch sử theo từng đề.
            </p>
            <div className="mt-9">
              <Link
                className="inline-flex min-h-12 items-center justify-center rounded-md bg-[#0284c7] px-6 py-3 font-semibold text-white hover:bg-[#0369a1]"
                href="/exams"
              >
                Làm đề ngay
              </Link>
            </div>
          </div>

          <aside className="relative overflow-hidden border border-[#bae6fd] bg-white p-5 shadow-[0_24px_80px_rgba(2,132,199,0.14)] sm:p-7">
            <div
              aria-hidden="true"
              className="absolute -right-16 -top-16 size-48 rounded-full bg-[#bae6fd]"
            />
            <div
              aria-hidden="true"
              className="absolute -bottom-20 left-8 size-40 rounded-full bg-[#e0f2fe]"
            />
            <div className="relative">
              <div className="flex items-center justify-between gap-4">
                <p className="text-sm font-semibold tracking-[0.14em] text-[#0284c7]">
                  PHIÊN ÔN TẬP MẪU
                </p>
                <span className="rounded-full bg-[#e0f2fe] px-3 py-1 text-xs font-semibold text-[#0369a1]">
                  50 phút
                </span>
              </div>
              <div className="hero-card-float mt-6 border border-[#bae6fd] bg-[#f8fcff] p-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#45667a]">
                      Đề ôn luyện
                    </p>
                    <h2 className="mt-2 text-2xl font-semibold leading-snug">
                      Việt Nam 1945-1975
                    </h2>
                  </div>
                  <div className="grid size-16 place-items-center rounded-full bg-[#0284c7] text-lg font-semibold text-white">
                    8.5
                  </div>
                </div>
                <div className="mt-6 h-2 overflow-hidden rounded-full bg-[#dbeafe]">
                  <div className="hero-meter-fill h-full rounded-full bg-[#0284c7]" />
                </div>
                <div className="mt-5 grid grid-cols-3 gap-3 text-center text-sm">
                  {[
                    ["28", "câu"],
                    ["2", "phần"],
                    ["10", "điểm"],
                  ].map(([value, label]) => (
                    <div className="bg-white p-3" key={label}>
                      <p className="text-xl font-semibold">{value}</p>
                      <p className="mt-1 text-xs uppercase tracking-[0.12em] text-[#45667a]">
                        {label}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
              <div className="hero-orbit-dot absolute right-6 top-28 size-4 rounded-full bg-[#38bdf8]" />
              <div className="hero-card-float hero-card-float-delay ml-auto mt-4 max-w-[15rem] border border-[#bae6fd] bg-white p-4 shadow-[0_18px_44px_rgba(2,132,199,0.12)]">
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#0284c7]">
                  Sau khi nộp
                </p>
                <p className="mt-2 text-sm leading-6 text-[#45667a]">
                  Xem điểm từng phần, đáp án đúng và lời giải theo từng câu.
                </p>
              </div>
            </div>
          </aside>
        </section>

        <FeaturedExams />

        <section className="border-y border-[#bae6fd] bg-white" id="gioi-thieu">
          <div className="mx-auto grid max-w-6xl gap-8 px-5 py-16 sm:px-8 lg:grid-cols-[0.9fr_1.1fr]">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                Một nơi để luyện đề, xem lại và làm lại.
              </h2>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              {[
                ["Kho đề có bộ lọc", "Lọc theo chủ đề và năm để tìm đúng đề cần luyện."],
                ["Đúng cấu trúc mới", "Phần I trắc nghiệm ABCD và Phần II đúng sai theo tư liệu."],
                ["Không mất bài", "Đáp án được tự lưu, thời gian tạm dừng khi rời màn hình làm bài."],
                ["Xem lại theo đề", "Lịch sử gom theo từng đề để so sánh các lần làm rõ hơn."],
              ].map(([title, body]) => (
                <article className="border border-[#bae6fd] bg-[#f8fdff] p-5" key={title}>
                  <h3 className="font-semibold">{title}</h3>
                  <p className="mt-2 text-sm leading-6 text-[#45667a]">{body}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <LandingSteps />
      </main>

      <footer className="border-t border-[#bae6fd] bg-white px-5 py-10 text-sm text-[#45667a] sm:px-8">
        <div className="mx-auto grid max-w-6xl gap-8 md:grid-cols-[1.2fr_0.8fr]">
          <div>
            <p className="text-lg font-semibold tracking-tight text-[#123047]">
              Điểm 10 <span className="text-[#0284c7]">Lịch sử</span>
            </p>
            <p className="mt-3 max-w-sm leading-6">
              Nền tảng luyện đề Lịch sử THPT với chấm điểm, lời giải và lịch sử
              làm bài theo từng đề.
            </p>
          </div>
          <nav aria-label="Liên kết footer" className="grid gap-2">
            <a className="hover:text-[#0284c7]" href="#gioi-thieu">
              Giới thiệu
            </a>
            <Link className="hover:text-[#0284c7]" href="/privacy">
              Chính sách bảo mật
            </Link>
            <Link className="hover:text-[#0284c7]" href="/terms">
              Điều khoản sử dụng
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
