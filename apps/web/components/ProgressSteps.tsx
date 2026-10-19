import type { RunOut } from "@/lib/types";

const PHASES = ["scoring", "scored", "deep_dive", "done"] as const;

const PHASE_LABELS: Record<string, string> = {
  scoring: "Score markets",
  scored: "Find gaps",
  deep_dive: "Deep dive",
  done: "Done",
};

function phaseIndex(status: string): number {
  const index = PHASES.indexOf(status as (typeof PHASES)[number]);
  if (index >= 0) return index;
  if (status === "partial") return PHASES.length - 1;
  return -1;
}

export function ProgressSteps({ run }: { run: RunOut }) {
  const current = phaseIndex(run.status);
  const failed = run.status === "failed";
  return (
    <div className="steps" role="list" aria-label="Run progress">
      {PHASES.map((phase, index) => {
        const done = current > index || run.status === "done";
        const active = current === index && run.status !== "done";
        const className = [
          "step",
          active ? "stepActive" : "",
          done ? "stepDone" : "",
          failed && active ? "stepFailed" : "",
        ]
          .filter(Boolean)
          .join(" ");
        return (
          <div key={phase} className={className} role="listitem">
            <span className="stepNum">{index + 1}</span>
            {PHASE_LABELS[phase]}
          </div>
        );
      })}
      {failed ? <span className="pill pillBad">failed</span> : null}
      {run.status === "partial" ? <span className="pill pillWarn">partial</span> : null}
    </div>
  );
}
