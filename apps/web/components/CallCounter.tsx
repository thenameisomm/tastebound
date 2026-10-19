import type { RunOut } from "@/lib/types";

export function CallCounter({ run }: { run: RunOut }) {
  const { counters } = run;
  const total = counters.qloo_live + counters.qloo_cached;
  return (
    <div className="row" style={{ gap: 8 }}>
      <span className="pill pillSky" title="Qloo API calls: live + served from the local cache">
        Qloo calls {total}
      </span>
      <span className="pill" title="Qloo calls served from cache (no quota spent)">
        cached {counters.qloo_cached}
      </span>
      <span className="pill" title="LLM calls made by the agent">
        LLM {counters.llm}
      </span>
      <span className="pill" title="Agent tool invocations">
        tools {counters.tools}
      </span>
    </div>
  );
}
