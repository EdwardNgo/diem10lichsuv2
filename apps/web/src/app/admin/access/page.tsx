import { AdminAllowlist } from "@/components/admin-allowlist";
import { AdminShell } from "@/components/admin-shell";

export default function AdminAccessPage() {
  return (
    <AdminShell
      activePath="/admin/access"
      description="Chỉ email trong allowlist mới nhận vai trò admin khi đăng nhập Google."
      title="Cấp quyền"
    >
      <AdminAllowlist />
    </AdminShell>
  );
}
