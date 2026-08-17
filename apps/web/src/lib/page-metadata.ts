import type { Metadata } from "next";

export function withCanonical(path: string, metadata: Metadata = {}): Metadata {
  return {
    ...metadata,
    alternates: {
      ...metadata.alternates,
      canonical: path,
    },
  };
}
