import { redirect } from "next/navigation";

export default function LegacyAdminDraftsPage() {
  redirect("/admin/publishing");
}
