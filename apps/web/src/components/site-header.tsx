import { AuthStatus } from "@/components/auth-status";
import { SiteBrand } from "@/components/site-brand";

export function SiteHeader() {
  return (
    <header className="border-b border-[#bae6fd] bg-white/80">
      <nav
        aria-label="Điều hướng chính"
        className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4 sm:px-8"
      >
        <SiteBrand />
        <AuthStatus />
      </nav>
    </header>
  );
}
