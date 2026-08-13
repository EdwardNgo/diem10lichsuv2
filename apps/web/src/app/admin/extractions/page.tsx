import { AdminExtractions } from "@/components/admin-extractions";
import { AdminShell } from "@/components/admin-shell";

export default function AdminExtractionsPage() {
  return (
    <AdminShell
      activePath="/admin/extractions"
      description="Chọn tài liệu nguồn đã upload để parser trích xuất tiêu đề, câu hỏi và lời giải thành bản nháp."
      title="Trích xuất bản nháp"
    >
      <AdminExtractions />
    </AdminShell>
  );
}
