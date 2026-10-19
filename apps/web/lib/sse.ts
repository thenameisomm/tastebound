import { sseUrl } from "./api";

export const RUN_EVENT_TYPES = [
  "phase_started",
  "phase_done",
  "tool_call",
  "step_done",
  "qloo_call",
  "warning",
  "failed",
] as const;

export type RunEventType = (typeof RUN_EVENT_TYPES)[number] | string;

export interface RunStreamEvent {
  seq: number | null;
  type: RunEventType;
  payload: Record<string, unknown>;
}

export interface RunStreamHandlers {
  onEvent: (event: RunStreamEvent) => void;
  onOpen?: () => void;
  onReconnect?: (attempt: number) => void;
  onError?: (error: Event) => void;
}

export function subscribeRunEvents(
  runId: string,
  token: string,
  handlers: RunStreamHandlers,
): () => void {
  let source: EventSource | null = null;
  let lastSeq = 0;
  let attempt = 0;
  let closed = false;
  let retryTimer: ReturnType<typeof setTimeout> | null = null;

  const open = () => {
    if (closed) return;
    const after = lastSeq > 0 ? `?after=${lastSeq}` : "";
    source = new EventSource(sseUrl(`/v1/runs/${runId}/events${after}`, token));

    source.onopen = () => {
      if (attempt > 0) {
        handlers.onReconnect?.(attempt);
      }
      attempt = 0;
      handlers.onOpen?.();
    };

    const handle = (type: string) => (message: MessageEvent) => {
      const seq = message.lastEventId ? Number(message.lastEventId) : null;
      if (seq !== null && !Number.isNaN(seq)) {
        lastSeq = Math.max(lastSeq, seq);
      }
      let payload: Record<string, unknown> = {};
      try {
        payload = JSON.parse(message.data) as Record<string, unknown>;
      } catch {
        payload = { raw: message.data };
      }
      handlers.onEvent({ seq, type, payload });
    };

    source.onmessage = handle("message");
    for (const type of RUN_EVENT_TYPES) {
      source.addEventListener(type, handle(type));
    }

    source.onerror = (error) => {
      handlers.onError?.(error);
      if (source) {
        source.close();
        source = null;
      }
      if (closed) return;
      attempt += 1;
      const delay = Math.min(1000 * 2 ** (attempt - 1), 15000);
      retryTimer = setTimeout(open, delay);
    };
  };

  open();

  return () => {
    closed = true;
    if (retryTimer) clearTimeout(retryTimer);
    source?.close();
    source = null;
  };
}
