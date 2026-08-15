"use client";

import Image from "next/image";

const steps = [
  {
    number: "01",
    title: "Chọn đề thi thử",
    body: "Chọn đề theo chủ đề hoặc năm, rồi bắt đầu một buổi thi thử.",
    image: "/images/landing-select-exam.gif",
    alt: "Animation quyển sách cho bước chọn đề",
  },
  {
    number: "02",
    title: "Làm bài",
    body: "Đồng hồ, tiến độ, đánh dấu xem lại và tự lưu giúp bạn tập trung vào câu hỏi.",
    image: "/images/landing-take-exam.gif",
    alt: "Animation cây bút cho bước làm bài",
  },
  {
    number: "03",
    title: "Rút kinh nghiệm",
    body: "Xem điểm từng phần, đáp án đúng và lời giải để biết phần cần ôn lại.",
    image: "/images/landing-review-result.gif",
    alt: "Animation quyển vở cho bước rút kinh nghiệm",
  },
] as const;

export function LandingSteps() {
  return (
    <section
      aria-labelledby="landing-steps-heading"
      className="relative overflow-hidden bg-[#123047] text-white"
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(2,132,199,0.22),transparent_55%),radial-gradient(circle_at_bottom_left,rgba(56,189,248,0.12),transparent_50%)]"
      />
      <div className="relative mx-auto max-w-6xl px-5 py-16 sm:px-8 sm:py-20">
        <div className="max-w-2xl">
          <p className="text-sm font-semibold tracking-[0.16em] text-[#7dd3fc]">
            QUY TRÌNH ÔN TẬP
          </p>
          <h2
            className="mt-3 text-2xl font-semibold tracking-tight sm:text-3xl"
            id="landing-steps-heading"
          >
            Ôn tập theo 3 bước
          </h2>
          <p className="mt-4 leading-7 text-[#bae6fd]">
            Chọn đề, làm bài, rồi xem lại lời giải để biết mình còn yếu ở đâu.
          </p>
        </div>

        <ol className="mt-10 grid gap-5 lg:grid-cols-3">
          {steps.map((step, index) => (
            <li className="relative" key={step.number}>
              {index < steps.length - 1 ? (
                <span
                  aria-hidden="true"
                  className="absolute left-1/2 top-12 hidden h-px w-full bg-[#0284c7]/40 lg:block"
                />
              ) : null}
              <article className="relative flex h-full flex-col rounded-2xl border border-[#0284c7]/30 bg-[#1a3d52]/80 p-6 backdrop-blur-sm">
                <div className="flex items-start justify-between gap-4">
                  <span className="text-sm font-semibold tracking-[0.2em] text-[#7dd3fc]">
                    BƯỚC {step.number}
                  </span>
                  <Image
                    alt={step.alt}
                    className="size-14 shrink-0 rounded-xl bg-[#123047]/60 p-2"
                    height={56}
                    src={step.image}
                    unoptimized
                    width={56}
                  />
                </div>
                <h3 className="mt-5 text-xl font-semibold">{step.title}</h3>
                <p className="mt-3 flex-1 text-sm leading-7 text-[#cbd5e1]">
                  {step.body}
                </p>
              </article>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
