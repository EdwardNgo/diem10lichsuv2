import Link from "next/link";

import { AdminShell, adminLinks } from "@/components/admin-shell";

export default function AdminPage() {
  return (
    <AdminShell
      description="Chọn một mục quản trị để cấp quyền, tải tài liệu nguồn, trích xuất bản nháp hoặc xuất bản đề."
      title="Quản trị"
    >
      <div className="grid gap-4 sm:grid-cols-2">
        {adminLinks.map((link) => (
          <Link
            className="grid gap-2 border border-[#bae6fd] bg-white p-5 transition hover:border-[#0284c7] hover:bg-[#f8fcff]"
            href={link.href}
            key={link.href}
          >
            <h2 className="text-xl font-semibold tracking-tight">{link.label}</h2>
            <p className="text-sm leading-6 text-[#45667a]">
              {link.href === "/admin/access"
                ? "Quản lý admin allowlist và quyền truy cập."
                : link.href === "/admin/source-documents"
                  ? "Upload DOCX/PDF nguồn lên storage riêng tư."
                  : link.href === "/admin/extractions"
                    ? "Parse tài liệu đã tải thành bản nháp để rà soát."
                    : "Rà soát metadata, câu hỏi và xuất bản đề."}
            </p>
          </Link>
        ))}
      </div>
    </AdminShell>
  );
}
