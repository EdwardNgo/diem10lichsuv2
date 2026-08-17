import type { MetadataRoute } from "next";

import { listPublicExamSlugs } from "@/lib/public-exams-server";
import { absoluteUrl } from "@/lib/site-url";

export const revalidate = 3600;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticRoutes: MetadataRoute.Sitemap = [
    {
      url: absoluteUrl("/"),
      changeFrequency: "weekly",
      priority: 1,
    },
    {
      url: absoluteUrl("/exams"),
      changeFrequency: "daily",
      priority: 0.9,
    },
    {
      url: absoluteUrl("/privacy"),
      changeFrequency: "yearly",
      priority: 0.3,
    },
    {
      url: absoluteUrl("/terms"),
      changeFrequency: "yearly",
      priority: 0.3,
    },
  ];

  const examSlugs = await listPublicExamSlugs();

  const examRoutes: MetadataRoute.Sitemap = examSlugs.map((slug) => ({
    url: absoluteUrl(`/exams/${slug}`),
    changeFrequency: "weekly",
    priority: 0.8,
  }));

  return [...staticRoutes, ...examRoutes];
}
