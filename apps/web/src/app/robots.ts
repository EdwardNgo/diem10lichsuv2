import type { MetadataRoute } from "next";

import { absoluteRequestUrl } from "@/lib/site-url";

export const dynamic = "force-dynamic";

export default async function robots(): Promise<MetadataRoute.Robots> {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/admin/", "/login", "/attempts/", "/history"],
    },
    sitemap: await absoluteRequestUrl("/sitemap.xml"),
  };
}
