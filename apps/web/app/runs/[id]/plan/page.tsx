"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { BudgetSliders } from "@/components/BudgetSliders";
import { BriefEditor } from "@/components/BriefEditor";
import { EmptyState } from "@/components/EmptyState";
import { ErrorPanel } from "@/components/ErrorPanel";
import type { BriefOut, MarketListResponse } from "@/lib/types";

export default function PlanPage() {
  const params = useParams<{ id: string }>();
  const runId = params.id;

  const [markets, setMarkets] = useState<MarketListResponse | null>(null);
  const [briefs, setBriefs] = useState<BriefOut[] | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const [marketPayload, briefPayload] = await Promise.all([
          api.get<MarketListResponse>(`/v1/runs/${runId}/markets`),
          api.get<BriefOut[]>(`/v1/runs/${runId}/briefs`),
        ]);
        if (cancelled) return;
        setMarkets(marketPayload);
        setBriefs(briefPayload);
      } catch (err) {
        if (!cancelled) setError(err);
      }
    };
    void load();
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

  if (!markets || !briefs) {
    return (
      <main className="page">
        <div className="section stack">
          <div className="skeleton" style={{ height: 40, width: 240 }} />
          <div className="skeleton" style={{ height: 200 }} />
          <div className="skeleton" style={{ height: 320 }} />
        </div>
      </main>
    );
  }

  const hasScores = markets.markets.some((market) => market.taste_score !== null);

  return (
    <main className="page">
      <div className="pageHero">
        <div className="pageHeroMain">
          <Link className="backLink" href={`/runs/${runId}`}>
            ← Back to results
          </Link>
          <span className="eyebrow">Campaign planner</span>
          <h1 className="heading">Budget &amp; briefs</h1>
          <p className="pageLead">
            The split is computed from Qloo taste scores, confidence and the gap. Locks pin an
            amount before the rest is split.
          </p>
        </div>
      </div>

      {hasScores ? (
        <section className="section">
          <div className="budgetCard stack">
            <div className="stackSm">
              <span className="kindTag">Allocator</span>
              <h2 className="headingSm">Budget split, weighted by the gap.</h2>
            </div>
            <BudgetSliders runId={runId} markets={markets.markets} />
          </div>
        </section>
      ) : (
        <section className="section">
          <EmptyState title="No scores yet">
            Budget needs a scored run — start one from the results page.
          </EmptyState>
        </section>
      )}

      <section className="section">
        <div className="sectionHeader">
          <div className="stackSm">
            <span className="kindTag">Deliverables</span>
            <h2 className="headingSm">Briefs</h2>
          </div>
          <span className="caption">
            One brief per shortlisted market. Template briefs are generated from Qloo evidence when
            the LLM is unavailable.
          </span>
        </div>
        <div className="stack sectionSm">
          {briefs.length === 0 ? (
            <EmptyState title="No briefs yet">
              Briefs appear after a deep dive. Pick markets on the results page and deep dive.
            </EmptyState>
          ) : (
            briefs.map((brief) => (
              <BriefEditor key={brief.id} brief={brief} onSaved={(updated) => setBriefs((current) => current?.map((item) => (item.id === updated.id ? updated : item)) ?? null)} />
            ))
          )}
        </div>
      </section>
    </main>
  );
}
