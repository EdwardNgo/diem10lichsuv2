"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { LoginRequiredPanel } from "@/components/login-required";

type AttemptQuestion = {
  id: string;
  position: number;
  part_number: number;
  part_position: number;
  question_type: "multiple_choice" | "true_false_group";
  body: string;
  source_text: string | null;
  options: { id: string; position: number; label: string; body: string }[];
  statements: { id: string; position: number; label: string; body: string }[];
};

type AttemptStatementAnswer = {
  statement_id: string;
  selected_value: boolean | null;
};

type AttemptAnswer = {
  question_id: string;
  selected_option_id: string | null;
  statement_answers: AttemptStatementAnswer[];
  is_marked_for_review: boolean;
  updated_at: string;
};

type AttemptDetail = {
  id: string;
  slug: string;
  title: string;
  summary: string;
  primary_topic: string;
  status: string;
  server_now: string;
  started_at: string;
  expires_at: string;
  duration_minutes: number;
  question_count: number;
  answered_count: number;
  questions: AttemptQuestion[];
  answers: AttemptAnswer[];
};

type AnswerDraft = {
  selected_option_id: string | null;
  statement_answers: Record<string, boolean | null>;
  is_marked_for_review: boolean;
};

type ResultQuestion = {
  id: string;
  position: number;
  part_number: number;
  part_position: number;
  question_type: "multiple_choice" | "true_false_group";
  body: string;
  source_text: string | null;
  explanation: string;
  selected_option_id: string | null;
  correct_option_id: string | null;
  options: { id: string; position: number; label: string; body: string }[];
  statements: {
    id: string;
    position: number;
    label: string;
    body: string;
    selected_value: boolean | null;
    correct_value: boolean;
    is_correct: boolean;
  }[];
  correct_count: number;
  total_count: number;
  earned_score: number;
  max_score: number;
};

type AttemptResult = {
  attempt_id: string;
  slug: string;
  title: string;
  attempt_number: number;
  status: string;
  score: number;
  part1_score: number;
  part2_score: number;
  correct_count: number;
  incorrect_count: number;
  unanswered_count: number;
  can_retry: boolean;
  questions: ResultQuestion[];
};

type TakerState =
  | { kind: "loading" }
  | { kind: "login_required" }
  | { kind: "not_found" }
  | { kind: "ready"; attempt: AttemptDetail }
  | { kind: "result"; result: AttemptResult }
  | { kind: "error"; message: string };

type SaveState = "idle" | "saving" | "saved" | "error" | "expired";
type SubmitState = "idle" | "submitting" | "error";
type LeaveState = "idle" | "pausing" | "error";
type RetryState = "idle" | "starting" | "error";

function answerMap(answers: AttemptAnswer[]): Record<string, AnswerDraft> {
  return Object.fromEntries(
    answers.map((answer) => [
      answer.question_id,
      {
        selected_option_id: answer.selected_option_id,
        statement_answers: Object.fromEntries(
          answer.statement_answers.map((statementAnswer) => [
            statementAnswer.statement_id,
            statementAnswer.selected_value,
          ]),
        ),
        is_marked_for_review: answer.is_marked_for_review,
      },
    ]),
  );
}

