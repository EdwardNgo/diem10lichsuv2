import { headers } from "next/headers";

const LOCAL_SITE_URL = "http://localhost:8080";
const PRODUCTION_SITE_URL = "https://suvanquan.com";

type SiteUrlContext = {
  host?: string | null;
  protocol?: string | null;
};

export function getSiteUrl(context?: SiteUrlContext): string {
  if (process.env.APP_BASE_URL) {
    return process.env.APP_BASE_URL.replace(/\/$/, "");
  }

  if (context?.host) {
    const protocol = context.protocol?.split(",")[0]?.trim() ?? "https";
    return `${protocol}://${context.host}`;
  }

  if (process.env.VERCEL_URL) {
    return `https://${process.env.VERCEL_URL}`;
  }

  if (process.env.NODE_ENV === "production") {
    return PRODUCTION_SITE_URL;
  }

  return LOCAL_SITE_URL;
}

export function absoluteUrl(path: string, context?: SiteUrlContext): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${getSiteUrl(context)}${normalizedPath}`;
}

export async function getRequestSiteUrl(): Promise<string> {
  const headerList = await headers();

  return getSiteUrl({
    host: headerList.get("host"),
    protocol: headerList.get("x-forwarded-proto"),
  });
}

export async function absoluteRequestUrl(path: string): Promise<string> {
  const baseUrl = await getRequestSiteUrl();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${baseUrl}${normalizedPath}`;
}
