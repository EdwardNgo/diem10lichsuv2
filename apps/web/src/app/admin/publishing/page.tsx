import { AdminDrafts } from "@/components/admin-drafts";
import { AdminShell } from "@/components/admin-shell";

export default function AdminPublishingPage() {
  return (
    <AdminShell
      activePath="/admin/publishing"
      description="Rà soát metadata, câu hỏi và xuất bản các bản nháp đã trích xuất hoặc soạn thủ công."
      title="Xuất bản đề"
    >
      <div className="grid gap-5 border border-[#bae6fd] bg-white p-5">
        <AdminDrafts />
      </div>
    </AdminShell>
  );
}
