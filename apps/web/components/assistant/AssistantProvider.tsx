"use client";

import { usePathname } from "next/navigation";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { api, ApiError } from "@/lib/api";
import type {
  AssistantAnswer,
  AssistantBootstrap,
  AssistantConversation,
} from "@/lib/types";
import {
  AssistantContext,
  type AssistantController,
  type AssistantOpenOptions,
} from "./AssistantContext";
import { AssistantDrawer, type DrawerMessage } from "./AssistantDrawer";
import { AssistantLauncher } from "./AssistantLauncher";

function storageKey(runId: string): string {
  return `tb_assistant_conversation:${runId}`;
}

function readStoredConversation(runId: string): string | null {
  try {
    return window.sessionStorage.getItem(storageKey(runId));
  } catch {
    return null;
  }
}

function storeConversation(runId: string, conversationId: string | null): void {
  try {
    if (conversationId) {
      window.sessionStorage.setItem(storageKey(runId), conversationId);
    } else {
      window.sessionStorage.removeItem(storageKey(runId));
    }
  } catch {
    // Private mode: the conversation still works for this page session.
  }
}

function assistantError(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return "The assistant could not reach the API. Check that it is running and try again.";
  }
  switch (error.code) {
    case "assistant_unavailable":
      return "The model provider is not configured or is temporarily unavailable.";
    case "assistant_timeout":
      return "The model took too long to answer. Try a shorter question.";
    case "assistant_rate_limited":
      return "You have reached the assistant limit for now. Try again later.";
    case "assistant_busy":
      return "The previous answer is still being checked. Wait a moment, then try again.";
    case "assistant_ungrounded":
      return "The model's answer could not be verified against this run. Try rephrasing the question.";
    case "assistant_bad_response":
      return "The model returned an answer the app could not use. Try again.";
    case "conversation_not_found":
      return "This conversation expired. Send the question again to start a fresh one.";
    case "invalid_workspace":
      return "Your workspace session expired. Reload the page and try again.";
    default:
      return error.detail || error.title || "The assistant could not answer.";
  }
}

