"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";

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

function navIsActive(
  pathname: string,
  href: "/exams" | "/history" | "/admin",
) {
  if (href === "/exams") {
    return (
      pathname === "/exams" ||
      pathname.startsWith("/exams/") ||
      pathname.startsWith("/attempts/")
    );
  }
  if (href === "/admin") {
    return pathname === "/admin" || pathname.startsWith("/admin/");
  }
  return pathname === "/history" || pathname.startsWith("/history/");
}

function menuItemClass(active: boolean) {
  return `block rounded-md px-3 py-2.5 text-sm font-medium ${
    active
      ? "bg-[#e0f2fe] text-[#0284c7]"
      : "text-[#123047] hover:bg-[#f2fbff] hover:text-[#0284c7]"
  }`;
}

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
  const [menuOpen, setMenuOpen] = useState(false);
  const [menuPath, setMenuPath] = useState(pathname);
  const menuId = useId();
  const menuRootRef = useRef<HTMLDivElement>(null);
  const returnTo = loginReturnTo ?? pathname ?? "/exams";

  if (menuPath !== pathname) {
    setMenuPath(pathname);
    setMenuOpen(false);
  }

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

  useEffect(() => {
    if (!menuOpen) {
      return;
    }

    function onPointerDown(event: PointerEvent) {
      if (
        menuRootRef.current !== null &&
        !menuRootRef.current.contains(event.target as Node)
      ) {
        setMenuOpen(false);
      }
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    }

    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [menuOpen]);

  async function logout() {
    try {
      setIsLoggingOut(true);
      setMenuOpen(false);
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
      <span
        aria-label="Đang kiểm tra đăng nhập"
        className="size-9 rounded-full border border-[#bae6fd] bg-[#f2fbff]"
      />
    );
  }

  if (state.kind === "authenticated") {
    const user = state.user;

    return (
      <div className="relative" ref={menuRootRef}>
        <button
          aria-controls={menuId}
          aria-expanded={menuOpen}
          aria-haspopup="true"
          aria-label={`Tài khoản ${user.display_name}`}
          className="flex items-center gap-2 rounded-full border border-[#bae6fd] bg-white py-1 pl-1 pr-3 text-left hover:border-[#7dd3fc]"
          onClick={() => setMenuOpen((open) => !open)}
          type="button"
        >
          {user.avatar_url === null ? (
            <span
              aria-hidden="true"
              className="grid size-8 shrink-0 place-items-center rounded-full bg-[#e0f2fe] text-xs font-semibold text-[#0369a1]"
            >
              {user.display_name.slice(0, 1).toUpperCase()}
            </span>
          ) : (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              alt=""
              className="size-8 shrink-0 rounded-full"
              height={32}
              src={user.avatar_url}
              width={32}
            />
          )}
          <span className="hidden max-w-36 truncate text-sm font-medium sm:inline">
            {user.display_name}
          </span>
          <span
            aria-hidden="true"
            className={`grid size-3 place-items-center ${menuOpen ? "rotate-180" : ""}`}
          >
            <span className="size-0 border-x-4 border-t-[5px] border-x-transparent border-t-[#45667a]" />
          </span>
        </button>
        {menuOpen ? (
          <div
            className="absolute right-0 z-50 mt-2 w-56 rounded-xl border border-[#bae6fd] bg-white p-2 shadow-[0_18px_44px_rgba(2,132,199,0.12)]"
            id={menuId}
          >
            <div className="border-b border-[#bae6fd] px-3 py-2">
              <p className="truncate text-sm font-semibold">{user.display_name}</p>
              <p className="truncate text-xs text-[#45667a]">{user.email}</p>
            </div>
            <nav aria-label="Tài khoản" className="mt-2 grid gap-0.5">
              <Link
                className={menuItemClass(navIsActive(pathname, "/exams"))}
                href="/exams"
              >
                Kho đề
              </Link>
              <Link
                className={menuItemClass(navIsActive(pathname, "/history"))}
                href="/history"
              >
                Lịch sử làm bài
              </Link>
              {user.role === "admin" ? (
                <Link
                  className={menuItemClass(navIsActive(pathname, "/admin"))}
                  href="/admin"
                >
                  Quản trị
                </Link>
              ) : null}
            </nav>
            <div className="mt-2 border-t border-[#bae6fd] pt-2">
              <button
                className="block w-full rounded-md px-3 py-2.5 text-left text-sm font-medium text-[#123047] hover:bg-[#f2fbff] hover:text-[#0284c7] disabled:cursor-wait disabled:opacity-70"
                disabled={isLoggingOut}
                onClick={() => void logout()}
                type="button"
              >
                {isLoggingOut ? "Đang đăng xuất..." : "Đăng xuất"}
              </button>
            </div>
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 text-sm font-medium">
      <Link
        className={
          navIsActive(pathname, "/exams")
            ? "text-[#0284c7]"
            : "hover:text-[#0284c7]"
        }
        href="/exams"
      >
        Kho đề
      </Link>
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
    </div>
  );
}
