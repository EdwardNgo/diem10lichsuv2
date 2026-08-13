import { AttemptTaker } from "@/components/attempt-taker";
import { SiteHeader } from "@/components/site-header";

export default function AttemptPage() {
  return (
    <div className="min-h-screen bg-[#f2fbff] text-[#123047]">
      <SiteHeader active="exams" />

      <main className="mx-auto max-w-6xl px-5 py-8 sm:px-8">
        <AttemptTaker />
      </main>
    </div>
  );
}
