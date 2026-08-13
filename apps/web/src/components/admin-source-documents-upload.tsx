"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";

type UploadState =
  | { kind: "idle" }
  | { kind: "uploading"; message: string }
  | { kind: "success"; filename: string }
  | { kind: "error"; message: string };

type AdminUploadState = "loading" | "ready" | "hidden";

type UploadUrlResponse = {
  object_key: string;
  bucket: string;
  upload_url: string;
  method: "PUT";
  headers: Record<string, string>;
  expires_in_seconds: number;
};

const maxSourceDocumentBytes = 20 * 1024 * 1024;
const mimeByExtension: Record<string, string> = {
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  pdf: "application/pdf",
};

function sourceMimeType(file: File) {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  return file.type || mimeByExtension[extension] || "";
}

function validateSourceDocument(file: File) {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  if (mimeByExtension[extension] === undefined) {
    return "Chỉ hỗ trợ tài liệu DOCX hoặc PDF có lớp chữ.";
  }
  if (sourceMimeType(file) !== mimeByExtension[extension]) {
    return "MIME type không khớp phần mở rộng tệp.";
  }
  if (file.size <= 0 || file.size > maxSourceDocumentBytes) {
    return "Tệp nguồn phải lớn hơn 0 byte và không vượt quá 20 MB.";
  }
  return null;
}

