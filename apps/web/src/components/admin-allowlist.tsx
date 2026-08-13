"use client";

import { FormEvent, useEffect, useState } from "react";

import { LoginRequiredPanel } from "@/components/login-required";

type AllowlistEntry = {
  id: string;
  email: string;
  added_by_user_id: string | null;
  created_at: string;
  revoked_at: string | null;
};

type AdminState =
  | { kind: "loading" }
  | { kind: "unauthenticated" }
  | { kind: "forbidden" }
  | { kind: "ready"; entries: AllowlistEntry[]; message: string | null }
  | { kind: "error"; message: string };

export function AdminAllowlist() {
  const [state, setState] = useState<AdminState>({ kind: "loading" });
  const [email, setEmail] = useState("");

  async function loadEntries(message: string | null = null) {
    try {
      const response = await fetch("/v1/admin/access/allowlist", {
        credentials: "same-origin",
      });
      if (response.status === 401) {
        setState({ kind: "unauthenticated" });
        return;
      }
      if (response.status === 403) {
        setState({ kind: "forbidden" });
        return;
      }
      if (!response.ok) {
        throw new Error("Không thể tải allowlist");
      }

      const data: { items: AllowlistEntry[] } = await response.json();
      setState({ kind: "ready", entries: data.items, message });
    } catch (error) {
      setState({
        kind: "error",
        message: error instanceof Error ? error.message : "Có lỗi xảy ra",
      });
    }
  }

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadEntries();
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, []);

  async function grant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const response = await fetch("/v1/admin/access/allowlist", {
      body: JSON.stringify({ email }),
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
    if (!response.ok) {
      setState({
        kind: "error",
        message: "Không thể cấp quyền admin cho email này.",
      });
      return;
    }

    setEmail("");
    await loadEntries("Đã cập nhật allowlist.");
  }

  async function revoke(entryId: string) {
    const response = await fetch(`/v1/admin/access/allowlist/${entryId}`, {
      credentials: "same-origin",
      method: "DELETE",
    });
    if (response.status === 409) {
      setState({
        kind: "error",
        message: "Không thể thu hồi admin cuối cùng.",
      });
      return;
    }
    if (!response.ok) {
      setState({ kind: "error", message: "Không thể thu hồi quyền admin." });
      return;
    }

    await loadEntries("Đã thu hồi quyền admin.");
  }

  if (state.kind === "loading") {
    return <p className="text-[#45667a]">Đang tải danh sách admin...</p>;
  }

  if (state.kind === "unauthenticated") {
    return (
      <LoginRequiredPanel
        body="Đăng nhập bằng tài khoản admin để quản lý allowlist."
        returnTo="/admin"
        title="Cần đăng nhập"
      />
    );
  }

  if (state.kind === "forbidden") {
    return (
      <div className="border border-[#fecaca] bg-[#fff1f2] p-6">
        <h2 className="text-2xl font-semibold">Không có quyền admin</h2>
        <p className="mt-2 text-[#7f1d1d]">
          Tài khoản hiện tại chưa nằm trong admin allowlist.
        </p>
      </div>
    );
  }

  if (state.kind === "error") {
    return (
      <div className="border border-[#fecaca] bg-[#fff1f2] p-6">
        <h2 className="text-2xl font-semibold">Có lỗi xảy ra</h2>
        <p className="mt-2 text-[#7f1d1d]">{state.message}</p>
        <button
          className="mt-5 rounded-md border border-[#991b1b] px-5 py-3 font-semibold"
          onClick={() => void loadEntries()}
          type="button"
        >
          Thử lại
        </button>
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      {state.message === null ? null : (
        <p className="border border-[#bae6fd] bg-[#e0f2fe] px-4 py-3 text-sm font-semibold text-[#0369a1]">
          {state.message}
        </p>
      )}

      <form
        className="grid gap-3 border border-[#bae6fd] bg-white p-5 sm:grid-cols-[1fr_auto]"
        onSubmit={(event) => void grant(event)}
      >
        <label className="grid gap-2">
          <span className="text-sm font-semibold text-[#45667a]">
            Email Google admin
          </span>
          <input
            className="min-h-12 border border-[#bae6fd] px-4 outline-none focus:border-[#0284c7]"
            onChange={(event) => setEmail(event.target.value)}
            placeholder="admin@example.com"
            required
            type="email"
            value={email}
          />
        </label>
        <button
          className="self-end rounded-md bg-[#123047] px-5 py-3 font-semibold text-white hover:bg-[#0284c7]"
          type="submit"
        >
          Cấp quyền
        </button>
      </form>

      <div className="divide-y divide-[#bae6fd] border border-[#bae6fd] bg-white">
        {state.entries.map((entry) => (
          <article
            className="grid gap-4 p-5 sm:grid-cols-[1fr_auto] sm:items-center"
            key={entry.id}
          >
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg font-semibold">{entry.email}</h2>
                <span className="rounded-full bg-[#e0f2fe] px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-[#0369a1]">
                  {entry.revoked_at === null ? "Active" : "Revoked"}
                </span>
              </div>
              <p className="mt-2 text-sm text-[#45667a]">
                Tạo lúc {new Date(entry.created_at).toLocaleString("vi-VN")}
              </p>
            </div>
            <button
              className="rounded-md border border-[#bae6fd] px-4 py-2 font-semibold disabled:cursor-not-allowed disabled:opacity-50"
              disabled={entry.revoked_at !== null}
              onClick={() => void revoke(entry.id)}
              type="button"
            >
              Thu hồi
            </button>
          </article>
        ))}
      </div>
    </div>
  );
}
