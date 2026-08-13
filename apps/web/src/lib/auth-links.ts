const defaultReturnPath = "/exams";

export function safeReturnPath(
  value: string,
  fallback = defaultReturnPath,
): string {
  const candidate = value.trim();

  if (
    candidate.length === 0 ||
    !candidate.startsWith("/") ||
    candidate.startsWith("//") ||
    candidate.includes("\\")
  ) {
    return fallback;
  }

  try {
    const parsed = new URL(candidate, "https://diem10.local");
    if (parsed.origin !== "https://diem10.local") {
      return fallback;
    }

    return `${parsed.pathname}${parsed.search}${parsed.hash}`;
  } catch {
    return fallback;
  }
}

export function googleLoginHref(returnTo: string): string {
  return `/v1/auth/google?return_to=${encodeURIComponent(safeReturnPath(returnTo))}`;
}

export function loginHref(returnTo: string): string {
  return `/login?return_to=${encodeURIComponent(safeReturnPath(returnTo))}`;
}