async function checksumSha256(file: File) {
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

function formatBytes(sizeBytes: number) {
  return `${(sizeBytes / (1024 * 1024)).toFixed(2)} MB`;
}

export function AdminSourceDocumentsUpload() {
  const [access, setAccess] = useState<AdminUploadState>("loading");
  const [file, setFile] = useState<File | null>(null);
  const [state, setState] = useState<UploadState>({ kind: "idle" });

  const checkAdminAccess = useCallback(async (signal: AbortSignal) => {
    const response = await fetch("/v1/admin/probe", {
      credentials: "same-origin",
      signal,
    });
    if (!response.ok) {
      setAccess("hidden");
      return;
    }
    setAccess("ready");
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => {
      void checkAdminAccess(controller.signal);
    }, 0);
    return () => {
      window.clearTimeout(timeoutId);
      controller.abort();
    };
  }, [checkAdminAccess]);

  useEffect(() => {
    if (state.kind !== "success") {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setState({ kind: "idle" });
    }, 4000);

    return () => window.clearTimeout(timeoutId);
  }, [state]);

  async function uploadSourceDocument(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (file === null) {
      setState({ kind: "error", message: "Hãy chọn tài liệu nguồn." });
      return;
    }

    const validationError = validateSourceDocument(file);
    if (validationError !== null) {
      setState({ kind: "error", message: validationError });
      return;
    }

    const uploadedFilename = file.name;

    try {
      setState({ kind: "uploading", message: "Đang tính checksum..." });
      const checksum = await checksumSha256(file);
      const metadata = {
        filename: uploadedFilename,
        mime_type: sourceMimeType(file),
        size_bytes: file.size,
        checksum_sha256: checksum,
      };

      setState({ kind: "uploading", message: "Đang xin URL upload..." });
      const uploadUrlResponse = await fetch(
        "/v1/admin/source-documents/upload-url",
        {
          body: JSON.stringify(metadata),
          credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          method: "POST",
        },
      );
      if (uploadUrlResponse.status === 403) {
        setAccess("hidden");
        return;
      }
      if (!uploadUrlResponse.ok) {
        throw new Error("Không thể chuẩn bị upload tài liệu nguồn.");
      }
      const upload: UploadUrlResponse = await uploadUrlResponse.json();

      setState({ kind: "uploading", message: "Đang tải tệp lên storage..." });
      const storageResponse = await fetch(upload.upload_url, {
        body: file,
        headers: upload.headers,
        method: upload.method,
      });
      if (!storageResponse.ok) {
        throw new Error("Storage từ chối upload. Hãy yêu cầu URL mới.");
      }

      setState({ kind: "uploading", message: "Đang xác nhận metadata..." });
      const confirmResponse = await fetch("/v1/admin/source-documents", {
        body: JSON.stringify({
          ...metadata,
          bucket: upload.bucket,
          object_key: upload.object_key,
        }),
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        method: "POST",
      });
      if (confirmResponse.status === 409) {
        throw new Error("Tài liệu này đã được upload trước đó.");
      }
      if (!confirmResponse.ok) {
        throw new Error("Không thể xác nhận tài liệu nguồn.");
      }
      await confirmResponse.json();
      setFile(null);
      setState({ kind: "success", filename: uploadedFilename });
    } catch (error) {
      setState({
        kind: "error",
        message: error instanceof Error ? error.message : "Có lỗi xảy ra.",
      });
    }
  }

  if (access !== "ready") {
    return null;
  }

  return (
    <>
      {state.kind === "success" ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#123047]/40 px-5"
          role="alertdialog"
          aria-live="polite"
          aria-label="Upload thành công"
        >
          <div className="w-full max-w-md border border-[#bbf7d0] bg-white p-6 shadow-lg">
            <p className="text-sm font-semibold tracking-[0.16em] text-[#166534]">
              THÀNH CÔNG
            </p>
            <h3 className="mt-2 text-2xl font-semibold text-[#123047]">
              Đã lưu tài liệu nguồn
            </h3>
            <p className="mt-3 leading-7 text-[#45667a]">
              <span className="font-semibold text-[#123047]">{state.filename}</span>{" "}
              đã được upload thành công.
            </p>
            <div className="mt-6 grid gap-3">
              <Link
                className="block w-full rounded-md bg-[#123047] px-5 py-3 text-center font-semibold text-white hover:bg-[#0284c7]"
                href="/admin/extractions"
              >
                Trích xuất bản nháp
              </Link>
              <button
                className="w-full rounded-md border border-[#123047] px-5 py-3 font-semibold text-[#123047]"
                onClick={() => setState({ kind: "idle" })}
                type="button"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <div className="grid gap-5 border border-[#bae6fd] bg-white p-5">
        <form
          className="grid gap-4"
          onSubmit={(event) => void uploadSourceDocument(event)}
        >
          <label className="grid gap-2">
            <span className="text-sm font-semibold text-[#45667a]">
              Tài liệu DOCX/PDF
            </span>
            <input
              accept=".docx,.pdf,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="min-h-12 border border-[#bae6fd] bg-white px-4 py-3"
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null);
                setState({ kind: "idle" });
              }}
              type="file"
            />
          </label>

          {file === null ? null : (
            <dl className="grid gap-2 text-sm text-[#45667a] sm:grid-cols-3">
              <div>
                <dt className="font-semibold text-[#123047]">Tên tệp</dt>
                <dd>{file.name}</dd>
              </div>
              <div>
                <dt className="font-semibold text-[#123047]">Dung lượng</dt>
                <dd>{formatBytes(file.size)}</dd>
              </div>
              <div>
                <dt className="font-semibold text-[#123047]">MIME type</dt>
                <dd>{sourceMimeType(file) || "Không nhận diện"}</dd>
              </div>
            </dl>
          )}

          <div className="flex flex-wrap items-center gap-3">
            <button
              className="rounded-md bg-[#123047] px-5 py-3 font-semibold text-white hover:bg-[#0284c7] disabled:cursor-wait disabled:opacity-70"
              disabled={state.kind === "uploading"}
              type="submit"
            >
              {state.kind === "uploading" ? "Đang upload..." : "Upload tài liệu"}
            </button>
            <p className="text-sm text-[#45667a]">Giới hạn 20 MB mỗi tệp.</p>
          </div>
        </form>

        {state.kind === "uploading" ? (
          <p className="border border-[#bae6fd] bg-[#e0f2fe] px-4 py-3 text-sm font-semibold text-[#0369a1]">
            {state.message}
          </p>
        ) : null}
        {state.kind === "error" ? (
          <p className="border border-[#fecaca] bg-[#fff1f2] px-4 py-3 text-sm font-semibold text-[#991b1b]">
            {state.message}
          </p>
        ) : null}
      </div>
    </>
  );
}
