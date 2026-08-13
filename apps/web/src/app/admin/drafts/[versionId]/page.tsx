import { redirect } from "next/navigation";

type LegacyDraftEditorPageProps = {
  params: Promise<{ versionId: string }>;
};

export default async function LegacyAdminDraftEditorPage({
  params,
}: LegacyDraftEditorPageProps) {
  const { versionId } = await params;
  redirect(`/admin/publishing/drafts/${versionId}`);
}
