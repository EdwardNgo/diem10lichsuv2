import { AdminSourceDocumentsUpload } from "@/components/admin-source-documents-upload";
import { AdminShell } from "@/components/admin-shell";

export default function AdminSourceDocumentsPage() {
  return (
    <AdminShell
      activePath="/admin/source-documents"
      description="Upload DOCX hoặc PDF có lớp chữ lên storage riêng tư. Tài liệu chưa được parse thành bản nháp ở bước này."
      title="Tải đề"
    >
      <AdminSourceDocumentsUpload />
    </AdminShell>
  );
}