function formatRemaining(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60)
    .toString()
    .padStart(2, "0");
  const seconds = (totalSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function formatScore(score: number) {
  return Number(score.toFixed(2)).toString();
}

export function AttemptTaker() {
  const params = useParams<{ attemptId: string }>();
  const router = useRouter();
  const attemptId = params.attemptId;
  const [state, setState] = useState<TakerState>({ kind: "loading" });
  const [answers, setAnswers] = useState<Record<string, AnswerDraft>>({});
  const [currentIndex, setCurrentIndex] = useState(0);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [submitState, setSubmitState] = useState<SubmitState>("idle");
  const [isSubmitPopupOpen, setIsSubmitPopupOpen] = useState(false);
  const [isProgressOpen, setIsProgressOpen] = useState(false);
  const [pendingLeaveHref, setPendingLeaveHref] = useState<string | null>(null);
  const [leaveState, setLeaveState] = useState<LeaveState>("idle");
  const [isRetryPopupOpen, setIsRetryPopupOpen] = useState(false);
  const [retryState, setRetryState] = useState<RetryState>("idle");
  const [resultMode, setResultMode] = useState<"single" | "all">("single");
  const [resultIndex, setResultIndex] = useState(0);
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const allowNavigationRef = useRef(false);

  const loadResult = useCallback(async () => {
    try {
      const response = await fetch(`/v1/student/attempts/${attemptId}/result`, {
        credentials: "same-origin",
      });
      if (response.status === 401) {
        setState({ kind: "login_required" });
        return;
      }
      if (response.status === 404) {
        setState({ kind: "not_found" });
        return;
      }
      if (response.status === 409) {
        return;
      }
      if (!response.ok) {
        throw new Error("Không thể tải kết quả.");
      }
      const result: AttemptResult = await response.json();
      setResultIndex(0);
      setState({ kind: "result", result });
    } catch (error) {
      setState({
        kind: "error",
        message: error instanceof Error ? error.message : "Có lỗi xảy ra.",
      });
    }
  }, [attemptId]);

  const loadAttempt = useCallback(async () => {
    try {
      setState({ kind: "loading" });
      const response = await fetch(`/v1/student/attempts/${attemptId}/resume`, {
        credentials: "same-origin",
        method: "POST",
      });
      if (response.status === 401) {
        setState({ kind: "login_required" });
        return;
      }
      if (response.status === 404) {
        setState({ kind: "not_found" });
        return;
      }
      if (!response.ok) {
        throw new Error("Không thể tải lượt làm.");
      }

      const attempt: AttemptDetail = await response.json();
      if (attempt.status !== "in_progress") {
        await loadResult();
        return;
      }
      setState({ kind: "ready", attempt });
      setAnswers(answerMap(attempt.answers));
      setRemainingSeconds(
        Math.max(
          0,
          Math.floor(
            (new Date(attempt.expires_at).getTime() -
              new Date(attempt.server_now).getTime()) /
              1000,
          ),
        ),
      );
    } catch (error) {
      setState({
        kind: "error",
        message: error instanceof Error ? error.message : "Có lỗi xảy ra.",
      });
    }
  }, [attemptId, loadResult]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadAttempt();
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, [loadAttempt]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setRemainingSeconds((current) => Math.max(0, current - 1));
    }, 1000);

    return () => window.clearInterval(intervalId);
  }, []);

  useEffect(() => {
    if (state.kind !== "ready") {
      return;
    }

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (allowNavigationRef.current) {
        return;
      }
      event.preventDefault();
      event.returnValue = "";
    };
    const handlePageHide = () => {
      if (allowNavigationRef.current) {
        return;
      }
      void fetch(`/v1/student/attempts/${state.attempt.id}/pause`, {
        credentials: "same-origin",
        keepalive: true,
        method: "POST",
      });
    };
    const handleDocumentClick = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0) {
        return;
      }
      const target = event.target;
      if (!(target instanceof Element)) {
        return;
      }
      const link = target.closest<HTMLAnchorElement>("a[href]");
      if (
        link === null ||
        link.target === "_blank" ||
        link.hasAttribute("download")
      ) {
        return;
      }
      const destination = new URL(link.href, window.location.href);
      if (destination.href === window.location.href) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      setLeaveState("idle");
      setPendingLeaveHref(destination.href);
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    window.addEventListener("pagehide", handlePageHide);
    document.addEventListener("click", handleDocumentClick, true);
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
      window.removeEventListener("pagehide", handlePageHide);
      document.removeEventListener("click", handleDocumentClick, true);
    };
  }, [state]);

  useEffect(() => {
    const handlePageShow = (event: PageTransitionEvent) => {
      if (event.persisted) {
        void loadAttempt();
      }
    };
    window.addEventListener("pageshow", handlePageShow);
    return () => window.removeEventListener("pageshow", handlePageShow);
  }, [loadAttempt]);

  const currentQuestion =
    state.kind === "ready" ? state.attempt.questions[currentIndex] : null;
  const answeredCount = useMemo(
    () =>
      state.kind === "ready"
        ? state.attempt.questions.filter((question) =>
            isQuestionAnswered(question, answers[question.id]),
          ).length
        : 0,
    [answers, state],
  );
  const isExpired = remainingSeconds <= 0;

  function isQuestionAnswered(question: AttemptQuestion, answer?: AnswerDraft) {
    if (answer === undefined) {
      return false;
    }
    if (question.question_type === "multiple_choice") {
      return answer.selected_option_id !== null;
    }
    return question.statements.every(
      (statement) =>
        answer.statement_answers[statement.id] !== undefined &&
        answer.statement_answers[statement.id] !== null,
    );
  }

  async function saveAnswer(questionId: string, nextAnswer: AnswerDraft) {
    if (state.kind !== "ready") {
      return;
    }

    setAnswers((current) => ({ ...current, [questionId]: nextAnswer }));
    setSaveState("saving");
    try {
      const statementAnswers = Object.entries(nextAnswer.statement_answers).map(
        ([statementId, selectedValue]) => ({
          statement_id: statementId,
          selected_value: selectedValue,
        }),
      );
      const response = await fetch(
        `/v1/student/attempts/${state.attempt.id}/answers/${questionId}`,
        {
          body: JSON.stringify({
            selected_option_id: nextAnswer.selected_option_id,
            statement_answers:
              statementAnswers.length > 0 ? statementAnswers : null,
            is_marked_for_review: nextAnswer.is_marked_for_review,
          }),
          credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          method: "PUT",
        },
      );
      if (response.status === 409) {
        setSaveState("expired");
        setRemainingSeconds(0);
        return;
      }
      if (!response.ok) {
        throw new Error("Không thể lưu đáp án.");
      }

      const saved: AttemptAnswer = await response.json();
      setAnswers((current) => ({
        ...current,
        [questionId]: {
          selected_option_id: saved.selected_option_id,
          statement_answers: Object.fromEntries(
            saved.statement_answers.map((statementAnswer) => [
              statementAnswer.statement_id,
              statementAnswer.selected_value,
            ]),
          ),
          is_marked_for_review: saved.is_marked_for_review,
        },
      }));
      setSaveState("saved");
    } catch {
      setSaveState("error");
    }
  }

  async function submitAttempt() {
    if (state.kind !== "ready") {
      return;
    }
    try {
      setIsSubmitPopupOpen(false);
      setSubmitState("submitting");
      const response = await fetch(
        `/v1/student/attempts/${state.attempt.id}/submit`,
        {
          credentials: "same-origin",
          method: "POST",
        },
      );
      if (!response.ok) {
        throw new Error("Không thể nộp bài.");
      }
      const result: AttemptResult = await response.json();
      setResultIndex(0);
      setState({ kind: "result", result });
    } catch {
      setSubmitState("error");
    }
  }

  async function pauseAndLeave() {
    if (
      state.kind !== "ready" ||
      pendingLeaveHref === null ||
      saveState === "saving"
    ) {
      return;
    }
    setLeaveState("pausing");
    try {
      const response = await fetch(
        `/v1/student/attempts/${state.attempt.id}/pause`,
        {
          credentials: "same-origin",
          method: "POST",
        },
      );
      if (!response.ok && response.status !== 409) {
        throw new Error("Không thể tạm dừng lượt làm.");
      }
      allowNavigationRef.current = true;
      window.location.assign(pendingLeaveHref);
    } catch {
      setLeaveState("error");
    }
  }

  async function retryAttempt(result: AttemptResult) {
    setRetryState("starting");
    try {
      const response = await fetch(
        `/v1/student/exams/${result.slug}/attempts?restart=true`,
        {
          credentials: "same-origin",
          method: "POST",
        },
      );
      if (!response.ok) {
        throw new Error("Không thể tạo lượt làm mới.");
      }
      const attempt: { id: string } = await response.json();
      router.push(`/attempts/${attempt.id}`);
    } catch {
      setRetryState("error");
    }
  }

  if (state.kind === "loading") {
    return (
      <div className="border border-[#bae6fd] bg-white p-8 text-[#45667a]">
        Đang tải lượt làm...
      </div>
    );
  }

  if (state.kind === "login_required") {
    return (
      <LoginRequiredPanel
        body="Đăng nhập để tiếp tục lượt làm của bạn."
        returnTo={`/attempts/${attemptId}`}
        title="Cần đăng nhập"
      />
    );
  }

  if (state.kind === "not_found") {
    return (
      <div className="border border-[#fecaca] bg-[#fff1f2] p-8">
        <h1 className="text-3xl font-semibold">Không tìm thấy lượt làm</h1>
        <p className="mt-3 text-[#7f1d1d]">
          Lượt làm không tồn tại hoặc không thuộc tài khoản hiện tại.
        </p>
        <Link className="mt-6 inline-flex font-semibold text-[#0284c7]" href="/exams">
          Quay lại kho đề
        </Link>
      </div>
    );
  }

  if (state.kind === "error") {
    return (
      <div className="border border-[#fecaca] bg-[#fff1f2] p-8">
        <p className="font-semibold text-[#7f1d1d]">{state.message}</p>
        <button
          className="mt-5 rounded-md border border-[#991b1b] px-5 py-3 font-semibold"
          onClick={() => void loadAttempt()}
          type="button"
        >
          Thử lại
        </button>
      </div>
    );
  }

  if (state.kind === "result") {
    const partOneStats = partStats(state.result, 1);
    const partTwoStats = partStats(state.result, 2);
    const visibleQuestions =
      resultMode === "all"
        ? state.result.questions
        : [state.result.questions[resultIndex]].filter(
            (question): question is ResultQuestion => question !== undefined,
          );

    return (
      <article className="grid gap-6">
        <section className="border border-[#bae6fd] bg-white p-6">
          <div className="grid gap-6 lg:grid-cols-[18rem_1fr] lg:items-center">
            <ScoreRing score={state.result.score} />
            <div>
              <p className="text-sm font-semibold tracking-[0.14em] text-[#0284c7]">
                KẾT QUẢ BÀI LÀM
              </p>
              <h1 className="mt-3 text-3xl font-semibold">
                Tổng điểm {formatScore(state.result.score)}/10
              </h1>
              <p className="mt-2 text-sm font-semibold text-[#45667a]">
                {state.result.title}, lần {state.result.attempt_number}
              </p>
              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <ResultDashboardCard
                  correctCount={partOneStats.correct}
                  incorrectCount={partOneStats.incorrect}
                  maxScore={6}
                  score={state.result.part1_score}
                  title="Phần I"
                  unansweredCount={partOneStats.unanswered}
                />
                <ResultDashboardCard
                  correctCount={partTwoStats.correct}
                  incorrectCount={partTwoStats.incorrect}
                  maxScore={4}
                  score={state.result.part2_score}
                  title="Phần II"
                  unansweredCount={partTwoStats.unanswered}
                />
              </div>
              <div className="mt-4 grid gap-3 text-sm md:grid-cols-3">
                <div className="rounded-md bg-[#f0fdf4] px-4 py-3 font-semibold text-[#166534]">
                  Đúng {state.result.correct_count} câu
                </div>
                <div className="rounded-md bg-[#fff1f2] px-4 py-3 font-semibold text-[#991b1b]">
                  Sai {state.result.incorrect_count} câu
                </div>
                <div className="rounded-md bg-[#fef9c3] px-4 py-3 font-semibold text-[#854d0e]">
                  Bỏ trống {state.result.unanswered_count} câu
                </div>
              </div>
              <div className="mt-5 flex flex-wrap gap-3">
                <Link
                  className="rounded-md border border-[#bae6fd] px-4 py-2 font-semibold text-[#45667a] hover:border-[#0284c7] hover:text-[#0284c7]"
                  href="/history"
                >
                  Xem lịch sử
                </Link>
                {state.result.can_retry ? (
                  <button
                    className="rounded-md bg-[#0284c7] px-4 py-2 font-semibold text-white"
                    onClick={() => {
                      setRetryState("idle");
                      setIsRetryPopupOpen(true);
                    }}
                    type="button"
                  >
                    Làm lại
                  </button>
                ) : (
                  <p className="py-2 text-sm font-semibold text-[#854d0e]">
                    Đề hiện không còn khả dụng để làm lại.
                  </p>
                )}
              </div>
            </div>
          </div>
        </section>

        <section className="border border-[#bae6fd] bg-white p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex rounded-md border border-[#bae6fd] p-1">
              {(["single", "all"] as const).map((mode) => (
                <button
                  className={`rounded px-4 py-2 text-sm font-semibold transition active:scale-[0.98] ${
                    resultMode === mode
                      ? "bg-[#0284c7] text-white"
                      : "text-[#45667a] hover:bg-[#e0f2fe]"
                  }`}
                  key={mode}
                  onClick={() => setResultMode(mode)}
                  type="button"
                >
                  {mode === "single" ? "Từng câu" : "Tất cả"}
                </button>
              ))}
            </div>
            {resultMode === "single" ? (
              <div className="flex items-center gap-3">
                <button
                  className="rounded-md border border-[#bae6fd] px-4 py-2 font-semibold transition active:scale-[0.98] disabled:opacity-50"
                  disabled={resultIndex === 0}
                  onClick={() => setResultIndex((current) => current - 1)}
                  type="button"
                >
                  Câu trước
                </button>
                <span className="text-sm font-semibold text-[#45667a]">
                  {resultIndex + 1}/{state.result.questions.length}
                </span>
                <button
                  className="rounded-md bg-[#123047] px-4 py-2 font-semibold text-white transition active:scale-[0.98] disabled:opacity-50"
                  disabled={resultIndex >= state.result.questions.length - 1}
                  onClick={() => setResultIndex((current) => current + 1)}
                  type="button"
                >
                  Câu sau
                </button>
              </div>
            ) : null}
          </div>
        </section>

        <section className="grid gap-4">
          {visibleQuestions.map((question) => (
            <ResultQuestionCard question={question} key={question.id} />
          ))}
        </section>
        {isRetryPopupOpen ? (
          <RetryConfirmPopup
            isStarting={retryState === "starting"}
            onCancel={() => setIsRetryPopupOpen(false)}
            onConfirm={() => void retryAttempt(state.result)}
            retryFailed={retryState === "error"}
          />
        ) : null}
      </article>
    );
  }

  if (currentQuestion === null) {
    return (
      <div className="border border-[#bae6fd] bg-white p-8">
        Đề chưa có câu hỏi để làm.
      </div>
    );
  }

  const currentAnswer = answers[currentQuestion.id] ?? {
    selected_option_id: null,
    statement_answers: {},
    is_marked_for_review: false,
  };

  return (
    <div className="grid gap-6">
      <section className="border border-[#bae6fd] bg-white p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold tracking-[0.14em] text-[#0284c7]">
              {state.attempt.primary_topic}
            </p>
            <h1 className="mt-2 text-3xl font-semibold">{state.attempt.title}</h1>
          </div>
          <div className="relative flex items-center gap-2">
            <button
              aria-expanded={isProgressOpen}
              aria-haspopup="dialog"
              className="rounded-md border border-[#bae6fd] bg-white px-4 py-3 font-semibold text-[#0369a1]"
              onClick={() => setIsProgressOpen((current) => !current)}
              type="button"
            >
              Tiến độ {answeredCount}/{state.attempt.question_count}
            </button>
            <div className="rounded-md bg-[#e0f2fe] px-4 py-3 text-2xl font-semibold text-[#0369a1]">
              {formatRemaining(remainingSeconds)}
            </div>
            <button
              className="rounded-md bg-[#0284c7] px-4 py-3 font-semibold text-white disabled:opacity-50"
              disabled={submitState === "submitting"}
              onClick={() => setIsSubmitPopupOpen(true)}
              type="button"
            >
              {submitState === "submitting" ? "Đang nộp..." : "Nộp bài"}
            </button>
            {isProgressOpen ? (
              <div
                aria-label="Tiến độ làm bài"
                className="absolute right-0 top-[calc(100%+0.5rem)] z-20 w-72 border border-[#bae6fd] bg-white p-4 shadow-xl"
                role="dialog"
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold text-[#123047]">Tiến độ làm bài</p>
                  <button
                    className="text-sm font-semibold text-[#45667a]"
                    onClick={() => setIsProgressOpen(false)}
                    type="button"
                  >
                    Đóng
                  </button>
                </div>
                <p className="mt-1 text-sm text-[#45667a]">
                  {answeredCount}/{state.attempt.question_count} câu đã trả lời
                </p>
                <div className="mt-4 grid grid-cols-5 gap-2">
                  {state.attempt.questions.map((question, index) => {
                    const answer = answers[question.id];
                    const isAnswered = isQuestionAnswered(question, answer);
                    return (
                      <button
                        className={`min-h-10 border text-sm font-semibold ${
                          index === currentIndex
                            ? "border-[#0284c7] bg-[#0284c7] text-white"
                            : answer?.is_marked_for_review
                              ? "border-[#facc15] bg-[#fef9c3] text-[#854d0e]"
                              : isAnswered
                                ? "border-[#bae6fd] bg-[#e0f2fe] text-[#0369a1]"
                                : "border-[#bae6fd] bg-white text-[#45667a]"
                        }`}
                        key={question.id}
                        onClick={() => {
                          setCurrentIndex(index);
                          setIsProgressOpen(false);
                        }}
                        type="button"
                      >
                        {question.position}
                      </button>
                    );
                  })}
                </div>
              </div>
            ) : null}
          </div>
        </div>

        {isExpired ? (
          <div className="mt-5 border border-[#fecaca] bg-[#fff1f2] p-4 text-[#7f1d1d]">
            Lượt làm đã hết giờ. Hãy nộp để hệ thống khóa bài và trả kết quả.
          </div>
        ) : null}

        <div className="mt-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-xl font-semibold">
              Phần {currentQuestion.part_number} - Câu {currentQuestion.position}.{" "}
              {currentQuestion.body}
            </h2>
            <button
              aria-label={
                currentAnswer.is_marked_for_review
                  ? "Bỏ đánh dấu xem lại"
                  : "Đánh dấu xem lại"
              }
              className={`rounded-full border p-2 disabled:opacity-50 ${
                currentAnswer.is_marked_for_review
                  ? "border-[#facc15] bg-[#fef9c3] text-[#854d0e]"
                  : "border-[#bae6fd] bg-white text-[#45667a]"
              }`}
              disabled={isExpired}
              onClick={() =>
                void saveAnswer(currentQuestion.id, {
                  ...currentAnswer,
                  is_marked_for_review: !currentAnswer.is_marked_for_review,
                })
              }
              title={
                currentAnswer.is_marked_for_review
                  ? "Bỏ đánh dấu xem lại"
                  : "Đánh dấu xem lại"
              }
              type="button"
            >
              <svg
                aria-hidden="true"
                className="h-5 w-5"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path d="M5 5v14" />
                <path d="M5 5h11l-2 4 2 4H5" />
              </svg>
            </button>
          </div>

          {currentQuestion.question_type === "multiple_choice" ? (
            <div className="mt-5 grid gap-3">
              {currentQuestion.options.map((option) => (
                <button
                  className={`border px-4 py-3 text-left transition-colors disabled:cursor-not-allowed ${
                    currentAnswer.selected_option_id === option.id
                      ? "border-[#0284c7] bg-[#e0f2fe] text-[#123047]"
                      : "border-[#bae6fd] bg-white text-[#45667a] hover:border-[#0284c7]"
                  }`}
                  disabled={isExpired}
                  key={option.id}
                  onClick={() =>
                    void saveAnswer(currentQuestion.id, {
                      ...currentAnswer,
                      selected_option_id:
                        currentAnswer.selected_option_id === option.id
                          ? null
                          : option.id,
                      statement_answers: {},
                    })
                  }
                  type="button"
                >
                  {option.label}. {option.body}
                </button>
              ))}
            </div>
          ) : (
            <div className="mt-5 grid gap-4">
              <div className="border border-[#bae6fd] bg-[#f0f9ff] p-4 leading-7 text-[#123047]">
                {currentQuestion.source_text}
              </div>
              {currentQuestion.statements.map((statement) => {
                const selected = currentAnswer.statement_answers[statement.id];
                return (
                  <div
                    className="grid gap-3 border border-[#bae6fd] p-4 sm:grid-cols-[1fr_auto]"
                    key={statement.id}
                  >
                    <p className="leading-7 text-[#45667a]">
                      {statement.label}) {statement.body}
                    </p>
                    <div className="flex gap-2">
                      {[true, false].map((value) => (
                        <button
                          className={`min-w-20 rounded-md border px-4 py-2 font-semibold ${
                            selected === value
                              ? "border-[#0284c7] bg-[#e0f2fe] text-[#123047]"
                              : "border-[#bae6fd] bg-white text-[#45667a]"
                          }`}
                          disabled={isExpired}
                          key={String(value)}
                          onClick={() =>
                            void saveAnswer(currentQuestion.id, {
                              ...currentAnswer,
                              selected_option_id: null,
                              statement_answers: {
                                ...currentAnswer.statement_answers,
                                [statement.id]: value,
                              },
                            })
                          }
                          type="button"
                        >
                          {value ? "Đúng" : "Sai"}
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-[#bae6fd] pt-5">
          <div>
            {saveState === "error" ? (
              <p className="text-sm font-semibold text-[#991b1b]">
                Chưa lưu được thay đổi. Hãy thử lại.
              </p>
            ) : null}
            {saveState === "expired" ? (
              <p className="text-sm font-semibold text-[#991b1b]">Đã hết giờ.</p>
            ) : null}
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              className="rounded-md border border-[#bae6fd] px-4 py-2 font-semibold disabled:opacity-50"
              disabled={currentIndex === 0}
              onClick={() => setCurrentIndex((current) => current - 1)}
              type="button"
            >
              Câu trước
            </button>
            <button
              className="rounded-md bg-[#123047] px-4 py-2 font-semibold text-white disabled:opacity-50"
              disabled={currentIndex >= state.attempt.questions.length - 1}
              onClick={() => setCurrentIndex((current) => current + 1)}
              type="button"
            >
              Câu sau
            </button>
          </div>
        </div>
        {submitState === "error" ? (
          <p className="mt-3 text-sm font-semibold text-[#991b1b]">
            Chưa nộp được bài. Hãy thử lại.
          </p>
        ) : null}
      </section>

      {isSubmitPopupOpen ? (
        <SubmitConfirmPopup
          isSubmitting={submitState === "submitting"}
          onCancel={() => setIsSubmitPopupOpen(false)}
          onConfirm={() => void submitAttempt()}
          unansweredCount={state.attempt.question_count - answeredCount}
        />
      ) : null}
      {pendingLeaveHref !== null ? (
        <LeaveConfirmPopup
          isPausing={leaveState === "pausing"}
          isSaving={saveState === "saving"}
          onCancel={() => {
            setLeaveState("idle");
            setPendingLeaveHref(null);
          }}
          onConfirm={() => void pauseAndLeave()}
          pauseFailed={leaveState === "error"}
        />
      ) : null}
    </div>
  );
}

function ResultQuestionCard({ question }: { question: ResultQuestion }) {
  return (
    <section className="border border-[#bae6fd] bg-white p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-semibold">
          Phần {question.part_number} - Câu {question.position}. {question.body}
        </h2>
        <span className="rounded-md bg-[#e0f2fe] px-3 py-1 text-sm font-semibold text-[#0369a1]">
          {formatScore(question.earned_score)}/{formatScore(question.max_score)}
        </span>
      </div>
      {question.source_text === null ? null : (
        <div className="mt-4 border border-[#bae6fd] bg-[#f0f9ff] p-4 leading-7 text-[#123047]">
          {question.source_text}
        </div>
      )}
      {question.question_type === "multiple_choice" ? (
        <div className="mt-4 grid gap-2">
          {question.options.map((option) => {
            const isSelected = option.id === question.selected_option_id;
            const isCorrect = option.id === question.correct_option_id;
            return (
              <div
                className={`border px-4 py-3 text-sm ${
                  isCorrect
                    ? "border-[#bbf7d0] bg-[#f0fdf4] text-[#166534]"
                    : isSelected
                      ? "border-[#fecaca] bg-[#fff1f2] text-[#7f1d1d]"
                      : "border-[#bae6fd] bg-white text-[#45667a]"
                }`}
                key={option.id}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span>
                    {option.label}. {option.body}
                  </span>
                  {isCorrect ? (
                    <ResultMark isCorrect />
                  ) : isSelected ? (
                    <ResultMark isCorrect={false} />
                  ) : null}
                </div>
              </div>
            );
          })}
          {question.selected_option_id === null ? (
            <p className="text-sm font-semibold text-[#991b1b]">
              Bạn chưa chọn đáp án cho câu này.
            </p>
          ) : null}
        </div>
      ) : (
        <div className="mt-4 grid gap-2">
          {question.statements.map((statement) => (
            <TrueFalseResultStatement statement={statement} key={statement.id} />
          ))}
        </div>
      )}
      <p className="mt-4 leading-7 text-[#45667a]">{question.explanation}</p>
    </section>
  );
}

function ScoreRing({ score }: { score: number }) {
  const percentage = Math.max(0, Math.min(100, score * 10));
  return (
    <div className="flex flex-col items-center justify-center">
      <div
        className="grid h-56 w-56 place-items-center rounded-full"
        style={{
          background: `conic-gradient(#0284c7 ${percentage * 3.6}deg, #e0f2fe 0deg)`,
        }}
      >
        <div className="grid h-44 w-44 place-items-center rounded-full bg-white text-center shadow-inner">
          <div>
            <p className="text-4xl font-semibold text-[#123047]">
              {formatScore(score)}
            </p>
            <p className="mt-1 text-sm font-semibold tracking-[0.14em] text-[#0284c7]">
              ĐIỂM
            </p>
          </div>
        </div>
      </div>
      <p className="mt-4 text-sm font-semibold text-[#45667a]">
        {formatScore(percentage)}% hoàn thành
      </p>
    </div>
  );
}

function ResultDashboardCard({
  correctCount,
  incorrectCount,
  maxScore,
  score,
  title,
  unansweredCount,
}: {
  correctCount: number;
  incorrectCount: number;
  maxScore: number;
  score: number;
  title: string;
  unansweredCount: number;
}) {
  return (
    <section className="border border-[#bae6fd] bg-[#f8fdff] p-4">
      <p className="text-sm font-semibold tracking-[0.14em] text-[#0284c7]">
        {title}
      </p>
      <p className="mt-2 text-3xl font-semibold text-[#123047]">
        {formatScore(score)}/{formatScore(maxScore)}
      </p>
      <dl className="mt-4 grid grid-cols-3 gap-2 text-sm">
        <div>
          <dt className="text-[#45667a]">Đúng</dt>
          <dd className="font-semibold text-[#166534]">{correctCount}</dd>
        </div>
        <div>
          <dt className="text-[#45667a]">Sai</dt>
          <dd className="font-semibold text-[#991b1b]">{incorrectCount}</dd>
        </div>
        <div>
          <dt className="text-[#45667a]">Bỏ trống</dt>
          <dd className="font-semibold text-[#854d0e]">{unansweredCount}</dd>
        </div>
      </dl>
    </section>
  );
}

function TrueFalseResultStatement({
  statement,
}: {
  statement: ResultQuestion["statements"][number];
}) {
  return (
    <div
      className={`border px-4 py-3 text-sm ${
        statement.is_correct
          ? "border-[#bbf7d0] bg-[#f0fdf4] text-[#166534]"
          : "border-[#fecaca] bg-[#fff1f2] text-[#7f1d1d]"
      }`}
    >
      <p>{statement.body}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {[true, false].map((value) => {
          const isSelected = statement.selected_value === value;
          const isCorrect = statement.correct_value === value;
          return (
            <span
              className={`rounded-md border px-3 py-1 font-semibold ${
                isCorrect
                  ? "border-[#16a34a] bg-white text-[#166534]"
                  : isSelected
                    ? "border-[#dc2626] bg-white text-[#991b1b]"
                    : "border-[#bae6fd] bg-white text-[#45667a]"
              }`}
              key={String(value)}
            >
              {formatBoolean(value)}
              {isCorrect ? (
                <ResultMark isCorrect />
              ) : isSelected ? (
                <ResultMark isCorrect={false} />
              ) : null}
            </span>
          );
        })}
        {statement.selected_value === null ? (
          <span className="rounded-md border border-[#facc15] bg-white px-3 py-1 font-semibold text-[#854d0e]">
            Bỏ trống
          </span>
        ) : null}
      </div>
    </div>
  );
}

function partStats(result: AttemptResult, partNumber: number) {
  return result.questions
    .filter((question) => question.part_number === partNumber)
    .reduce(
      (stats, question) => {
        if (isResultQuestionUnanswered(question)) {
          return { ...stats, unanswered: stats.unanswered + 1 };
        }
        if (question.earned_score === question.max_score) {
          return { ...stats, correct: stats.correct + 1 };
        }
        return { ...stats, incorrect: stats.incorrect + 1 };
      },
      { correct: 0, incorrect: 0, unanswered: 0 },
    );
}

function isResultQuestionUnanswered(question: ResultQuestion) {
  if (question.question_type === "multiple_choice") {
    return question.selected_option_id === null;
  }
  return question.statements.some(
    (statement) => statement.selected_value === null,
  );
}

function formatBoolean(value: boolean | null) {
  if (value === null) {
    return "Bỏ trống";
  }
  return value ? "Đúng" : "Sai";
}

function ResultMark({ isCorrect }: { isCorrect: boolean }) {
  return (
    <span
      aria-label={isCorrect ? "Đáp án đúng" : "Bạn chọn sai"}
      className={`ml-2 text-base font-bold ${
        isCorrect ? "text-[#16a34a]" : "text-[#dc2626]"
      }`}
      role="img"
      title={isCorrect ? "Đáp án đúng" : "Bạn chọn sai"}
    >
      {isCorrect ? "✓" : "X"}
    </span>
  );
}

function RetryConfirmPopup({
  isStarting,
  onCancel,
  onConfirm,
  retryFailed,
}: {
  isStarting: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  retryFailed: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-[#123047]/40 px-5">
      <section
        aria-labelledby="retry-attempt-title"
        aria-modal="true"
        className="w-full max-w-md border border-[#bae6fd] bg-white p-6 shadow-xl"
        role="dialog"
      >
        <h2 className="text-2xl font-semibold" id="retry-attempt-title">
          Làm lại đề này?
        </h2>
        <p className="mt-3 leading-7 text-[#45667a]">
          Hệ thống sẽ tạo một lượt làm mới theo phiên bản đề đang xuất bản. Kết
          quả cũ vẫn được giữ trong lịch sử.
        </p>
        {retryFailed ? (
          <p className="mt-3 text-sm font-semibold text-[#991b1b]">
            Chưa thể tạo lượt làm mới. Đề có thể không còn khả dụng.
          </p>
        ) : null}
        <div className="mt-6 flex justify-end gap-3">
          <button
            className="rounded-md border border-[#bae6fd] px-4 py-2 font-semibold text-[#45667a]"
            disabled={isStarting}
            onClick={onCancel}
            type="button"
          >
            Hủy
          </button>
          <button
            className="rounded-md bg-[#0284c7] px-4 py-2 font-semibold text-white disabled:opacity-50"
            disabled={isStarting}
            onClick={onConfirm}
            type="button"
          >
            {isStarting ? "Đang tạo..." : "Làm lại"}
          </button>
        </div>
      </section>
    </div>
  );
}

function LeaveConfirmPopup({
  isPausing,
  isSaving,
  onCancel,
  onConfirm,
  pauseFailed,
}: {
  isPausing: boolean;
  isSaving: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  pauseFailed: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-[#123047]/40 px-5">
      <section
        aria-labelledby="leave-attempt-title"
        aria-modal="true"
        className="w-full max-w-md border border-[#bae6fd] bg-white p-6 shadow-xl"
        role="dialog"
      >
        <h2 className="text-2xl font-semibold" id="leave-attempt-title">
          Rời khỏi bài đang làm?
        </h2>
        <p className="mt-3 leading-7 text-[#45667a]">
          Thời gian còn lại sẽ được tạm dừng và các đáp án đã lưu sẽ được giữ
          lại để bạn tiếp tục sau.
        </p>
        {isSaving ? (
          <p className="mt-3 text-sm font-semibold text-[#45667a]">
            Đang lưu đáp án mới nhất...
          </p>
        ) : null}
        {pauseFailed ? (
          <p className="mt-3 text-sm font-semibold text-[#991b1b]">
            Chưa thể tạm dừng lượt làm. Hãy thử lại.
          </p>
        ) : null}
        <div className="mt-6 flex justify-end gap-3">
          <button
            className="rounded-md border border-[#bae6fd] px-4 py-2 font-semibold text-[#45667a]"
            disabled={isPausing}
            onClick={onCancel}
            type="button"
          >
            Ở lại làm bài
          </button>
          <button
            className="rounded-md bg-[#0284c7] px-4 py-2 font-semibold text-white"
            disabled={isPausing || isSaving}
            onClick={onConfirm}
            type="button"
          >
            {isPausing ? "Đang tạm dừng..." : "Rời khỏi"}
          </button>
        </div>
      </section>
    </div>
  );
}

function SubmitConfirmPopup({
  isSubmitting,
  onCancel,
  onConfirm,
  unansweredCount,
}: {
  isSubmitting: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  unansweredCount: number;
}) {
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-[#123047]/40 px-5">
      <section className="w-full max-w-md border border-[#bae6fd] bg-white p-6 shadow-xl">
        <p className="text-sm font-semibold tracking-[0.14em] text-[#0284c7]">
          XÁC NHẬN NỘP BÀI
        </p>
        <h2 className="mt-3 text-2xl font-semibold">Bạn muốn nộp bài?</h2>
        <p className="mt-3 leading-7 text-[#45667a]">
          {unansweredCount > 0
            ? `Bạn còn ${unansweredCount} câu chưa hoàn tất. Sau khi nộp, bài sẽ được khóa và chuyển sang màn hình kết quả.`
            : "Bài sẽ được khóa và chuyển sang màn hình kết quả sau khi nộp."}
        </p>
        <div className="mt-6 flex justify-end gap-3">
          <button
            className="rounded-md border border-[#bae6fd] px-4 py-2 font-semibold text-[#45667a]"
            disabled={isSubmitting}
            onClick={onCancel}
            type="button"
          >
            Xem lại
          </button>
          <button
            className="rounded-md bg-[#0284c7] px-4 py-2 font-semibold text-white disabled:opacity-50"
            disabled={isSubmitting}
            onClick={onConfirm}
            type="button"
          >
            {isSubmitting ? "Đang nộp..." : "Nộp bài"}
          </button>
        </div>
      </section>
    </div>
  );
}
