import { Suspense } from "react";

import { LoginPanel } from "@/components/login-panel";
import { SiteHeader } from "@/components/site-header";

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-[#f2fbff] text-[#123047]">
      <SiteHeader />
      <main>
        <Suspense
          fallback={
            <div className="mx-auto max-w-6xl px-5 py-12 text-[#45667a] sm:px-8">
              Đang chuẩn bị đăng nhập...
            </div>
          }
        >
          <LoginPanel />
        </Suspense>
      </main>
    </div>
  );
}
