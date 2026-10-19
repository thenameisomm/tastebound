"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE, api, ApiError, getToken } from "@/lib/api";
import { useRunStream } from "@/lib/useRunStream";
import { formatDate } from "@/lib/format";
import { Banner } from "@/components/Banner";
import { CallCounter } from "@/components/CallCounter";
import { EmptyState } from "@/components/EmptyState";
import { ErrorPanel } from "@/components/ErrorPanel";
import { GapQuadrant } from "@/components/GapQuadrant";
import { MarketTable } from "@/components/MarketTable";
import { ProgressSteps } from "@/components/ProgressSteps";
import type { MarketListResponse, RunOut } from "@/lib/types";

const TERMINAL = new Set(["done", "failed", "partial"]);

export default function RunPage() {
  const params = useParams<{ id: string }>();
  const runId = params.id;

  const [run, setRun] = useState<RunOut | null>(null);
  const [markets, setMarkets] = useState<MarketListResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [deepDiveBusy, setDeepDiveBusy] = useState(false);
  const [deepDiveError, setDeepDiveError] = useState<unknown>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const { events, reconnecting } = useRunStream(
    runId,
    Boolean(runId) && (!run || !TERMINAL.has(run.status)),
  );

  const refresh = useCallback(async () => {
    try {
      const fresh = await api.get<RunOut>(`/v1/runs/${runId}`);
      setRun(fresh);
      if (["scored", "deep_dive", "done", "partial"].includes(fresh.status)) {
        const list = await api.get<MarketListResponse>(`/v1/runs/${runId}/markets`);
        setMarkets(list);
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setError(err);
      } else {
        setError(err);
      }
    }
  }, [runId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (!run || TERMINAL.has(run.status)) {
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = null;
      return;
    }
    timerRef.current = setInterval(() => void refresh(), 1500);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = null;
    };
  }, [run, refresh]);

  useEffect(() => {
    if (events.length > 0) void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [events.length]);

  const deepDive = async () => {
    setDeepDiveBusy(true);
    setDeepDiveError(null);
    try {
      await api.post(`/v1/runs/${runId}/deep-dive`, { market_ids: selected });
      await refresh();
    } catch (err) {
      setDeepDiveError(err);
    } finally {
      setDeepDiveBusy(false);
    }
  };

  if (error instanceof ApiError && error.status === 404) {
    return (
      <main className="page">
        <div className="section">
          <EmptyState title="Run not found">
            This run does not exist or belongs to another workspace.
          </EmptyState>
        </div>
      </main>
    );
  }

  if (error && !run) {
    return (
      <main className="page">
        <div className="section">
          <ErrorPanel error={error} onRetry={() => void refresh()} />
        </div>
      </main>
    );
  }

  if (!run) {
    return (
      <main className="page">
        <div className="section stack">
          <div className="skeleton" style={{ height: 40, width: 280 }} />
          <div className="skeleton" style={{ height: 16, width: "60%" }} />
          <div className="skeleton" style={{ height: 320 }} />
        </div>
      </main>
    );
  }

  const liveEvents = events.slice(-6).reverse();
  const scored = run.status !== "queued" && run.status !== "scoring";
  const canDeepDive = ["scored", "done"].includes(run.status);

  return (
    <main className="page">
      <div className="stack" style={{ marginTop: 32 }}>
        <div className="spread">
          <div>
            <span className="eyebrow">Qloo scorecard</span>
            <h1 className="heading">Run results</h1>
            <p className="caption">
              Run {run.run_id} · created {formatDate(run.created_at)}
              {run.finished_at ? ` · finished ${formatDate(run.finished_at)}` : ""}
            </p>
          </div>
          <CallCounter run={run} />
        </div>

        <ProgressSteps run={run} />

        {reconnecting ? (
          <Banner tone="warn">Live connection lost — reconnecting…</Banner>
        ) : null}

        {run.orchestration === "deterministic_fallback" ? (
          <Banner tone="info">
            LLM unavailable{run.orchestration_reason ? ` (${run.orchestration_reason})` : ""}. The agent
            is running deterministic tools; briefs will be labelled as templates.
          </Banner>
        ) : null}

        {run.status === "failed" ? (
          <div className="banner bannerError" role="alert">
            <div className="stackSm" style={{ flex: 1 }}>
              <strong>Run failed{run.error_code ? `: ${run.error_code}` : ""}</strong>
              {run.error_message ? <span>{run.error_message}</span> : null}
              <span className="caption">
                No partial ranking is shown as complete. Fix the cause and start a new run.
              </span>
            </div>
            <button type="button" className="btnOutline" onClick={() => void refresh()}>
              Refresh
            </button>
          </div>
        ) : null}

        {run.status === "partial" ? (
          <Banner tone="warn">
            Partial run: some phases hit a limit or error. Results below are complete for the markets
            shown.
          </Banner>
        ) : null}

        {run.warnings.length > 0 ? (
          <div className="stackSm">
            {run.warnings.map((warning, index) => (
              <Banner key={index} tone="warn">
                {String((warning as { message?: string }).message ?? JSON.stringify(warning))}
              </Banner>
            ))}
          </div>
        ) : null}

        {!TERMINAL.has(run.status) ? (
          <div className="card stackSm">
            <span className="kindTag">Live progress</span>
            {liveEvents.length === 0 ? (
              <p className="muted">Waiting for the first event…</p>
            ) : (
              <ul className="stackSm" style={{ listStyle: "none" }}>
                {liveEvents.map((event, index) => (
                  <li key={`${event.seq}-${index}`} className="row" style={{ gap: 8 }}>
                    <span className="pill pillSky">{event.type}</span>
                    <span className="caption">
                      {String(event.payload.tool ?? event.payload.phase ?? "")}{" "}
                      {String(event.payload.summary && typeof event.payload.summary === "object" ? "" : event.payload.summary ?? "")}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : null}
      </div>

      {scored && markets ? (
        <section className="section">
          {markets.gap_enabled && markets.gap_note ? (
            <Banner tone="info">{markets.gap_note}</Banner>
          ) : null}
          {!markets.gap_enabled ? (
            <Banner tone="info">
              Lift-only view: no arrivals are attached to this run.{" "}
              <Link className="link" href="/start">
                Upload arrivals in a new run
              </Link>{" "}
              to see the gap quadrant.
            </Banner>
          ) : null}
          {markets.population_suspect ? (
            <Banner tone="warn">
              Population correlation is {markets.population_correlation?.toFixed(2)} — the ranking may
              partly track market size. Read lift together with coverage.
            </Banner>
          ) : null}

          <div className="sectionSm">
            <div className="spread">
              <h2 className="headingSm">Gap quadrant</h2>
              <span className="caption">
                Top-left is untapped: strong taste fit, few arrivals today.
              </span>
            </div>
            {markets.gap_enabled ? (
              <GapQuadrant markets={markets.markets} thresholds={markets.thresholds} runId={runId} />
            ) : null}
          </div>

          <div className="sectionSm">
            <div className="spread">
              <h2 className="headingSm">Markets</h2>
              {canDeepDive ? (
                <div className="row">
                  <span className="caption">{selected.length} picked for deep dive</span>
                  <button
                    type="button"
                    className="btnPrimary"
                    disabled={deepDiveBusy || selected.length < 3}
                    title={selected.length < 3 ? "Pick at least 3 markets" : "Fetch audiences, angles and partners for the picked markets"}
                    onClick={() => void deepDive()}
                  >
                    {deepDiveBusy ? "Deep diving…" : "Deep dive"}
                  </button>
                </div>
              ) : null}
            </div>
            {deepDiveError ? <ErrorPanel error={deepDiveError} onRetry={() => void deepDive()} /> : null}
            <MarketTable
              markets={markets.markets}
              runId={runId}
              selectable={canDeepDive}
              selected={selected}
              onToggle={(marketId) =>
                setSelected((current) =>
                  current.includes(marketId)
                    ? current.filter((id) => id !== marketId)
                    : [...current, marketId],
                )
              }
            />
          </div>

          {run.shortlist.length > 0 ? (
            <div className="sectionSm row">
              <span className="kindTag">Shortlist</span>
              {run.shortlist.map((marketId) => {
                const market = markets.markets.find((item) => item.market_id === marketId);
                return (
                  <Link key={marketId} className="chip" href={`/runs/${runId}/markets/${marketId}`}>
                    {market?.city ?? marketId}
                  </Link>
                );
              })}
            </div>
          ) : null}
        </section>
      ) : null}

      {TERMINAL.has(run.status) ? (
        <section className="section">
          <div className="row" style={{ gap: 12 }}>
            <Link className="btnPrimary" href={`/runs/${runId}/plan`}>
              Budget & briefs
            </Link>
            <Link className="btnOutline" href={`/runs/${runId}/trace`}>
              View trace
            </Link>
            <a
              className="btnText"
              href="#"
              onClick={async (event) => {
                event.preventDefault();
                const token = await getToken();
                const response = await fetch(`${API_BASE}/v1/runs/${runId}/export.csv`, {
                  headers: { "X-Workspace-Token": token },
                });
                if (!response.ok) return;
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const anchor = document.createElement("a");
                anchor.href = url;
                anchor.download = "tastebound-markets.csv";
                anchor.click();
                URL.revokeObjectURL(url);
              }}
            >
              Export markets CSV
            </a>
          </div>
        </section>
      ) : null}
    </main>
  );
}
