"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { googleLoginHref, safeReturnPath } from "@/lib/auth-links";

type AuthUser = {
  email: string;
  display_name: string;
  role: "student" | "admin";
};

type LoginState =
  | { kind: "loading" }
  | { kind: "anonymous" }
  | { kind: "authenticated"; user: AuthUser };

const authErrorMessages: Record<string, string> = {
  account_conflict:
    "Email này đã được gắn với một hồ sơ khác. Hãy dùng đúng tài khoản Google đã đăng nhập trước đó.",
  cancelled: "Bạn đã hủy đăng nhập Google. Bạn có thể thử lại khi sẵn sàng.",
  invalid_profile:
    "Tài khoản Google chưa có email đã xác minh. Hãy kiểm tra tài khoản hoặc dùng tài khoản khác.",
  invalid_state: "Phiên đăng nhập đã hết hạn. Hãy bấm đăng nhập lại.",
  missing_code: "Google chưa trả đủ thông tin đăng nhập. Hãy thử lại.",
  provider_error: "Google chưa phản hồi thành công. Hãy thử lại sau ít phút.",
};

export function LoginPanel() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnTo = safeReturnPath(searchParams.get("return_to") ?? "/exams");
  const loginReturnTo = `/login?return_to=${encodeURIComponent(returnTo)}`;
  const authError = searchParams.get("auth_error");
  const [state, setState] = useState<LoginState>({ kind: "loading" });
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    async function loadUser() {
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
    }

    void loadUser();
    return () => controller.abort();
  }, []);

  async function logout() {
    try {
      setIsLoggingOut(true);
      await fetch("/v1/auth/logout", {
        credentials: "same-origin",
        method: "POST",
      });
      setState({ kind: "anonymous" });
      router.refresh();
    } finally {
      setIsLoggingOut(false);
    }
  }

  return (
    <section className="mx-auto grid max-w-6xl gap-8 px-5 py-12 sm:px-8 lg:grid-cols-[0.95fr_1.05fr] lg:py-20">
      <div className="rounded-3xl border border-[#bae6fd] bg-white p-6 shadow-[0_24px_80px_rgba(2,132,199,0.12)] sm:p-8">
        <p className="text-sm font-semibold tracking-[0.16em] text-[#0284c7]">
          TÀI KHOẢN HỌC TẬP
        </p>
        <h1 className="mt-4 text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">
          Lưu bài làm và lịch sử theo tài khoản của bạn.
        </h1>
        <p className="mt-5 max-w-xl leading-7 text-[#45667a]">
          Điểm 10 Lịch sử dùng Google để xác thực. Ứng dụng không lưu mật khẩu
          và chỉ nhận tên, email, ảnh đại diện để tạo hồ sơ học tập.
        </p>
        <dl className="mt-8 grid gap-4">
          {[
            ["Không mật khẩu", "Bạn đăng nhập trực tiếp qua Google."],
            ["Quay lại đúng chỗ", "Sau khi xác thực, hệ thống mở lại trang bạn chọn."],
            ["Phân quyền rõ ràng", "Admin chỉ được cấp khi email nằm trong allowlist."],
          ].map(([term, description]) => (
            <div className="border-t border-[#bae6fd] pt-4" key={term}>
              <dt className="font-semibold text-[#123047]">{term}</dt>
              <dd className="mt-1 text-sm leading-6 text-[#45667a]">
                {description}
              </dd>
            </div>
          ))}
        </dl>
      </div>

      <div className="self-start rounded-3xl border border-[#bae6fd] bg-[#f8fdff] p-6 sm:p-8">
        {authError === null ? null : (
          <div
            aria-live="polite"
            className="mb-6 rounded-2xl border border-[#fecaca] bg-[#fff1f2] p-4 text-sm leading-6 text-[#7f1d1d]"
          >
            {authErrorMessages[authError] ?? "Đăng nhập chưa hoàn tất. Hãy thử lại."}
          </div>
        )}

        {state.kind === "loading" ? (
          <div className="rounded-2xl border border-[#bae6fd] bg-white p-5 text-[#45667a]">
            Đang kiểm tra phiên đăng nhập...
          </div>
        ) : null}

        {state.kind === "authenticated" ? (
          <div className="rounded-2xl border border-[#bae6fd] bg-white p-5">
            <p className="font-semibold">Bạn đang đăng nhập</p>
            <p className="mt-2 text-sm leading-6 text-[#45667a]">
              {state.user.display_name} ({state.user.email})
            </p>
            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <Link
                className="inline-flex min-h-11 items-center justify-center rounded-xl bg-[#123047] px-5 py-2 font-semibold text-white hover:bg-[#0284c7]"
                href={returnTo}
              >
                Tiếp tục
              </Link>
              <button
                className="inline-flex min-h-11 items-center justify-center rounded-xl border border-[#bae6fd] px-5 py-2 font-semibold text-[#45667a] hover:border-[#0284c7] hover:text-[#0284c7] disabled:cursor-wait disabled:opacity-70"
                disabled={isLoggingOut}
                onClick={() => void logout()}
                type="button"
              >
                {isLoggingOut ? "Đang đăng xuất..." : "Đăng xuất"}
              </button>
            </div>
          </div>
        ) : null}

        {state.kind === "anonymous" ? (
          <div className="rounded-2xl border border-[#bae6fd] bg-white p-5">
            <h2 className="text-2xl font-semibold">Tiếp tục với Google</h2>
            <p className="mt-3 leading-7 text-[#45667a]">
              Sau khi Google xác thực xong, bạn có thể tiếp tục tới đúng trang
              đang chọn.
            </p>
            <Link
              className="mt-6 inline-flex min-h-12 w-full items-center justify-center rounded-xl border border-[#bae6fd] bg-white px-5 py-3 font-semibold text-[#123047] shadow-[0_10px_30px_rgba(18,48,71,0.08)] hover:border-[#0284c7]"
              href={googleLoginHref(loginReturnTo)}
            >
              <span
                aria-hidden="true"
                className="mr-3 grid size-6 place-items-center rounded-full border border-[#dbeafe] text-sm font-bold text-[#0284c7]"
              >
                G
              </span>
              Tiếp tục với Google
            </Link>
          </div>
        ) : null}

        <p className="mt-5 text-sm leading-6 text-[#45667a]">
          Khi tiếp tục, bạn đồng ý với{" "}
          <Link className="font-semibold text-[#0284c7]" href="/terms">
            Điều khoản sử dụng
          </Link>{" "}
          và{" "}
          <Link className="font-semibold text-[#0284c7]" href="/privacy">
            Chính sách bảo mật
          </Link>
          .
        </p>
      </div>
    </section>
  );
}
