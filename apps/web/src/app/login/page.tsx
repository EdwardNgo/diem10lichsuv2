import { Suspense } from "react";

import { LoginPanel } from "@/components/login-panel";

export default function LoginPage() {
  return (
    <div className="min-h-dvh bg-[#f2fbff] text-[#123047]">
      <main>
        <Suspense
          fallback={
            <div className="fixed inset-0 z-[90] grid place-items-center bg-[#123047]/35 px-5">
              <div className="rounded-2xl border border-[#bae6fd] bg-white px-5 py-4 text-sm font-semibold text-[#123047]">
                Đang chuẩn bị đăng nhập...
              </div>
            </div>
          }
        >
          <LoginPanel />
        </Suspense>
      </main>
    </div>
  );
}
