"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

type DraftOption = {
  id: string;
  position: number;
  label: string;
  body: string;
  is_correct: boolean;
};

type DraftStatement = {
  id: string;
  position: number;
  label: string;
  body: string;
  is_correct: boolean;
};

type DraftQuestion = {
  id: string;
  position: number;
  part_number: number;
  part_position: number;
  question_type: "multiple_choice" | "true_false_group";
  body: string;
  source_text: string | null;
  explanation: string;
  options: DraftOption[];
  statements: DraftStatement[];
};

type ImportFinding = {
  id: string;
  severity: string;
  field_path: string;
  message: string;
  resolved_at: string | null;
};

type DraftDetail = {
  id: string;
  exam_id: string;
  exam_slug: string;
  title: string;
  summary: string;
  year: number | null;
  difficulty: string;
  duration_minutes: number;
  primary_topic_id: string | null;
  updated_at: string;
  questions: DraftQuestion[];
  import_context: {
    source_filename: string | null;
    source_download_url: string | null;
    findings: ImportFinding[];
  } | null;
};

type TopicOption = { id: string; slug: string; name: string };

type ValidationIssue = {
  severity: string;
  field_path: string;
  message: string;
  part_number?: number | null;
  part_position?: number | null;
};

type EditorState =
  | { kind: "loading" }
  | { kind: "forbidden" }
  | { kind: "error"; message: string }
  | {
      kind: "ready";
      draft: DraftDetail;
      topics: TopicOption[];
      activePart: 1 | 2;
      saveState: "idle" | "saving" | "saved" | "error";
      validation: {
        errors: ValidationIssue[];
        warnings: ValidationIssue[];
      } | null;
      acknowledgeWarnings: boolean;
      publishMessage: string | null;
    };

const difficulties = ["Dễ", "Trung bình", "Khó"];

function questionPayload(question: DraftQuestion) {
  return {
    id: question.id,
    position: question.position,
    part_number: question.part_number,
    part_position: question.part_position,
    question_type: question.question_type,
    body: question.body,
    source_text: question.source_text,
    explanation: question.explanation,
    options: question.options.map((option) => ({
      id: option.id,
      position: option.position,
      body: option.body,
      is_correct: option.is_correct,
    })),
    statements: question.statements.map((statement) => ({
      id: statement.id,
      position: statement.position,
      body: statement.body,
      is_correct: statement.is_correct,
    })),
  };
}

