import Link from "next/link";

type SiteBrandProps = {
  href?: string;
};

export function SiteMark({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      fill="none"
      viewBox="0 0 100 100"
      xmlns="http://www.w3.org/2000/svg"
    >
      <g
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M 50 28 Q 24 34 22 72 Q 38 64 50 72" strokeWidth="3.5" />
        <path d="M 50 28 Q 76 34 78 72 Q 62 64 50 72" strokeWidth="3.5" />
        <line x1="50" y1="28" x2="50" y2="72" strokeWidth="3" />
      </g>
    </svg>
  );
}

export function SiteBrand({ href = "/" }: SiteBrandProps) {
  return (
    <Link className="inline-flex items-center gap-2.5 text-[#123047]" href={href}>
      <SiteMark className="size-8 shrink-0 text-[#0284c7]" />
      <span className="text-lg font-semibold tracking-tight">
        Sử Văn <span className="text-[#0284c7]">Quán</span>
      </span>
    </Link>
  );
}
