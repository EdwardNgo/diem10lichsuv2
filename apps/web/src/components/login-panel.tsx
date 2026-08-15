"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { LoginModal } from "@/components/login-modal";
import { safeReturnPath } from "@/lib/auth-links";

type LoginState =
  | { kind: "loading" }
  | { kind: "anonymous" }
  | { kind: "authenticated" };

export function LoginPanel() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnTo = safeReturnPath(searchParams.get("return_to") ?? "/exams");
  const authError = searchParams.get("auth_error");
  const [state, setState] = useState<LoginState>({ kind: "loading" });

  const loadUser = useCallback(async (signal?: AbortSignal) => {
    try {
      const response = await fetch("/v1/auth/me", {
        credentials: "same-origin",
        signal,
      });
      if (response.status === 401) {
        setState({ kind: "anonymous" });
        return false;
      }
      if (!response.ok) {
        throw new Error("Không thể tải phiên đăng nhập");
      }
      setState({ kind: "authenticated" });
      return true;
    } catch {
      if (signal?.aborted !== true) {
        setState({ kind: "anonymous" });
      }
      return false;
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => {
      void loadUser(controller.signal);
    }, 0);
    return () => {
      window.clearTimeout(timeoutId);
      controller.abort();
    };
  }, [loadUser]);

  useEffect(() => {
    if (state.kind === "authenticated") {
      router.replace(returnTo);
      router.refresh();
    }
  }, [returnTo, router, state.kind]);

  if (state.kind === "authenticated") {
    return (
      <div className="fixed inset-0 z-[100] grid place-items-center bg-[#123047]/55 px-5">
        <div className="rounded-2xl border border-[#bae6fd] bg-white px-5 py-4 text-sm font-semibold text-[#123047]">
          Đã đăng nhập. Đang chuyển tới trang của bạn...
        </div>
      </div>
    );
  }

  return (
    <>
      {state.kind === "loading" ? (
        <div className="fixed inset-0 z-[90] grid place-items-center bg-[#123047]/35 px-5">
          <div className="rounded-2xl border border-[#bae6fd] bg-white px-5 py-4 text-sm font-semibold text-[#123047]">
            Đang chuẩn bị đăng nhập...
          </div>
        </div>
      ) : null}
      <LoginModal
        errorCode={authError}
        onClose={() => router.push(returnTo)}
        open={state.kind === "anonymous"}
        returnTo={returnTo}
      />
    </>
  );
}