export function AdminDraftEditor() {
  const params = useParams<{ versionId: string }>();
  const router = useRouter();
  const versionId = params.versionId;
  const [state, setState] = useState<EditorState>({ kind: "loading" });

  const loadDraft = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      const [draftResponse, topicsResponse] = await Promise.all([
        fetch(`/v1/admin/publishing/drafts/${versionId}`, { credentials: "same-origin" }),
        fetch("/v1/admin/publishing/topics", { credentials: "same-origin" }),
      ]);
      if (draftResponse.status === 403) {
        setState({ kind: "forbidden" });
        return;
      }
      if (!draftResponse.ok) {
        throw new Error("Không thể tải bản nháp");
      }
      const draft: DraftDetail = await draftResponse.json();
      const topics = topicsResponse.ok
        ? ((await topicsResponse.json()) as { items: TopicOption[] }).items
        : [];
      setState({
        kind: "ready",
        draft,
        topics,
        activePart: 1,
        saveState: "idle",
        validation: null,
        acknowledgeWarnings: false,
        publishMessage: null,
      });
    } catch (error) {
      setState({
        kind: "error",
        message: error instanceof Error ? error.message : "Có lỗi xảy ra",
      });
    }
  }, [versionId]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadDraft();
    }, 0);
    return () => window.clearTimeout(timeoutId);
  }, [loadDraft]);

  const partQuestions = useMemo(() => {
    if (state.kind !== "ready") {
      return [];
    }
    return state.draft.questions
      .filter((question) => question.part_number === state.activePart)
      .sort((left, right) => left.part_position - right.part_position);
  }, [state]);

  async function saveDraft(nextDraft: DraftDetail) {
    if (state.kind !== "ready") {
      return;
    }
    setState({ ...state, saveState: "saving", draft: nextDraft });
    const metadataResponse = await fetch(`/v1/admin/publishing/drafts/${versionId}`, {
      method: "PATCH",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        expected_updated_at: state.draft.updated_at,
        title: nextDraft.title,
        summary: nextDraft.summary,
        year: nextDraft.year,
        difficulty: nextDraft.difficulty,
        duration_minutes: nextDraft.duration_minutes,
        primary_topic_id: nextDraft.primary_topic_id,
      }),
    });
    if (metadataResponse.status === 409) {
      setState({ ...state, saveState: "error", publishMessage: "Bản nháp đã thay đổi — hãy tải lại." });
      return;
    }
    const metadataDraft: DraftDetail = await metadataResponse.json();
    const questionsResponse = await fetch(
      `/v1/admin/publishing/drafts/${versionId}/questions`,
      {
        method: "PUT",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          expected_updated_at: metadataDraft.updated_at,
          questions: nextDraft.questions.map(questionPayload),
        }),
      },
    );
    if (!questionsResponse.ok) {
      setState({
        ...state,
        saveState: "error",
        publishMessage: "Không thể lưu câu hỏi.",
      });
      return;
    }
    const savedDraft: DraftDetail = await questionsResponse.json();
    setState({
      ...state,
      kind: "ready",
      draft: savedDraft,
      saveState: "saved",
      publishMessage: null,
    });
  }

  function updateDraft(updater: (draft: DraftDetail) => DraftDetail) {
    if (state.kind !== "ready") {
      return;
    }
    const nextDraft = updater(state.draft);
    setState({ ...state, draft: nextDraft, saveState: "idle" });
  }

  async function validateDraft() {
    if (state.kind !== "ready") {
      return;
    }
    const response = await fetch(`/v1/admin/publishing/drafts/${versionId}/validate`, {
      method: "POST",
      credentials: "same-origin",
    });
    if (!response.ok) {
      setState({ ...state, publishMessage: "Không thể kiểm tra bản nháp." });
      return;
    }
    const body = await response.json();
    setState({
      ...state,
      validation: { errors: body.errors, warnings: body.warnings },
      publishMessage: null,
    });
  }

  async function publishDraft() {
    if (state.kind !== "ready") {
      return;
    }
    await saveDraft(state.draft);
    const refreshed = await fetch(`/v1/admin/publishing/drafts/${versionId}`, {
      credentials: "same-origin",
    });
    if (!refreshed.ok) {
      setState({ ...state, publishMessage: "Không thể tải lại bản nháp trước khi xuất bản." });
      return;
    }
    const current: DraftDetail = await refreshed.json();
    const response = await fetch(`/v1/admin/publishing/drafts/${versionId}/publish`, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        expected_updated_at: current.updated_at,
        acknowledge_warnings: state.acknowledgeWarnings,
      }),
    });
    if (response.status === 422) {
      const body = await response.json();
      setState({
        ...state,
        validation: {
          errors: body.detail?.errors ?? [],
          warnings: body.detail?.warnings ?? [],
        },
        publishMessage: body.detail?.message ?? "Chưa đủ điều kiện xuất bản.",
      });
      return;
    }
    if (!response.ok) {
      setState({ ...state, publishMessage: "Xuất bản thất bại." });
      return;
    }
    const body = await response.json();
    router.push(`/exams/${body.exam_slug}`);
  }

  if (state.kind === "loading") {
    return <p className="text-sm text-[#45667a]">Đang tải editor...</p>;
  }
  if (state.kind === "forbidden") {
    return <p className="text-sm text-[#45667a]">Chỉ admin mới mở được editor.</p>;
  }
  if (state.kind === "error") {
    return (
      <p className="border border-[#fecaca] bg-[#fff1f2] px-4 py-3 text-sm font-semibold text-[#991b1b]">
        {state.message}
      </p>
    );
  }

  const { draft, topics, activePart, saveState, validation, publishMessage } =
    state;

  return (
    <div className="grid gap-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold tracking-[0.16em] text-[#0284c7]">
            BẢN NHÁP
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">
            {draft.title}
          </h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            className="rounded-md border border-[#123047] px-4 py-2 text-sm font-semibold text-[#123047]"
            onClick={() => void saveDraft(draft)}
            type="button"
          >
            {saveState === "saving" ? "Đang lưu..." : "Lưu"}
          </button>
          <button
            className="rounded-md border border-[#0284c7] px-4 py-2 text-sm font-semibold text-[#0284c7]"
            onClick={() => void validateDraft()}
            type="button"
          >
            Kiểm tra
          </button>
          <button
            className="rounded-md bg-[#123047] px-4 py-2 text-sm font-semibold text-white hover:bg-[#0284c7]"
            onClick={() => void publishDraft()}
            type="button"
          >
            Xuất bản
          </button>
        </div>
      </div>

      {publishMessage ? (
        <p className="border border-[#fecaca] bg-[#fff1f2] px-4 py-3 text-sm font-semibold text-[#991b1b]">
          {publishMessage}
        </p>
      ) : null}

      {validation ? (
        <section className="grid gap-3 border border-[#bae6fd] bg-[#f8fcff] p-4">
          <h2 className="text-lg font-semibold text-[#123047]">Kết quả kiểm tra</h2>
          {validation.errors.length === 0 && validation.warnings.length === 0 ? (
            <p className="text-sm text-[#0369a1]">Bản nháp sẵn sàng xuất bản.</p>
          ) : null}
          {validation.errors.map((issue) => (
            <p className="text-sm text-[#991b1b]" key={`${issue.field_path}-error`}>
              [Lỗi] {issue.field_path}: {issue.message}
            </p>
          ))}
          {validation.warnings.map((issue) => (
            <p className="text-sm text-[#92400e]" key={`${issue.field_path}-warning`}>
              [Cảnh báo] {issue.field_path}: {issue.message}
            </p>
          ))}
          {validation.warnings.length > 0 ? (
            <label className="flex items-center gap-2 text-sm text-[#45667a]">
              <input
                checked={state.acknowledgeWarnings}
                onChange={(event) =>
                  setState({ ...state, acknowledgeWarnings: event.target.checked })
                }
                type="checkbox"
              />
              Tôi đã rà soát các cảnh báo còn lại
            </label>
          ) : null}
        </section>
      ) : null}

      <section className="grid gap-4 border border-[#bae6fd] bg-white p-5">
        <h2 className="text-xl font-semibold text-[#123047]">Metadata</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="grid gap-1 text-sm">
            <span className="font-semibold text-[#123047]">Tiêu đề</span>
            <input
              className="border border-[#dbeafe] px-3 py-2"
              onChange={(event) =>
                updateDraft((current) => ({ ...current, title: event.target.value }))
              }
              value={draft.title}
            />
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-semibold text-[#123047]">Mức độ</span>
            <select
              className="border border-[#dbeafe] px-3 py-2"
              onChange={(event) =>
                updateDraft((current) => ({
                  ...current,
                  difficulty: event.target.value,
                }))
              }
              value={draft.difficulty}
            >
              <option value="Chưa phân loại">Chọn mức độ</option>
              {difficulties.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm md:col-span-2">
            <span className="font-semibold text-[#123047]">Mô tả</span>
            <textarea
              className="min-h-24 border border-[#dbeafe] px-3 py-2"
              onChange={(event) =>
                updateDraft((current) => ({
                  ...current,
                  summary: event.target.value,
                }))
              }
              value={draft.summary}
            />
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-semibold text-[#123047]">Năm</span>
            <input
              className="border border-[#dbeafe] px-3 py-2"
              onChange={(event) =>
                updateDraft((current) => ({
                  ...current,
                  year: event.target.value ? Number(event.target.value) : null,
                }))
              }
              type="number"
              value={draft.year ?? ""}
            />
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-semibold text-[#123047]">Thời lượng (phút)</span>
            <input
              className="border border-[#dbeafe] px-3 py-2"
              onChange={(event) =>
                updateDraft((current) => ({
                  ...current,
                  duration_minutes: Number(event.target.value),
                }))
              }
              type="number"
              value={draft.duration_minutes}
            />
          </label>
          <label className="grid gap-1 text-sm md:col-span-2">
            <span className="font-semibold text-[#123047]">Chủ đề chính</span>
            <select
              className="border border-[#dbeafe] px-3 py-2"
              onChange={(event) =>
                updateDraft((current) => ({
                  ...current,
                  primary_topic_id: event.target.value || null,
                }))
              }
              value={draft.primary_topic_id ?? ""}
            >
              <option value="">Chọn chủ đề</option>
              {topics.map((topic) => (
                <option key={topic.id} value={topic.id}>
                  {topic.name}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      {draft.import_context ? (
        <section className="grid gap-3 border border-[#bae6fd] bg-white p-5">
          <h2 className="text-xl font-semibold text-[#123047]">Rà soát import</h2>
          <p className="text-sm text-[#45667a]">
            Nguồn: {draft.import_context.source_filename ?? "Không rõ"}
            {draft.import_context.source_download_url ? (
              <>
                {" "}
                ·{" "}
                <a
                  className="font-semibold text-[#0284c7]"
                  href={draft.import_context.source_download_url}
                  rel="noreferrer"
                  target="_blank"
                >
                  Tải tệp nguồn
                </a>
              </>
            ) : null}
          </p>
          <ul className="grid max-h-56 gap-2 overflow-y-auto text-sm text-[#45667a]">
            {draft.import_context.findings
              .filter((finding) => finding.resolved_at === null)
              .slice(0, 20)
              .map((finding) => (
                <li key={finding.id}>
                  <span className="font-semibold text-[#123047]">
                    [{finding.severity}]
                  </span>{" "}
                  {finding.field_path}: {finding.message}
                </li>
              ))}
          </ul>
        </section>
      ) : null}

      <section className="grid gap-4 border border-[#bae6fd] bg-white p-5">
        <div className="flex flex-wrap gap-2">
          <button
            className={`rounded-md px-4 py-2 text-sm font-semibold ${
              activePart === 1
                ? "bg-[#123047] text-white"
                : "border border-[#123047] text-[#123047]"
            }`}
            onClick={() => setState({ ...state, activePart: 1 })}
            type="button"
          >
            Phần I
          </button>
          <button
            className={`rounded-md px-4 py-2 text-sm font-semibold ${
              activePart === 2
                ? "bg-[#123047] text-white"
                : "border border-[#123047] text-[#123047]"
            }`}
            onClick={() => setState({ ...state, activePart: 2 })}
            type="button"
          >
            Phần II
          </button>
        </div>

        <div className="grid gap-4">
          {partQuestions.map((question) => (
            <article
              className="grid gap-3 border border-[#dbeafe] p-4"
              key={question.id}
            >
              <h3 className="font-semibold text-[#123047]">
                Câu {question.part_position}
              </h3>
              {question.question_type === "true_false_group" ? (
                <textarea
                  className="min-h-24 border border-[#dbeafe] px-3 py-2 text-sm"
                  onChange={(event) =>
                    updateDraft((current) => ({
                      ...current,
                      questions: current.questions.map((item) =>
                        item.id === question.id
                          ? { ...item, source_text: event.target.value }
                          : item,
                      ),
                    }))
                  }
                  placeholder="Đoạn tư liệu"
                  value={question.source_text ?? ""}
                />
              ) : null}
              <textarea
                className="min-h-20 border border-[#dbeafe] px-3 py-2 text-sm"
                onChange={(event) =>
                  updateDraft((current) => ({
                    ...current,
                    questions: current.questions.map((item) =>
                      item.id === question.id
                        ? { ...item, body: event.target.value }
                        : item,
                    ),
                  }))
                }
                placeholder="Nội dung câu hỏi"
                value={question.body}
              />
              {question.question_type === "multiple_choice"
                ? question.options.map((option) => (
                    <label
                      className="flex items-start gap-2 text-sm text-[#45667a]"
                      key={option.id}
                    >
                      <input
                        checked={option.is_correct}
                        name={`correct-${question.id}`}
                        onChange={() =>
                          updateDraft((current) => ({
                            ...current,
                            questions: current.questions.map((item) =>
                              item.id === question.id
                                ? {
                                    ...item,
                                    options: item.options.map((entry) => ({
                                      ...entry,
                                      is_correct:
                                        entry.position === option.position,
                                    })),
                                  }
                                : item,
                            ),
                          }))
                        }
                        type="radio"
                      />
                      <span className="pt-1 font-semibold text-[#123047]">
                        {option.label}.
                      </span>
                      <input
                        className="flex-1 border border-[#dbeafe] px-2 py-1"
                        onChange={(event) =>
                          updateDraft((current) => ({
                            ...current,
                            questions: current.questions.map((item) =>
                              item.id === question.id
                                ? {
                                    ...item,
                                    options: item.options.map((entry) =>
                                      entry.id === option.id
                                        ? { ...entry, body: event.target.value }
                                        : entry,
                                    ),
                                  }
                                : item,
                            ),
                          }))
                        }
                        value={option.body}
                      />
                    </label>
                  ))
                : question.statements.map((statement) => (
                    <div
                      className="grid gap-2 md:grid-cols-[120px_1fr]"
                      key={statement.id}
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-[#123047]">
                          {statement.label})
                        </span>
                        <select
                          className="border border-[#dbeafe] px-2 py-1 text-sm"
                          onChange={(event) =>
                            updateDraft((current) => ({
                              ...current,
                              questions: current.questions.map((item) =>
                                item.id === question.id
                                  ? {
                                      ...item,
                                      statements: item.statements.map((entry) =>
                                        entry.id === statement.id
                                          ? {
                                              ...entry,
                                              is_correct:
                                                event.target.value === "true",
                                            }
                                          : entry,
                                      ),
                                    }
                                  : item,
                              ),
                            }))
                          }
                          value={String(statement.is_correct)}
                        >
                          <option value="true">Đúng</option>
                          <option value="false">Sai</option>
                        </select>
                      </div>
                      <input
                        className="border border-[#dbeafe] px-2 py-1 text-sm"
                        onChange={(event) =>
                          updateDraft((current) => ({
                            ...current,
                            questions: current.questions.map((item) =>
                              item.id === question.id
                                ? {
                                    ...item,
                                    statements: item.statements.map((entry) =>
                                      entry.id === statement.id
                                        ? { ...entry, body: event.target.value }
                                        : entry,
                                    ),
                                  }
                                : item,
                            ),
                          }))
                        }
                        value={statement.body}
                      />
                    </div>
                  ))}
              <textarea
                className="min-h-16 border border-[#dbeafe] px-3 py-2 text-sm"
                onChange={(event) =>
                  updateDraft((current) => ({
                    ...current,
                    questions: current.questions.map((item) =>
                      item.id === question.id
                        ? { ...item, explanation: event.target.value }
                        : item,
                    ),
                  }))
                }
                placeholder="Lời giải (tuỳ chọn)"
                value={question.explanation}
              />
            </article>
          ))}
        </div>
      </section>

      <p className="text-sm text-[#45667a]">
        <Link className="font-semibold text-[#0284c7]" href="/admin/publishing">
          ← Quay lại danh sách bản nháp
        </Link>
      </p>
    </div>
  );
}
