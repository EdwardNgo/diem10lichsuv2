"use client";

import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";

import { loginHref } from "@/lib/auth-links";

type GateState =
  | { kind: "loading" }
  | { kind: "anonymous" }
  | { kind: "forbidden" }
  | { kind: "ready" };

export function AdminRequired({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [state, setState] = useState<GateState>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => {
      void (async () => {
        try {
          const response = await fetch("/v1/auth/me", {
            credentials: "same-origin",
            signal: controller.signal,
          });
          if (response.status === 401) {
            setState({ kind: "anonymous" });
            return;
          }
          if (!response.ok) {
            setState({ kind: "forbidden" });
            return;
          }

          const data: { user: { role: "student" | "admin" } } =
            await response.json();
          if (data.user.role !== "admin") {
            setState({ kind: "forbidden" });
            return;
          }

          setState({ kind: "ready" });
        } catch {
          if (!controller.signal.aborted) {
            setState({ kind: "forbidden" });
          }
        }
      })();
    }, 0);

    return () => {
      window.clearTimeout(timeoutId);
      controller.abort();
    };
  }, []);

  useEffect(() => {
    if (state.kind === "anonymous") {
      router.replace(loginHref(pathname || "/admin"));
      return;
    }
    if (state.kind === "forbidden") {
      router.replace("/exams");
    }
  }, [pathname, router, state.kind]);

  if (state.kind !== "ready") {
    return (
      <div className="grid min-h-screen place-items-center bg-[#f2fbff] px-5 text-[#45667a]">
        <p className="text-sm font-semibold">Đang kiểm tra quyền truy cập...</p>
      </div>
    );
  }

  return children;
}
