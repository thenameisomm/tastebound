"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  QUADRANT_HELP,
  QUADRANT_LABELS,
  flagLabel,
  formatLift,
  formatScore,
  formatShare,
  quadrantClass,
} from "@/lib/format";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { ScoreCell } from "./ScoreCell";
import type { MarketRow } from "@/lib/types";

type SortKey = "rank" | "city" | "taste_score" | "lift" | "coverage" | "arrivals_share" | "gap";

export function MarketTable({
  markets,
  runId,
  selectable = false,
  selected = [],
  onToggle,
}: {
  markets: MarketRow[];
  runId: string;
  selectable?: boolean;
  selected?: string[];
  onToggle?: (marketId: string) => void;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("rank");
  const [sortAsc, setSortAsc] = useState(true);
  const [region, setRegion] = useState("all");
  const [confidence, setConfidence] = useState("all");
  const [quadrant, setQuadrant] = useState("all");
  const [query, setQuery] = useState("");

  const regions = useMemo(
    () => Array.from(new Set(markets.map((market) => market.region))).sort(),
    [markets],
  );

  const visible = useMemo(() => {
    const filtered = markets.filter((market) => {
      if (region !== "all" && market.region !== region) return false;
      if (confidence !== "all" && market.confidence !== confidence) return false;
      if (quadrant !== "all" && market.quadrant !== quadrant) return false;
      if (query && !`${market.city} ${market.country_name}`.toLowerCase().includes(query.toLowerCase()))
        return false;
      return true;
    });
    const direction = sortAsc ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const aValue = a[sortKey];
      const bValue = b[sortKey];
      if (aValue === null || aValue === undefined) return 1;
      if (bValue === null || bValue === undefined) return -1;
      if (typeof aValue === "string" && typeof bValue === "string") {
        return aValue.localeCompare(bValue) * direction;
      }
      return ((aValue as number) - (bValue as number)) * direction;
    });
  }, [markets, region, confidence, quadrant, query, sortKey, sortAsc]);

  const header = (key: SortKey, label: string, title: string) => (
    <th
      scope="col"
      title={title}
      aria-sort={sortKey === key ? (sortAsc ? "ascending" : "descending") : "none"}
    >
      <button
        type="button"
        className="sortButton"
        onClick={() => {
          if (sortKey === key) {
            setSortAsc(!sortAsc);
          } else {
            setSortKey(key);
            setSortAsc(true);
          }
        }}
      >
        {label}
        <span aria-hidden="true">{sortKey === key ? (sortAsc ? "↑" : "↓") : ""}</span>
      </button>
    </th>
  );

  return (
    <div className="stack">
      <div className="filterRow">
        <label className="field">
          <span className="label">Region</span>
          <select className="select" value={region} onChange={(event) => setRegion(event.target.value)}>
            <option value="all">All regions</option>
            {regions.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span className="label">Confidence</span>
          <select
            className="select"
            value={confidence}
            onChange={(event) => setConfidence(event.target.value)}
          >
            <option value="all">All</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </label>
        <label className="field">
          <span className="label">Quadrant</span>
          <select
            className="select"
            value={quadrant}
            onChange={(event) => setQuadrant(event.target.value)}
          >
            <option value="all">All quadrants</option>
            <option value="untapped">Untapped</option>
            <option value="core">Core</option>
            <option value="habit">Habit</option>
            <option value="low_priority">Low priority</option>
          </select>
        </label>
        <label className="field fieldGrow">
          <span className="label">Search</span>
          <input
            className="input"
            type="search"
            placeholder="City or country"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
      </div>

      {visible.length === 0 ? (
        <div className="empty">No markets match these filters.</div>
      ) : (
        <>
          <div className="tableWrap desktopOnly">
            <table className="table">
              <caption>
                {visible.length} of {markets.length} markets. Taste score is the percentile of lift
                within this run; it is taste fit, not a visitor forecast.
              </caption>
              <thead>
                <tr>
                  {selectable ? <th scope="col">Pick</th> : null}
                  {header("rank", "Rank", "Rank by taste score within this run's markets")}
                  {header("city", "Market", "Destination market city and country")}
                  {header("taste_score", "Taste score", "Percentile of lift across this run's markets (0–100)")}
                  {header("lift", "Lift", "Raw taste affinity for this destination minus the run's typical affinity")}
                  {header("coverage", "Coverage", "Share of profile entities with Qloo signals in this market")}
                  <th scope="col" title="Confidence from coverage and stability of the signal">
                    Confidence
                  </th>
                  {header("arrivals_share", "Arrivals", "Share of your uploaded arrivals in this market")}
                  {header("gap", "Gap", "Taste percentile minus arrivals percentile")}
                  <th scope="col" title="Quadrant from taste and arrivals thresholds">
                    Quadrant
                  </th>
                  <th scope="col">Flags</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((market) => (
                  <tr key={market.market_id}>
                    {selectable ? (
                      <td>
                        <input
                          type="checkbox"
                          checked={selected.includes(market.market_id)}
                          onChange={() => onToggle?.(market.market_id)}
                          aria-label={`Select ${market.city} for deep dive`}
                        />
                      </td>
                    ) : null}
                    <td className="num">{market.rank ?? "—"}</td>
                    <td>
                      <Link className="tableLink" href={`/runs/${runId}/markets/${market.market_id}`}>
                        {market.city}
                      </Link>
                      <div className="caption">{market.country_name}</div>
                    </td>
                    <td>
                      <ScoreCell score={market.taste_score} />
                    </td>
                    <td className="num" title="Raw affinity minus this run's typical affinity">
                      {formatLift(market.lift)}
                    </td>
                    <td className="num" title="Share of profile entities with Qloo signals here">
                      {formatShare(market.coverage)}
                    </td>
                    <td>
                      <ConfidenceBadge confidence={market.confidence} />
                    </td>
                    <td className="num" title="Share of uploaded arrivals in this market">
                      {formatShare(market.arrivals_share)}
                    </td>
                    <td className="num" title="Taste percentile minus arrivals percentile">
                      {market.gap === null ? "—" : `${market.gap >= 0 ? "+" : ""}${(market.gap * 100).toFixed(1)}`}
                    </td>
                    <td>
                      {market.quadrant ? (
                        <span className={quadrantClass(market.quadrant)} title={QUADRANT_HELP[market.quadrant]}>
                          {QUADRANT_LABELS[market.quadrant]}
                        </span>
                      ) : (
                        <span className="faint">—</span>
                      )}
                    </td>
                    <td>
                      {market.flags.length === 0 ? (
                        <span className="faint">—</span>
                      ) : (
                        <div className="row" style={{ gap: 4 }}>
                          {market.flags.map((flag) => (
                            <span key={flag} className="pill pillWarn" title="Caveat from the scoring step">
                              {flagLabel(flag)}
                            </span>
                          ))}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mobileOnly stackSm">
            {visible.map((market) => (
              <Link
                key={market.market_id}
                href={`/runs/${runId}/markets/${market.market_id}`}
                className="card cardTight stackSm"
              >
                <div className="spread">
                  <strong>
                    #{market.rank ?? "—"} {market.city}
                  </strong>
                  <ScoreCell score={market.taste_score} />
                </div>
                <div className="row" style={{ gap: 6 }}>
                  <ConfidenceBadge confidence={market.confidence} />
                  {market.quadrant ? (
                    <span className={quadrantClass(market.quadrant)}>{QUADRANT_LABELS[market.quadrant]}</span>
                  ) : null}
                  {market.flags.map((flag) => (
                    <span key={flag} className="pill pillWarn">
                      {flagLabel(flag)}
                    </span>
                  ))}
                </div>
                <div className="caption">
                  {market.country_name} · lift {formatLift(market.lift)} · coverage{" "}
                  {formatShare(market.coverage)} · arrivals {formatShare(market.arrivals_share)}
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
