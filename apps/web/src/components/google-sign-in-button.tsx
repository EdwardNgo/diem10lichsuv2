"use client";

// Official Google Identity branding asset.
const googleLogoUrl = "https://developers.google.com/identity/images/g-logo.png";

type GoogleSignInButtonProps = {
  connecting?: boolean;
  disabled?: boolean;
  onClick: () => void;
};

export function GoogleSignInButton({
  connecting = false,
  disabled = false,
  onClick,
}: GoogleSignInButtonProps) {
  return (
    <button
      className="inline-flex min-h-12 w-full items-center justify-center rounded-xl border border-[#dadce0] bg-white px-5 py-3 font-medium text-[#3c4043] shadow-[0_10px_30px_rgba(18,48,71,0.08)] hover:bg-[#f8f9fa] disabled:cursor-wait disabled:opacity-70"
      disabled={disabled || connecting}
      onClick={onClick}
      type="button"
    >
      {connecting ? (
        <span
          aria-hidden="true"
          className="mr-3 size-5 animate-spin rounded-full border-2 border-[#dadce0] border-t-[#4285f4]"
        />
      ) : (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          alt=""
          className="mr-3 size-5"
          height={20}
          src={googleLogoUrl}
          width={20}
        />
      )}
      {connecting ? "Đang kết nối..." : "Đăng nhập bằng Google"}
    </button>
  );
}
