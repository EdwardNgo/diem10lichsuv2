"use client";

import Link from "next/link";
import { useEffect, useId, useRef, useState } from "react";

import { GoogleSignInButton } from "@/components/google-sign-in-button";
import { authErrorMessage } from "@/lib/auth-messages";
import { googleLoginHref, safeReturnPath } from "@/lib/auth-links";

type LoginModalProps = {
  body?: string;
  errorCode?: string | null;
  onClose?: () => void;
  open: boolean;
  returnTo: string;
  title?: string;
};

export function LoginModal({
  body = "",
  errorCode = null,
  onClose,
  open,
  returnTo,
  title = "Đăng nhập để lưu tiến độ học",
}: LoginModalProps) {
  const titleId = useId();
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const [connecting, setConnecting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [wasOpen, setWasOpen] = useState(open);
  const message = localError ?? authErrorMessage(errorCode);

  if (open !== wasOpen) {
    setWasOpen(open);
    if (open) {
      setConnecting(false);
      setLocalError(null);
    }
  }

  useEffect(() => {
    if (!open) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && onClose !== undefined && !connecting) {
        onClose();
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [connecting, onClose, open]);

  if (!open) {
    return null;
  }

  function startGoogleLogin() {
    setLocalError(null);
    setConnecting(true);
    window.location.assign(googleLoginHref(safeReturnPath(returnTo)));
  }

  return (
    <div
      aria-labelledby={titleId}
      aria-modal="true"
      className="fixed inset-0 z-[100] grid place-items-center bg-[#123047]/55 px-5"
      role="dialog"
    >
      <div className="w-full max-w-md rounded-3xl border border-[#bae6fd] bg-white p-6 shadow-[0_24px_80px_rgba(18,48,71,0.28)] sm:p-8">
        <p className="text-sm font-semibold tracking-[0.16em] text-[#0284c7]">
          TÀI KHOẢN HỌC TẬP
        </p>
        <h2 className="mt-3 text-2xl font-semibold tracking-tight" id={titleId}>
          {title}
        </h2>
        <p className="mt-3 leading-7 text-[#45667a]">{body}</p>

        {message === null ? null : (
          <div
            aria-live="polite"
            className="mt-5 rounded-2xl border border-[#fecaca] bg-[#fff1f2] p-4 text-sm leading-6 text-[#7f1d1d]"
          >
            {message}
          </div>
        )}

        <div className="mt-6">
          <GoogleSignInButton
            connecting={connecting}
            onClick={startGoogleLogin}
          />
        </div>

        {onClose === undefined ? null : (
          <button
            className="mt-3 inline-flex min-h-11 w-full items-center justify-center rounded-xl border border-[#bae6fd] px-5 py-2 font-semibold text-[#45667a] hover:border-[#0284c7] hover:text-[#0284c7] disabled:cursor-not-allowed disabled:opacity-50"
            disabled={connecting}
            onClick={onClose}
            ref={closeButtonRef}
            type="button"
          >
            Để sau
          </button>
        )}

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
    </div>
  );
}
