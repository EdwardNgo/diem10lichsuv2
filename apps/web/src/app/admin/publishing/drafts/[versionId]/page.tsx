import Link from "next/link";

import { AdminDraftEditor } from "@/components/admin-draft-editor";
import { AdminShell } from "@/components/admin-shell";

export default function AdminPublishingDraftPage() {
  return (
    <AdminShell
      activePath="/admin/publishing"
      description="Chỉnh metadata, câu hỏi và xuất bản bản nháp."
      title="Rà soát bản nháp"
    >
      <div className="mb-4">
        <Link
          className="text-sm font-semibold text-[#0284c7] hover:underline"
          href="/admin/publishing"
        >
          ← Quay lại danh sách bản nháp
        </Link>
      </div>
      <AdminDraftEditor />
    </AdminShell>
  );
}
