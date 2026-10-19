"use client";

import { useMemo } from "react";
import type { RunStreamEvent } from "@/lib/sse";

interface LiveQlooCounterProps {
  events: RunStreamEvent[];
  runCounters: { qloo_live: number; qloo_cached: number };
}

export function LiveQlooCounter({ events, runCounters }: LiveQlooCounterProps) {
  const liveFromEvents = useMemo(() => {
    let live = 0;
    let cached = 0;
    for (const event of events) {
      if (event.type === "qloo_call") {
        if (event.payload.cache_hit === true) {
          cached += 1;
        } else {
          live += 1;
        }
      }
    }
    return { live, cached };
  }, [events]);

  // Use SSE counts if available, otherwise fall back to run counters
  const live = liveFromEvents.live > 0 ? liveFromEvents.live : runCounters.qloo_live;
  const cached = liveFromEvents.cached > 0 ? liveFromEvents.cached : runCounters.qloo_cached;
  const total = live + cached;

  return (
    <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
      <span className="pill pillSky" title="Qloo API calls: live + served from the local cache">
        Qloo calls {total}
      </span>
      <span className="pill" title="Qloo calls served from cache (no quota spent)">
        cached {cached}
      </span>
      <span className="pill" title="Live Qloo API requests made">
        live {live}
      </span>
      {liveFromEvents.live > 0 && (
        <span className="pill pillSky" style={{ fontSize: 11, opacity: 0.8 }}>
          live from SSE
        </span>
      )}
    </div>
  );
}
