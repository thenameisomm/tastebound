"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { Banner } from "@/components/Banner";
import { ErrorPanel } from "@/components/ErrorPanel";
import type { DemoResponse, RunOut } from "@/lib/types";

export default function SamplePage() {
  const [demo, setDemo] = useState<DemoResponse | null>(null);
  const [run, setRun] = useState<RunOut | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    let cancelled = false;
    void api
      .get<DemoResponse>("/v1/demo")
      .then(async (payload) => {
        if (cancelled) return;
        setDemo(payload);
        try {
          const runPayload = await api.get<RunOut>(`/v1/runs/${payload.run_id}`);
          if (!cancelled) setRun(runPayload);
        } catch {
          // the stored run is best-effort; the header below still renders
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <main className="page">
        <div className="section">
          <ErrorPanel error={error} />
        </div>
      </main>
    );
  }

  if (!demo) {
    return (
      <main className="page">
        <div className="section stack">
          <div className="skeleton" style={{ height: 40, width: 320 }} />
          <div className="skeleton" style={{ height: 120 }} />
          <div className="skeleton" style={{ height: 64, width: 360 }} />
        </div>
      </main>
    );
  }

  return (
    <main className="page pageNarrow">
      <div className="stack" style={{ marginTop: 48 }}>
        <span className="pill pillWarm" style={{ alignSelf: "flex-start" }}>
          Sample run · stored {run ? formatDate(run.created_at) : "date unavailable"}
        </span>
        <h1 className="displaySm">{demo.headline}</h1>
        <p className="serif" style={{ fontSize: 18 }}>
          A stored, read-only run for {demo.destination}. No Qloo quota and no sign-up — explore the
          full results, plan and trace exactly as they were produced.
        </p>
        <Banner tone="info">
          This run is read-only: editing, rescoring and deep dives are disabled on the sample.
        </Banner>
        <div className="row" style={{ gap: 12 }}>
          <Link className="btnPrimary" href={`/runs/${demo.run_id}`}>
            Open the results
          </Link>
          <Link className="btnOutline" href={`/runs/${demo.run_id}/plan`}>
            Budget & briefs
          </Link>
          <Link className="btnOutline" href={`/runs/${demo.run_id}/trace`}>
            Trace
          </Link>
        </div>
        {demo.shortlist.length > 0 ? (
          <div className="stackSm">
            <span className="kindTag">Shortlisted markets</span>
            <div className="row" style={{ gap: 6 }}>
              {demo.shortlist.map((city) => (
                <span key={city} className="chip">
                  {city}
                </span>
              ))}
            </div>
          </div>
        ) : null}
        <p className="caption">
          Taste fit, not a visitor forecast. Every number links to the Qloo call that produced it in
          the trace.
        </p>
      </div>
    </main>
  );
}
