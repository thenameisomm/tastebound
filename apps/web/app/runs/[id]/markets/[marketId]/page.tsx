"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import {
  QUADRANT_HELP,
  QUADRANT_LABELS,
  confidenceHelp,
  flagLabel,
  formatCurrency,
  formatLift,
  formatScore,
  formatShare,
  quadrantClass,
} from "@/lib/format";
import { AssistantButton } from "@/components/assistant/AssistantButton";
import { AudienceBars } from "@/components/AudienceBars";
import { Banner } from "@/components/Banner";
import { ConfidenceBadge } from "@/components/ConfidenceBadge";
import { EmptyState } from "@/components/EmptyState";
import { ErrorPanel } from "@/components/ErrorPanel";
import { EvidenceList } from "@/components/EvidenceList";
import { PartnerTabs } from "@/components/PartnerTabs";
import { SourceChip } from "@/components/SourceChip";
import type { MarketDetailResponse } from "@/lib/types";

export default function MarketDetailPage() {
  const params = useParams<{ id: string; marketId: string }>();
  const { id: runId, marketId } = params;

  const [detail, setDetail] = useState<MarketDetailResponse | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const payload = await api.get<MarketDetailResponse>(`/v1/runs/${runId}/markets/${marketId}`);
        if (!cancelled) setDetail(payload);
      } catch (err) {
        if (!cancelled) setError(err);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [runId, marketId]);

  if (error instanceof ApiError && error.status === 404) {
    return (
      <main className="page">
        <div className="section">
          <EmptyState title="Market not found">This market is not part of this run.</EmptyState>
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

  if (!detail) {
    return (
      <main className="page">
        <div className="section stack">
          <div className="skeleton" style={{ height: 40, width: 240 }} />
          <div className="grid4">
            {[0, 1, 2, 3].map((index) => (
              <div key={index} className="skeleton" style={{ height: 96 }} />
            ))}
          </div>
          <div className="skeleton" style={{ height: 240 }} />
        </div>
      </main>
    );
  }

  const { market, score, audience, audience_note, angle, partners, brands, arrivals_source_note } = detail;

  return (
    <main className="page">
      <div className="pageHero">
        <div className="pageHeroMain">
          <Link className="backLink" href={`/runs/${runId}`}>
            ← Back to results
          </Link>
          <span className="eyebrow">Market brief / {market.region}</span>
          <div className="marketTitleRow">
            <h1 className="display">{market.city}</h1>
            {score.quadrant ? (
              <span
                className={quadrantClass(score.quadrant)}
                title={QUADRANT_HELP[score.quadrant]}
              >
                {QUADRANT_LABELS[score.quadrant]}
              </span>
            ) : null}
          </div>
          <p className="pageMeta">
            <span>
              {market.country_name} · {market.region}
            </span>
            {score.rank !== null ? <span>Rank #{score.rank} in this run</span> : null}
            <span>Taste fit, not a visitor forecast</span>
          </p>
          <div className="assistantContextActions">
            <AssistantButton
              focusMarketId={marketId}
              prompt={`Explain ${market.city}'s taste score and what the evidence supports.`}
            >
              Ask about this market
            </AssistantButton>
          </div>
        </div>
      </div>

      <div className="statGrid sectionSm" id="score">
        <div className="stat statDark">
          <span className="statLabel">Taste score</span>
          <span
            className="statValue"
            title="Percentile of lift across this run's markets (0–100). Taste fit, not a visitor forecast."
          >
            {formatScore(score.taste_score)}
          </span>
          <span className="statNote">Percentile of lift, 0–100</span>
        </div>
        <div className="stat">
          <span className="statLabel">Lift</span>
          <span
            className="statValue"
            title="Qloo affinity with this destination's signals minus the same market queried without them"
          >
            {formatLift(score.lift)}
          </span>
          <span className="statNote">Target vs baseline affinity</span>
        </div>
        <div className="stat">
          <span className="statLabel">Coverage</span>
          <span
            className="statValue"
            title="Share of the destination's profile entities with Qloo signals in this market"
          >
            {formatShare(score.coverage)}
          </span>
          <span className="statNote">Of profile entities have signals here</span>
        </div>
        <div className="stat">
          <span className="statLabel">Confidence</span>
          <span style={{ marginTop: 4 }}>
            <ConfidenceBadge confidence={score.confidence} />
          </span>
          <span className="statNote">{confidenceHelp(score.confidence)}</span>
        </div>
      </div>

      {score.flags.length > 0 ? (
        <div className="sectionSm">
          <Banner tone="warn">
            {score.flags.map(flagLabel).join(" · ")} — read this market&apos;s numbers with care.
          </Banner>
        </div>
      ) : null}

      <section className="section grid2">
        <div className="card stack">
          <div className="stackSm">
            <span className="kindTag">Evidence</span>
            <h2 className="headingSm">Arrivals &amp; gap</h2>
          </div>
          <dl className="kv">
            <dt title="Share of your uploaded arrivals in this market">Arrivals share</dt>
            <dd className="num">{formatShare(score.arrivals_share)}</dd>
            <dt title="Percentile of arrivals share across markets with arrivals">Arrivals percentile</dt>
            <dd className="num">{score.arrivals_pct === null ? "—" : score.arrivals_pct.toFixed(1)}</dd>
            <dt title="Taste percentile minus arrivals percentile">Gap</dt>
            <dd className="num">
              {score.gap === null ? "—" : `${score.gap >= 0 ? "+" : ""}${(score.gap * 100).toFixed(1)} points`}
            </dd>
          </dl>
          {arrivals_source_note ? (
            <SourceChip label={`arrivals: ${arrivals_source_note}`} title="Source note you provided with the arrivals upload" />
          ) : (
            <span className="caption">No arrivals attached to this run.</span>
          )}
        </div>

        <div className="card stack" id="audience">
          <div className="spread">
            <div className="stackSm">
              <span className="kindTag">Signal</span>
              <h2 className="headingSm">Audience</h2>
            </div>
            {audience_note ? <span className="caption">{audience_note}</span> : null}
          </div>
          <AudienceBars audience={audience} />
        </div>
      </section>

      <section className="section" id="angle">
        {angle ? (
          <div className="angleCard stack">
            <div className="spread">
              <span className="kindTag">Campaign angle</span>
              <span className="pill pillGood">evidence attached</span>
            </div>
            <p className="angleHeadline">{angle.headline}</p>
            <EvidenceList evidence={angle.evidence} />
          </div>
        ) : (
          <div className="card stack">
            <h2 className="headingSm">Campaign angle</h2>
            <p className="muted">
              No angle yet. Pick this market in a deep dive on the{" "}
              <Link className="link" href={`/runs/${runId}`}>
                results page
              </Link>
              .
            </p>
          </div>
        )}
      </section>

      <section className="section grid2">
        <div className="card stack" id="partners">
          <div className="stackSm">
            <span className="kindTag">Media</span>
            <h2 className="headingSm">Partners</h2>
          </div>
          <PartnerTabs partners={partners} />
        </div>
        <div className="card stack">
          <div className="stackSm">
            <span className="kindTag">Brands</span>
            <h2 className="headingSm">Global brands</h2>
          </div>
          {brands.length > 0 ? (
            <ul>
              {brands.map((brand) => (
                <li key={brand.entity_id} className="partnerRow">
                  <span className="partnerName">{brand.name}</span>
                  <span className="num caption" title="Taste lift of this brand against the destination profile">
                    {formatLift(brand.lift)}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">No global brands recorded for this profile yet.</p>
          )}
        </div>
      </section>

      {detail.allocation_share !== null ? (
        <section className="section">
          <div className="cardTint spread">
            <span>
              Budget share from the latest plan: <strong>{formatShare(detail.allocation_share)}</strong>
            </span>
            {detail.budget_amount !== null ? (
              <strong className="num">{formatCurrency(detail.budget_amount, "EUR")}</strong>
            ) : null}
            <Link className="btnOutline" href={`/runs/${runId}/plan`}>
              Open plan
            </Link>
          </div>
        </section>
      ) : null}
    </main>
  );
}
