"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { EmptyState } from "@/components/EmptyState";
import { ErrorPanel } from "@/components/ErrorPanel";
import { TraceTable } from "@/components/TraceTable";
import type { TraceResponse } from "@/lib/types";

export default function TracePage() {
  const params = useParams<{ id: string }>();
  const runId = params.id;

  const [trace, setTrace] = useState<TraceResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [highlightCall, setHighlightCall] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setHighlightCall(params.get("call"));
  }, []);

  useEffect(() => {
    let cancelled = false;
    void api
      .get<TraceResponse>(`/v1/runs/${runId}/trace`)
      .then((payload) => {
        if (!cancelled) setTrace(payload);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err);
      });
    return () => {
      cancelled = true;
    };
  }, [runId]);

  if (error instanceof ApiError && error.status === 404) {
    return (
      <main className="page">
        <div className="section">
          <EmptyState title="Run not found">This run does not exist or belongs to another workspace.</EmptyState>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page">
        <div className="section">
          <ErrorPanel error={error} />
        </div>
      </main>
    );
  }

  return (
    <main className="page">
      <div className="pageHero">
        <div className="pageHeroMain">
          <Link className="backLink" href={`/runs/${runId}`}>
            ← Back to results
          </Link>
          <span className="eyebrow">Audit log</span>
          <h1 className="heading">Trace</h1>
          <p className="pageLead">
            Every LLM step, tool call and Qloo call in order. Expand a row for the full parameters.
          </p>
          {highlightCall ? (
            <p className="pageMeta">
              <span>Highlighting evidence call {highlightCall}</span>
            </p>
          ) : null}
        </div>
      </div>

      {trace ? (
        <div className="statGrid sectionSm">
          <div className="stat">
            <span className="statLabel">Qloo calls</span>
            <span className="statValue">
              {trace.items.filter((item) => item.kind === "qloo").length}
            </span>
            <span className="statNote">Live and cached requests</span>
          </div>
          <div className="stat">
            <span className="statLabel">LLM calls</span>
            <span className="statValue">
              {trace.items.filter((item) => item.kind === "llm").length}
            </span>
            <span className="statNote">Proposals and written briefs</span>
          </div>
          <div className="stat">
            <span className="statLabel">Tool calls</span>
            <span className="statValue">
              {trace.items.filter((item) => item.kind === "tool").length}
            </span>
            <span className="statNote">Deterministic agent tools</span>
          </div>
          <div className="stat statDark">
            <span className="statLabel">Total events</span>
            <span className="statValue">{trace.items.length}</span>
            <span className="statNote">Ordered, timestamped, inspectable</span>
          </div>
        </div>
      ) : null}

      <section className="section">
        {trace === null ? (
          <div className="stack">
            {[0, 1, 2, 3, 4].map((index) => (
              <div key={index} className="skeleton" style={{ height: 56 }} />
            ))}
          </div>
        ) : trace.items.length === 0 ? (
          <EmptyState title="Nothing traced yet">Events appear here as the run progresses.</EmptyState>
        ) : (
          <TraceTable items={trace.items} highlightCallId={highlightCall} />
        )}
      </section>
    </main>
  );
}
