import type { Metadata } from "next";

import { ExamDetail } from "@/components/exam-detail";
import { SiteHeader } from "@/components/site-header";
import { withCanonical } from "@/lib/page-metadata";

type ExamDetailPageProps = {
  params: Promise<{ slug: string }>;
};

export async function generateMetadata({
  params,
}: ExamDetailPageProps): Promise<Metadata> {
  const { slug } = await params;
  return withCanonical(`/exams/${slug}`);
}

export default function ExamDetailPage() {
  return (
    <div className="min-h-screen bg-[#f2fbff] text-[#123047]">
      <SiteHeader />

      <main className="mx-auto max-w-6xl px-5 py-12 sm:px-8">
        <ExamDetail />
      </main>
    </div>
  );
}
