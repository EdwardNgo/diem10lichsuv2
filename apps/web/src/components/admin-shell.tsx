import Link from "next/link";
import type { ReactNode } from "react";

import { SiteHeader } from "@/components/site-header";

const adminLinks = [
  { href: "/admin/access", label: "Cấp quyền" },
  { href: "/admin/source-documents", label: "Tải đề" },
  { href: "/admin/extractions", label: "Trích xuất bản nháp" },
  { href: "/admin/publishing", label: "Xuất bản đề" },
] as const;

type AdminShellProps = {
  activePath?: (typeof adminLinks)[number]["href"];
  children: ReactNode;
  description: string;
  title: string;
};

export function AdminShell({
  activePath,
  children,
  description,
  title,
}: AdminShellProps) {
  return (
    <div className="min-h-screen bg-[#f2fbff] text-[#123047]">
      <SiteHeader />

      <main className="mx-auto max-w-6xl px-5 py-12 sm:px-8">
        <p className="text-sm font-semibold tracking-[0.16em] text-[#0284c7]">
          QUẢN TRỊ
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-4 max-w-2xl leading-7 text-[#45667a]">{description}</p>

        <nav
          aria-label="Mục quản trị"
          className="mt-8 flex flex-wrap gap-2 border-b border-[#bae6fd] pb-4"
        >
          <Link
            className={`rounded-md px-4 py-2 text-sm font-semibold ${
              activePath === undefined
                ? "bg-[#123047] text-white"
                : "border border-[#bae6fd] text-[#123047] hover:bg-[#e0f2fe]"
            }`}
            href="/admin"
          >
            Tổng quan
          </Link>
          {adminLinks.map((link) => (
            <Link
              className={`rounded-md px-4 py-2 text-sm font-semibold ${
                activePath === link.href
                  ? "bg-[#123047] text-white"
                  : "border border-[#bae6fd] text-[#123047] hover:bg-[#e0f2fe]"
              }`}
              href={link.href}
              key={link.href}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <section className="mt-8 grid gap-8">{children}</section>
      </main>
    </div>
  );
}

export { adminLinks };
