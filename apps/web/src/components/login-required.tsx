"use client";

import { useState } from "react";

import { GoogleSignInButton } from "@/components/google-sign-in-button";
import { LoginModal } from "@/components/login-modal";
import { googleLoginHref, safeReturnPath } from "@/lib/auth-links";

type LoginRequiredCopy = {
  body: string;
  returnTo: string;
  title: string;
};

export function LoginRequiredPanel({ body, returnTo, title }: LoginRequiredCopy) {
  const [connecting, setConnecting] = useState(false);

  return (
    <div className="border border-[#bae6fd] bg-white p-8">
      <h1 className="text-3xl font-semibold">{title}</h1>
      <p className="mt-3 max-w-xl leading-7 text-[#45667a]">{body}</p>
      <div className="mt-6 max-w-sm">
        <GoogleSignInButton
          connecting={connecting}
          onClick={() => {
            setConnecting(true);
            window.location.assign(googleLoginHref(safeReturnPath(returnTo)));
          }}
        />
      </div>
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
  return (
    <LoginModal
      body={body}
      onClose={onCancel}
      open
      returnTo={returnTo}
      title={title}
    />
  );
}
