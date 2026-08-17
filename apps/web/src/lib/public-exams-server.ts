type PublicExamSummary = {
  slug: string;
};

type PublicExamPage = {
  items: PublicExamSummary[];
  page: number;
  page_size: number;
  total: number;
};

function getApiBaseUrl(): string {
  const raw =
    process.env.API_INTERNAL_URL ??
    process.env.APP_BASE_URL ??
    "http://localhost:8080";

  return raw.replace(/\/$/, "");
}

async function fetchPublicExamPage(page: number): Promise<PublicExamPage> {
  const response = await fetch(
    `${getApiBaseUrl()}/v1/public/exams?page=${page}&page_size=50`,
    { next: { revalidate: 3600 } },
  );

  if (!response.ok) {
    throw new Error(`Failed to load public exams (page ${page}): ${response.status}`);
  }

  return response.json() as Promise<PublicExamPage>;
}

export async function listPublicExamSlugs(): Promise<string[]> {
  try {
    const firstPage = await fetchPublicExamPage(1);
    const slugs = firstPage.items.map((exam) => exam.slug);
    const totalPages = Math.ceil(firstPage.total / firstPage.page_size);

    for (let page = 2; page <= totalPages; page += 1) {
      const nextPage = await fetchPublicExamPage(page);
      slugs.push(...nextPage.items.map((exam) => exam.slug));
    }

    return slugs;
  } catch {
    return [];
  }
}
