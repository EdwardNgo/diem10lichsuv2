"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";

import { loginHref } from "@/lib/auth-links";

type LoginRequiredCopy = {
  body: string;
  returnTo: string;
  title: string;
};

export function LoginRequiredPanel({ body, returnTo, title }: LoginRequiredCopy) {
  return (
    <div className="border border-[#bae6fd] bg-white p-8">
      <h1 className="text-3xl font-semibold">{title}</h1>
      <p className="mt-3 max-w-xl leading-7 text-[#45667a]">{body}</p>
      <Link
        className="mt-6 inline-flex min-h-11 items-center rounded-md bg-[#123047] px-5 py-3 font-semibold text-white hover:bg-[#0284c7]"
        href={loginHref(returnTo)}
      >
        Tiếp tục với Google
      </Link>
    </div>
  );
}

type LoginRequiredDialogProps = LoginRequiredCopy & {
  onCancel: () => void;
};

export function LoginRequiredDialog({
  body,
  onCancel,
  returnTo,
  title,
}: LoginRequiredDialogProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeButtonRef.current?.focus();

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onCancel();
      }
    }

    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [onCancel]);

  return (
    <div
      aria-labelledby="login-required-title"
      aria-modal="true"
      className="fixed inset-0 z-50 grid place-items-center bg-[#123047]/45 px-5"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onCancel();
        }
      }}
      role="dialog"
    >
      <div className="w-full max-w-md rounded-2xl border border-[#bae6fd] bg-white p-6 shadow-[0_24px_80px_rgba(18,48,71,0.2)]">
        <p className="text-sm font-semibold tracking-[0.14em] text-[#0284c7]">
          CẦN ĐĂNG NHẬP
        </p>
        <h2 className="mt-3 text-2xl font-semibold" id="login-required-title">
          {title}
        </h2>
        <p className="mt-3 leading-7 text-[#45667a]">{body}</p>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <Link
            className="inline-flex min-h-11 items-center justify-center rounded-xl bg-[#123047] px-5 py-2 font-semibold text-white hover:bg-[#0284c7]"
            href={loginHref(returnTo)}
          >
            Tiếp tục với Google
          </Link>
          <button
            className="inline-flex min-h-11 items-center justify-center rounded-xl border border-[#bae6fd] px-5 py-2 font-semibold text-[#45667a] hover:border-[#0284c7] hover:text-[#0284c7]"
            onClick={onCancel}
            ref={closeButtonRef}
            type="button"
          >
            Để sau
          </button>
        </div>
      </div>
    </div>
  );
}
