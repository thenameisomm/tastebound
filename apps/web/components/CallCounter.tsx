"use client";

import { useMemo } from "react";
import type { RunOut } from "@/lib/types";
import type { RunStreamEvent } from "@/lib/sse";

interface CallCounterProps {
  run: RunOut;
  events?: RunStreamEvent[];
}

export function CallCounter({ run, events = [] }: CallCounterProps) {
  const sseCounts = useMemo(() => {
    let qloo_live = 0;
    let qloo_cached = 0;
    let llm = 0;
    let tools = 0;
    
    for (const event of events) {
      if (event.type === "qloo_call") {
        if (event.payload.cache_hit === true) {
          qloo_cached += 1;
        } else {
          qloo_live += 1;
        }
      } else if (event.type === "llm_call") {
        llm += 1;
      } else if (event.type === "tool_call") {
        tools += 1;
      }
    }
    return { qloo_live, qloo_cached, llm, tools };
  }, [events]);

  // Use SSE counts if available, otherwise fall back to run counters
  const qloo_live = sseCounts.qloo_live > 0 ? sseCounts.qloo_live : run.counters.qloo_live;
  const qloo_cached = sseCounts.qloo_cached > 0 ? sseCounts.qloo_cached : run.counters.qloo_cached;
  const llm = sseCounts.llm > 0 ? sseCounts.llm : run.counters.llm;
  const tools = sseCounts.tools > 0 ? sseCounts.tools : run.counters.tools;
  const total = qloo_live + qloo_cached;

  const hasSSE = events.length > 0 && (sseCounts.qloo_live > 0 || sseCounts.qloo_cached > 0);

  return (
    <div className="callCounter">
      <span className="pill pillSky" title="Qloo API calls: live + served from the local cache">
        Qloo calls {total}
      </span>
      <span className="pill" title="Qloo calls served from cache (no quota spent)">
        cached {qloo_cached}
      </span>
      <span className="pill" title="Live Qloo API requests made">
        live {qloo_live}
      </span>
      <span className="pill" title="LLM calls made by the agent">
        LLM {llm}
      </span>
      <span className="pill" title="Agent tool invocations">
        tools {tools}
      </span>
      {hasSSE && <span className="pill pillGood">streaming</span>}
    </div>
  );
}