export function AssistantProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const runMatch = pathname?.match(/^\/runs\/([^/]+)/);
  const marketMatch = pathname?.match(/^\/runs\/[^/]+\/markets\/([^/]+)/);
  const runId = runMatch?.[1] ? decodeURIComponent(runMatch[1]) : null;
  const pathFocus = marketMatch?.[1]
    ? decodeURIComponent(marketMatch[1])
    : null;

  const [visible, setVisible] = useState(false);
  const [focusMarketId, setFocusMarketId] = useState<string | null>(pathFocus);
  const [bootstrap, setBootstrap] = useState<AssistantBootstrap | null>(null);
  const [bootstrapLoading, setBootstrapLoading] = useState(false);
  const [bootstrapError, setBootstrapError] = useState<string | null>(null);
  const [bootstrapNonce, setBootstrapNonce] = useState(0);
  const [hydrating, setHydrating] = useState(false);
  const [messages, setMessages] = useState<DrawerMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [followups, setFollowups] = useState<string[]>([]);

  const conversationRef = useRef<string | null>(null);
  const messagesRef = useRef<DrawerMessage[]>([]);
  const sendingRef = useRef(false);
  const requestSeq = useRef(0);
  const pendingPromptRef = useRef<string | null>(null);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  useEffect(() => {
    setVisible(false);
    setFocusMarketId(pathFocus);
    setBootstrap(null);
    setBootstrapError(null);
    conversationRef.current = null;
    requestSeq.current += 1;
    sendingRef.current = false;
    setSending(false);
    setMessages([]);
    setInput("");
    setError(null);
    setFollowups([]);
    pendingPromptRef.current = null;
  }, [runId, pathFocus]);

  const open = useCallback(
    (options?: AssistantOpenOptions) => {
      setVisible(true);
      setError(null);
      setFocusMarketId(options?.focusMarketId ?? pathFocus ?? null);
      if (options?.prompt) {
        pendingPromptRef.current = options.prompt;
      }
    },
    [pathFocus],
  );

  const close = useCallback(() => {
    setVisible(false);
    pendingPromptRef.current = null;
    setError(null);
  }, []);

  useEffect(() => {
    if (!visible || !runId) return;
    let cancelled = false;
    setBootstrapLoading(true);
    setBootstrapError(null);
    const query = focusMarketId
      ? `?focus_market_id=${encodeURIComponent(focusMarketId)}`
      : "";
    void api
      .get<AssistantBootstrap>(`/v1/runs/${runId}/assistant${query}`)
      .then((payload) => {
        if (!cancelled) setBootstrap(payload);
      })
      .catch((err: unknown) => {
        if (!cancelled) setBootstrapError(assistantError(err));
      })
      .finally(() => {
        if (!cancelled) setBootstrapLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [visible, runId, focusMarketId, bootstrapNonce]);

  useEffect(() => {
    if (!visible || !runId) return;
    const stored = readStoredConversation(runId);
    if (!stored) {
      setHydrating(false);
      return;
    }
    let cancelled = false;
    setHydrating(true);
    void api
      .get<AssistantConversation>(
        `/v1/runs/${runId}/assistant/conversations/${encodeURIComponent(stored)}`,
      )
      .then((payload) => {
        if (cancelled) return;
        conversationRef.current = payload.conversation_id;
        setMessages(payload.messages);
        setFollowups([]);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.code === "conversation_not_found") {
          storeConversation(runId, null);
          setMessages([]);
          setFollowups([]);
        }
        conversationRef.current = null;
      })
      .finally(() => {
        if (!cancelled) setHydrating(false);
      });
    return () => {
      cancelled = true;
    };
  }, [visible, runId]);

  const submit = useCallback(
    async (raw?: string) => {
      const question = (raw ?? input).trim();
      if (!runId || !bootstrap?.ready || !question || sendingRef.current) {
        return;
      }
      const seq = ++requestSeq.current;
      sendingRef.current = true;
      setSending(true);
      setError(null);
      setFollowups([]);
      setInput("");
      const snapshot = messagesRef.current;
      const optimistic: DrawerMessage = {
        id: `local-${Date.now()}`,
        role: "user",
        content: question,
        evidence: [],
        created_at: new Date().toISOString(),
      };
      setMessages([...snapshot, optimistic]);
      try {
        let activeConversation = conversationRef.current;
        if (!activeConversation) {
          const created = await api.post<AssistantConversation>(
            `/v1/runs/${runId}/assistant/conversations`,
            { focus_market_id: focusMarketId },
          );
          if (requestSeq.current !== seq) return;
          activeConversation = created.conversation_id;
          conversationRef.current = activeConversation;
          storeConversation(runId, activeConversation);
        }
        const answer = await api.post<AssistantAnswer>(
          `/v1/runs/${runId}/assistant/conversations/${encodeURIComponent(activeConversation)}/messages`,
          { message: question, focus_market_id: focusMarketId },
        );
        if (requestSeq.current !== seq) return;
        const assistantMessage: DrawerMessage = {
          id: answer.message_id,
          role: "assistant",
          content: answer.answer,
          evidence: answer.evidence,
          created_at: answer.created_at,
          followups: answer.followups,
        };
        setMessages([...snapshot, optimistic, assistantMessage]);
        setFollowups(answer.followups);
      } catch (err) {
        if (requestSeq.current !== seq) return;
        if (err instanceof ApiError && err.code === "conversation_not_found") {
          conversationRef.current = null;
          storeConversation(runId, null);
          setMessages([]);
          setFollowups([]);
          setInput(question);
          setError(assistantError(err));
          return;
        }
        setMessages(snapshot);
        setInput(question);
        setError(assistantError(err));
      } finally {
        if (requestSeq.current === seq) {
          sendingRef.current = false;
          setSending(false);
        }
      }
    },
    [bootstrap?.ready, focusMarketId, input, runId],
  );

  useEffect(() => {
    if (!visible || hydrating || sending || !bootstrap?.ready) return;
    const prompt = pendingPromptRef.current;
    if (!prompt) return;
    pendingPromptRef.current = null;
    void submit(prompt);
  }, [visible, hydrating, sending, bootstrap?.ready, submit]);

  const controller = useMemo<AssistantController>(
    () => ({ open, close, isOpen: visible }),
    [open, close, visible],
  );

  return (
    <AssistantContext.Provider value={controller}>
      {children}
      {runId ? (
        <AssistantLauncher visible={!visible} onClick={() => open()} />
      ) : null}
      {runId ? (
        <AssistantDrawer
          visible={visible}
          onClose={close}
          bootstrap={bootstrap}
          bootstrapLoading={bootstrapLoading}
          bootstrapError={bootstrapError}
          onRetryBootstrap={() => setBootstrapNonce((value) => value + 1)}
          messages={messages}
          sending={sending}
          hydrating={hydrating}
          input={input}
          onInput={setInput}
          onSend={(text) => void submit(text)}
          error={error}
          followups={followups}
          onSuggestion={(question) => {
            setInput(question);
            void submit(question);
          }}
        />
      ) : null}
    </AssistantContext.Provider>
  );
}
