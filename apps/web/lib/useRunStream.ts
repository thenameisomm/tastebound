"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { subscribeRunEvents, type RunStreamEvent } from "./sse";
import { getToken } from "./api";

export function useRunStream(runId: string | null, enabled: boolean) {
  const [events, setEvents] = useState<RunStreamEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  const reset = useCallback(() => {
    setEvents([]);
    setConnected(false);
    setReconnecting(false);
  }, []);

  useEffect(() => {
    if (!runId || !enabled) return;
    let cancelled = false;

    void getToken().then((token) => {
      if (cancelled) return;
      unsubscribeRef.current = subscribeRunEvents(runId, token, {
        onEvent: (event) => {
          setEvents((current) => [...current, event]);
        },
        onOpen: () => {
          setConnected(true);
          setReconnecting(false);
        },
        onReconnect: () => {
          setReconnecting(false);
        },
        onError: () => {
          setConnected(false);
          setReconnecting(true);
        },
      });
    });

    return () => {
      cancelled = true;
      unsubscribeRef.current?.();
      unsubscribeRef.current = null;
      setConnected(false);
      setReconnecting(false);
    };
  }, [runId, enabled]);

  return { events, connected, reconnecting, reset };
}
