import type { MetadataRoute } from "next";

import { listPublicExamSlugs } from "@/lib/public-exams-server";
import { absoluteRequestUrl } from "@/lib/site-url";

export const dynamic = "force-dynamic";
export const revalidate = 3600;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticRoutes: MetadataRoute.Sitemap = [
    {
      url: await absoluteRequestUrl("/"),
      changeFrequency: "weekly",
      priority: 1,
    },
    {
      url: await absoluteRequestUrl("/exams"),
      changeFrequency: "daily",
      priority: 0.9,
    },
    {
      url: await absoluteRequestUrl("/privacy"),
      changeFrequency: "yearly",
      priority: 0.3,
    },
    {
      url: await absoluteRequestUrl("/terms"),
      changeFrequency: "yearly",
      priority: 0.3,
    },
  ];

  const examSlugs = await listPublicExamSlugs();

  const examRoutes: MetadataRoute.Sitemap = await Promise.all(
    examSlugs.map(async (slug) => ({
      url: await absoluteRequestUrl(`/exams/${slug}`),
      changeFrequency: "weekly" as const,
      priority: 0.8,
    })),
  );

  return [...staticRoutes, ...examRoutes];
}
