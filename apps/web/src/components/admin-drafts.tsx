"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type DraftSummary = {
  id: string;
  exam_slug: string;
  title: string;
  status: string;
  updated_at: string;
  part1_count: number;
  part2_count: number;
  import_warnings: number | null;
};

type DraftListState =
  | { kind: "loading" }
  | { kind: "forbidden" }
  | { kind: "ready"; drafts: DraftSummary[] }
  | { kind: "error"; message: string };

export function AdminDrafts() {
  const [state, setState] = useState<DraftListState>({ kind: "loading" });

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void (async () => {
        try {
          const response = await fetch("/v1/admin/publishing/drafts", {
            credentials: "same-origin",
          });
          if (response.status === 403) {
            setState({ kind: "forbidden" });
            return;
          }
          if (!response.ok) {
            throw new Error("Không thể tải danh sách bản nháp");
          }
          const data: { items: DraftSummary[] } = await response.json();
          setState({ kind: "ready", drafts: data.items });
        } catch (error) {
          setState({
            kind: "error",
            message: error instanceof Error ? error.message : "Có lỗi xảy ra",
          });
        }
      })();
    }, 0);
    return () => window.clearTimeout(timeoutId);
  }, []);

  if (state.kind === "loading") {
    return <p className="text-sm text-[#45667a]">Đang tải bản nháp...</p>;
  }
  if (state.kind === "forbidden") {
    return (
      <p className="text-sm text-[#45667a]">
        Chỉ admin mới xem được danh sách bản nháp.
      </p>
    );
  }
  if (state.kind === "error") {
    return (
      <p className="border border-[#fecaca] bg-[#fff1f2] px-4 py-3 text-sm font-semibold text-[#991b1b]">
        {state.message}
      </p>
    );
  }

  if (state.drafts.length === 0) {
    return (
      <p className="border border-[#bae6fd] bg-[#f8fcff] px-4 py-3 text-sm text-[#45667a]">
        Chưa có bản nháp. Hãy nhập đề từ tài liệu nguồn ở mục bên trên.
      </p>
    );
  }

  return (
    <ul className="grid gap-3">
      {state.drafts.map((draft) => (
        <li
          className="flex flex-wrap items-center justify-between gap-3 border border-[#dbeafe] px-4 py-3"
          key={draft.id}
        >
          <div>
            <p className="font-semibold text-[#123047]">{draft.title}</p>
            <p className="text-sm text-[#45667a]">
              {draft.part1_count} câu Phần I · {draft.part2_count} câu Phần II
              {draft.import_warnings
                ? ` · ${draft.import_warnings} cảnh báo import`
                : ""}
            </p>
          </div>
          <Link
            className="rounded-md border border-[#123047] px-4 py-2 text-sm font-semibold text-[#123047] hover:bg-[#123047] hover:text-white"
            href={`/admin/publishing/drafts/${draft.id}`}
          >
            Rà soát
          </Link>
        </li>
      ))}
    </ul>
  );
}
