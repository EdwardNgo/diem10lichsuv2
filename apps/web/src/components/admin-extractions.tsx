"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

type SourceAsset = {
  id: string;
  object_key: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
};

type ImportFinding = {
  severity: string;
  field_path: string;
  message: string;
};

type ImportResult = {
  import_job_id: string;
  exam_version_id: string | null;
  status: string;
  error_code: string | null;
  findings: ImportFinding[];
  summary: {
    part1_count: number;
    part2_count: number;
    warnings: number;
    errors: number;
  };
};

type AdminExtractionState = "loading" | "ready" | "hidden";

function formatBytes(sizeBytes: number) {
  return `${(sizeBytes / (1024 * 1024)).toFixed(2)} MB`;
}

function assetFilename(objectKey: string) {
  return objectKey.split("/").pop() ?? objectKey;
}

export function AdminExtractions() {
  const [access, setAccess] = useState<AdminExtractionState>("loading");
  const [assets, setAssets] = useState<SourceAsset[]>([]);
  const [assetsLoading, setAssetsLoading] = useState(false);
  const [importingAssetId, setImportingAssetId] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  const loadAssets = useCallback(async () => {
    setAssetsLoading(true);
    try {
      const response = await fetch("/v1/admin/source-documents", {
        credentials: "same-origin",
      });
      if (!response.ok) {
        throw new Error("Không thể tải danh sách tài liệu nguồn.");
      }
      const data: { items: SourceAsset[] } = await response.json();
      setAssets(data.items);
    } catch (error) {
      setImportError(
        error instanceof Error ? error.message : "Không thể tải tài liệu nguồn.",
      );
    } finally {
      setAssetsLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function bootstrap() {
      try {
        const response = await fetch("/v1/admin/probe", {
          credentials: "same-origin",
          signal: controller.signal,
        });
        if (!response.ok) {
          setAccess("hidden");
          return;
        }
        setAccess("ready");
        await loadAssets();
      } catch {
        if (!controller.signal.aborted) {
          setAccess("hidden");
        }
      }
    }

    void bootstrap();
    return () => controller.abort();
  }, [loadAssets]);

  async function extractDraft(assetId: string) {
    setImportingAssetId(assetId);
    setImportError(null);
    setImportResult(null);
    try {
      const response = await fetch(`/v1/admin/extractions/${assetId}`, {
        body: JSON.stringify({}),
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        method: "POST",
      });
      if (!response.ok) {
        throw new Error("Không thể trích xuất bản nháp từ tài liệu nguồn.");
      }
      const result: ImportResult = await response.json();
      setImportResult(result);
      if (result.status === "failed") {
        setImportError(result.error_code ?? "Trích xuất thất bại.");
      }
    } catch (error) {
      setImportError(
        error instanceof Error ? error.message : "Trích xuất thất bại.",
      );
    } finally {
      setImportingAssetId(null);
    }
  }

  if (access !== "ready") {
    return null;
  }

  return (
    <div className="grid gap-5 border border-[#bae6fd] bg-white p-5">
      {assetsLoading ? (
        <p className="text-sm text-[#45667a]">Đang tải danh sách tài liệu...</p>
      ) : null}

      {!assetsLoading && assets.length === 0 ? (
        <div className="grid gap-3 border border-[#bae6fd] bg-[#f8fcff] px-4 py-3 text-sm text-[#45667a]">
          <p>Chưa có tài liệu nguồn nào.</p>
          <Link
            className="font-semibold text-[#0284c7] hover:underline"
            href="/admin/source-documents"
          >
            Tải tài liệu nguồn trước
          </Link>
        </div>
      ) : null}

      <ul className="grid gap-3">
        {assets.map((asset) => (
          <li
            className="flex flex-wrap items-center justify-between gap-3 border border-[#dbeafe] px-4 py-3"
            key={asset.id}
          >
            <div>
              <p className="font-semibold text-[#123047]">
                {assetFilename(asset.object_key)}
              </p>
              <p className="text-sm text-[#45667a]">
                {formatBytes(asset.size_bytes)} · {asset.mime_type}
              </p>
            </div>
            <button
              className="rounded-md border border-[#123047] px-4 py-2 text-sm font-semibold text-[#123047] hover:bg-[#123047] hover:text-white disabled:cursor-wait disabled:opacity-70"
              disabled={importingAssetId === asset.id}
              onClick={() => void extractDraft(asset.id)}
              type="button"
            >
              {importingAssetId === asset.id ? "Đang trích xuất..." : "Trích xuất"}
            </button>
          </li>
        ))}
      </ul>

      {importError ? (
        <p className="border border-[#fecaca] bg-[#fff1f2] px-4 py-3 text-sm font-semibold text-[#991b1b]">
          {importError}
        </p>
      ) : null}

      {importResult ? (
        <div className="grid gap-3 border border-[#bae6fd] bg-[#f8fcff] p-4">
          <p className="font-semibold text-[#123047]">
            Trích xuất{" "}
            {importResult.status === "succeeded" ? "thành công" : "thất bại"}
          </p>
          {importResult.exam_version_id ? (
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-sm text-[#45667a]">
                Draft ID:{" "}
                <span className="font-mono text-[#123047]">
                  {importResult.exam_version_id}
                </span>
              </p>
              <Link
                className="rounded-md border border-[#123047] px-4 py-2 text-sm font-semibold text-[#123047] hover:bg-[#123047] hover:text-white"
                href={`/admin/publishing/drafts/${importResult.exam_version_id}`}
              >
                Mở bản nháp
              </Link>
            </div>
          ) : null}
          <p className="text-sm text-[#45667a]">
            Phần I: {importResult.summary.part1_count} câu · Phần II:{" "}
            {importResult.summary.part2_count} câu ·{" "}
            {importResult.summary.warnings} cảnh báo ·{" "}
            {importResult.summary.errors} lỗi
          </p>
          {importResult.findings.length > 0 ? (
            <ul className="grid max-h-56 gap-2 overflow-y-auto text-sm text-[#45667a]">
              {importResult.findings.slice(0, 12).map((finding) => (
                <li key={`${finding.field_path}-${finding.message}`}>
                  <span className="font-semibold text-[#123047]">
                    [{finding.severity}]
                  </span>{" "}
                  {finding.field_path}: {finding.message}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
