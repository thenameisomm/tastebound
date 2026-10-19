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
      <div className="stack" style={{ marginTop: 32 }}>
        <p className="caption">
          <Link className="link" href={`/runs/${runId}`}>
            ← Back to results
          </Link>
        </p>
        <h1 className="heading">Trace</h1>
        <p className="muted">
          Every LLM step, tool call and Qloo call in order. Expand a row for the full parameters.
        </p>
      </div>

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
          <TraceTable items={trace.items} />
        )}
      </section>
    </main>
  );
}
