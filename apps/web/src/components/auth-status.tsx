"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { LoginModal } from "@/components/login-modal";

type AuthUser = {
  avatar_url: string | null;
  email: string;
  display_name: string;
  role: "student" | "admin";
};

type AuthState =
  | { kind: "loading" }
  | { kind: "anonymous" }
  | { kind: "authenticated"; user: AuthUser };

export function AuthStatus({
  loginReturnTo,
  logoutRedirectTo = "/",
}: {
  loginReturnTo?: string;
  logoutRedirectTo?: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [state, setState] = useState<AuthState>({ kind: "loading" });
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);
  const returnTo = loginReturnTo ?? pathname ?? "/exams";

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
            throw new Error("Không thể tải phiên đăng nhập");
          }

          const data: { user: AuthUser } = await response.json();
          setState({ kind: "authenticated", user: data.user });
        } catch {
          if (!controller.signal.aborted) {
            setState({ kind: "anonymous" });
          }
        }
      })();
    }, 0);

    return () => {
      window.clearTimeout(timeoutId);
      controller.abort();
    };
  }, []);

  async function logout() {
    try {
      setIsLoggingOut(true);
      await fetch("/v1/auth/logout", {
        credentials: "same-origin",
        method: "POST",
      });
      setState({ kind: "anonymous" });
      router.push(logoutRedirectTo);
      router.refresh();
    } finally {
      setIsLoggingOut(false);
    }
  }

  if (state.kind === "loading") {
    return (
      <span className="rounded-md border border-[#bae6fd] px-4 py-2.5 text-[#45667a]">
        Đang kiểm tra...
      </span>
    );
  }

  if (state.kind === "authenticated") {
    return (
      <div className="flex flex-wrap items-center gap-3">
        <Link className="font-semibold hover:text-[#0284c7]" href="/history">
          Lịch sử
        </Link>
        {state.user.role === "admin" ? (
          <Link className="font-semibold text-[#0284c7]" href="/admin">
            Quản trị
          </Link>
        ) : null}
        <span className="flex min-w-0 items-center gap-2 text-[#45667a]">
          {state.user.avatar_url === null ? (
            <span
              aria-hidden="true"
              className="grid size-8 shrink-0 place-items-center rounded-full bg-[#e0f2fe] text-xs font-semibold text-[#0369a1]"
            >
              {state.user.display_name.slice(0, 1).toUpperCase()}
            </span>
          ) : (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              alt=""
              className="size-8 shrink-0 rounded-full"
              height={32}
              src={state.user.avatar_url}
              width={32}
            />
          )}
          <span className="hidden max-w-36 truncate sm:inline">
            {state.user.display_name}
          </span>
        </span>
        <button
          className="rounded-md bg-[#123047] px-4 py-2.5 text-white hover:bg-[#0284c7] disabled:cursor-wait disabled:opacity-70"
          disabled={isLoggingOut}
          onClick={() => void logout()}
          type="button"
        >
          {isLoggingOut ? "Đang đăng xuất..." : "Đăng xuất"}
        </button>
      </div>
    );
  }

  return (
    <>
      <button
        className="rounded-md bg-[#123047] px-4 py-2.5 text-white hover:bg-[#0284c7]"
        onClick={() => setLoginOpen(true)}
        type="button"
      >
        Đăng nhập
      </button>
      <LoginModal
        onClose={() => setLoginOpen(false)}
        open={loginOpen}
        returnTo={returnTo}
      />
    </>
  );
}
