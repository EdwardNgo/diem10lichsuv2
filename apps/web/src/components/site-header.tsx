import Link from "next/link";

import { AuthStatus } from "@/components/auth-status";

type SiteHeaderProps = {
  active?: "home" | "exams" | "history" | "admin";
};

export function SiteHeader({ active }: SiteHeaderProps) {
  return (
    <header className="border-b border-[#bae6fd] bg-white/80">
      <nav
        aria-label="Điều hướng chính"
        className="mx-auto flex max-w-6xl flex-col gap-4 px-5 py-5 sm:px-8 md:flex-row md:items-center md:justify-between"
      >
        <Link className="text-lg font-semibold tracking-tight" href="/">
          Điểm 10 <span className="text-[#0284c7]">Lịch sử</span>
        </Link>
        <div className="flex flex-wrap items-center gap-4 text-sm font-medium">
          <Link
            className={
              active === "home" ? "text-[#0284c7]" : "hover:text-[#0284c7]"
            }
            href="/"
          >
            Trang chủ
          </Link>
          <Link
            className={
              active === "exams" ? "text-[#0284c7]" : "hover:text-[#0284c7]"
            }
            href="/exams"
          >
            Kho đề
          </Link>
          <AuthStatus />
        </div>
      </nav>
    </header>
  );
}
