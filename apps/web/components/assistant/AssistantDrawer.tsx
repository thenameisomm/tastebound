"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import type { AssistantBootstrap, AssistantMessage } from "@/lib/types";

export type DrawerMessage = AssistantMessage & { followups?: string[] };

type Props = {
  visible: boolean;
  onClose: () => void;
  bootstrap: AssistantBootstrap | null;
  bootstrapLoading: boolean;
  bootstrapError: string | null;
  onRetryBootstrap: () => void;
  messages: DrawerMessage[];
  sending: boolean;
  hydrating: boolean;
  input: string;
  onInput: (value: string) => void;
  onSend: (text?: string) => void;
  error: string | null;
  followups: string[];
  onSuggestion: (question: string) => void;
};

function focusables(panel: HTMLElement): HTMLElement[] {
  return Array.from(
    panel.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ),
  ).filter((element) => element.offsetParent !== null);
}

export function AssistantDrawer({
  visible,
  onClose,
  bootstrap,
  bootstrapLoading,
  bootstrapError,
  onRetryBootstrap,
  messages,
  sending,
  hydrating,
  input,
  onInput,
  onSend,
  error,
  followups,
  onSuggestion,
}: Props) {
  const panelRef = useRef<HTMLDivElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (!visible) return;
    const previous =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    panelRef.current?.focus();

    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab" || !panelRef.current) return;
      const items = focusables(panelRef.current);
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (!first || !last) return;
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => {
      window.removeEventListener("keydown", handleKey);
      document.body.style.overflow = previousOverflow;
      previous?.focus();
    };
  }, [visible, onClose]);

  useEffect(() => {
    if (visible) endRef.current?.scrollIntoView({ block: "end" });
  }, [visible, messages.length, sending]);

  useEffect(() => {
    if (!sending) {
      setElapsedSeconds(0);
      return;
    }
    const started = Date.now();
    setElapsedSeconds(0);
    const timer = window.setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - started) / 1000));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [sending]);

  if (!visible) return null;

  const ready = Boolean(
    bootstrap?.enabled && bootstrap.ready && !bootstrapError,
  );
  const maxChars = bootstrap?.max_message_chars ?? 800;
  const canSend = ready && !sending && !hydrating && input.trim().length > 0;

  return (
    <div className="assistantLayer">
      <button
        type="button"
        className="assistantBackdrop"
        aria-label="Close results assistant"
        onClick={onClose}
        tabIndex={-1}
      />
      <div
        ref={panelRef}
        className="assistantPanel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="assistant-title"
        aria-describedby="assistant-description"
        tabIndex={-1}
      >
        <div className="assistantHeader">
          <div className="assistantHeaderMain">
            <span className="eyebrow">Results assistant</span>
            <h2 id="assistant-title" className="assistantTitle">
              Ask the run
            </h2>
          </div>
          <div className="assistantHeaderActions">
            {bootstrap?.model ? (
              <span className="pill pillMuted">{bootstrap.model}</span>
            ) : null}
            <button
              type="button"
              className="assistantClose"
              onClick={onClose}
              aria-label="Close results assistant"
            >
              ×
            </button>
          </div>
        </div>

        <div className="assistantBody">
          <p id="assistant-description" className="assistantIntro">
            Answers use this run&apos;s scores and evidence. Taste fit, not a
            visitor forecast.
          </p>

          {bootstrapError ? (
            <div className="assistantNotice assistantNoticeError" role="alert">
              <strong>Assistant unavailable</strong>
              <span>{bootstrapError}</span>
              <button
                type="button"
                className="btnOutline btnSmall"
                onClick={onRetryBootstrap}
              >
                Try again
              </button>
            </div>
          ) : null}

          {bootstrapLoading && !bootstrap ? (
            <div className="assistantNotice" aria-live="polite">
              Checking what this run supports…
            </div>
          ) : null}

          {hydrating ? (
            <div className="assistantNotice" aria-live="polite">
              Restoring this conversation…
            </div>
          ) : null}

          {bootstrap && !bootstrap.enabled ? (
            <div className="assistantNotice">
              <strong>No model configured</strong>
              <span>
                {bootstrap.notice ?? "The results assistant is unavailable."}
              </span>
              <span className="caption">
                Results remain fully usable; the assistant needs a configured
                model provider.
              </span>
            </div>
          ) : null}

          {bootstrap && bootstrap.enabled && !bootstrap.ready ? (
            <div className="assistantNotice">
              <strong>Results are not ready</strong>
              <span>
                {bootstrap.notice ?? "This run has not been scored yet."}
              </span>
            </div>
          ) : null}

          {messages.length === 0 && bootstrap?.ready ? (
            <div className="assistantIntroBlock">
              <span className="kindTag">Start with</span>
              <div className="assistantSuggestions">
                {bootstrap.suggested_questions.map((question) => (
                  <button
                    key={question}
                    type="button"
                    className="assistantSuggestion"
                    onClick={() => onSuggestion(question)}
                    disabled={sending || hydrating}
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          <div className="assistantMessages" aria-live="polite">
            {messages.map((message) => (
              <article
                key={message.id}
                className={
                  message.role === "user"
                    ? "assistantMessageUser"
                    : "assistantMessageBot"
                }
              >
                <span className="assistantMessageRole">
                  {message.role === "user" ? "You" : "TasteBound"}
                </span>
                <p className="assistantMessageText">{message.content}</p>
                {message.evidence && message.evidence.length > 0 ? (
                  <div className="assistantEvidence">
                    <span className="kindTag">Evidence</span>
                    {message.evidence.map((item) => (
                      <Link
                        key={item.id}
                        className="assistantEvidenceLink"
                        href={item.href}
                        onClick={onClose}
                      >
                        <span className="assistantEvidenceId">{item.id}</span>
                        <span>
                          <strong>{item.label}</strong>
                          <span className="assistantEvidenceDetail">
                            {item.detail}
                          </span>
                        </span>
                      </Link>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}

            {sending ? (
              <div
                className="assistantMessageBot assistantTyping"
                role="status"
              >
                <span />
                <span />
                <span />
                <em aria-hidden="true">
                  Checking the run data…
                  {elapsedSeconds > 0 ? ` ${elapsedSeconds}s` : ""}
                </em>
                <span className="srOnly">Checking the run data</span>
              </div>
            ) : null}
          </div>

          {error ? (
            <div className="assistantNotice assistantNoticeError" role="alert">
              <strong>Could not answer</strong>
              <span>{error}</span>
            </div>
          ) : null}

          {followups.length > 0 && !sending ? (
            <div className="assistantFollowups">
              <span className="kindTag">Follow up</span>
              <div className="assistantSuggestions">
                {followups.map((question) => (
                  <button
                    key={question}
                    type="button"
                    className="assistantSuggestion"
                    onClick={() => onSuggestion(question)}
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          <div ref={endRef} />
        </div>

        {bootstrap?.enabled ? (
          <form
            className="assistantComposer"
            onSubmit={(event) => {
              event.preventDefault();
              if (canSend) onSend();
            }}
          >
            <label className="srOnly" htmlFor="assistant-input">
              Ask a question about this run
            </label>
            <textarea
              id="assistant-input"
              className="textarea assistantInput"
              value={input}
              onChange={(event) =>
                onInput(event.target.value.slice(0, maxChars))
              }
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  if (canSend) onSend();
                }
              }}
              placeholder={
                ready
                  ? "Ask about scores, gaps, audience or evidence…"
                  : "Results are not ready yet"
              }
              rows={2}
              maxLength={maxChars}
              disabled={!ready || sending || hydrating}
            />
            <div className="assistantComposerRow">
              <span className="caption">
                {input.length}/{maxChars} · Enter to send, Shift+Enter for a new
                line
              </span>
              <button
                type="submit"
                className="btnPrimary btnSmall"
                disabled={!canSend}
              >
                {sending ? "Checking…" : "Send"}
              </button>
            </div>
          </form>
        ) : null}
      </div>
    </div>
  );
}
