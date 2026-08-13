import { ExamDetail } from "@/components/exam-detail";
import { SiteHeader } from "@/components/site-header";

export default function ExamDetailPage() {
  return (
    <div className="min-h-screen bg-[#f2fbff] text-[#123047]">
      <SiteHeader active="exams" />

      <main className="mx-auto max-w-6xl px-5 py-12 sm:px-8">
        <ExamDetail />
      </main>
    </div>
  );
}
