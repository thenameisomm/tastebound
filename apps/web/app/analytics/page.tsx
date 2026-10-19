"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Banner } from "@/components/Banner";
import { EmptyState } from "@/components/EmptyState";
import { SourceChip } from "@/components/SourceChip";
import { TasteScoreChart } from "@/components/charts/TasteScoreChart";
import { QuadrantScatterChart } from "@/components/charts/QuadrantScatterChart";
import type { MarketRow, ArrivalsSampleOut } from "@/lib/types";

const PRESET_LABELS: Record<string, string> = {
  us10: "US Domestic (10)",
  us20: "US Domestic (20)",
  na15: "North America (15)",
  europe20: "Europe (20)",
  apac15: "Asia-Pacific (15)",
  me8: "Middle East (8)",
  latam10: "Latin America (10)",
};

export default function AnalyticsPage() {
  const [markets, setMarkets] = useState<MarketRow[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [runs, setRuns] = useState<Array<{ run_id: string; created_at: string; status: string; destination_name?: string }>>([]);
  const [samples, setSamples] = useState<ArrivalsSampleOut[]>([]);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState<string | null>(null);

  // Filters
  const [regionFilter, setRegionFilter] = useState<string>("all");
  const [quadrantFilter, setQuadrantFilter] = useState<string>("all");
  const [minTasteScore, setMinTasteScore] = useState<number>(0);
  const [maxTasteScore, setMaxTasteScore] = useState<number>(100);
  const [minArrivals, setMinArrivals] = useState<number>(0);
  const [maxArrivals, setMaxArrivals] = useState<number>(100);
  const [sortBy, setSortBy] = useState<"taste_score" | "arrivals_share" | "lift" | "gap" | "city">("taste_score");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const loadData = async () => {
    setBusy("markets");
    setError(null);
    try {
      const [marketsPayload, runsPayload, samplesPayload] = await Promise.all([
        api.get<{ markets: MarketRow[] }>("/v1/markets"),
        api.get<Array<{ run_id: string; created_at: string; status: string }>>("/v1/runs?limit=20"),
        api.get<ArrivalsSampleOut[]>("/v1/arrivals/samples"),
      ]);
      setMarkets(marketsPayload.markets);
      setRuns(runsPayload);
      setSamples(samplesPayload);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(null);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  const filteredMarkets = useMemo(() => {
    return markets
      .filter((m) => {
        if (regionFilter !== "all" && m.region !== regionFilter) return false;
        const tasteScore = m.taste_score ?? 0;
        if (tasteScore < minTasteScore || tasteScore > maxTasteScore) return false;
        const arrivals = m.arrivals_share ?? 0;
        if (arrivals < minArrivals || arrivals > maxArrivals) return false;
        if (quadrantFilter !== "all" && m.quadrant !== quadrantFilter) return false;
        return true;
      })
      .sort((a, b) => {
        const aVal = a[sortBy] ?? 0;
        const bVal = b[sortBy] ?? 0;
        const dir = sortDir === "asc" ? 1 : -1;
        if (typeof aVal === "number" && typeof bVal === "number") {
          return (aVal - bVal) * dir;
        }
        return String(aVal).localeCompare(String(bVal)) * dir;
      });
  }, [markets, regionFilter, quadrantFilter, minTasteScore, maxTasteScore, minArrivals, maxArrivals, sortBy, sortDir]);

  const regions = useMemo(() => Array.from(new Set(markets.map((m) => m.region))).sort(), [markets]);

  const handleSort = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(field);
      setSortDir("desc");
    }
  };

  const exportCSV = () => {
    const headers = ["City", "Country", "Region", "Taste Score", "Lift", "Coverage", "Confidence", "Arrivals Share", "Gap", "Quadrant"];
    const rows = filteredMarkets.map((m) => [
      m.city,
      m.country_name,
      m.region,
      m.taste_score?.toFixed(1) ?? "—",
      m.lift?.toFixed(4) ?? "—",
      `${(m.coverage * 100).toFixed(1)}%`,
      m.confidence ?? "—",
      m.arrivals_share?.toFixed(1) ?? "—",
      m.gap?.toFixed(1) ?? "—",
      m.quadrant ?? "—",
    ]);
    const csv = [headers.join(","), ...rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tastebound-analytics-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <main className="page">
      <div className="stack" style={{ marginTop: 32 }}>
        <div className="stackSm">
          <span className="eyebrow">Analytics</span>
          <h1 className="heading">Market Analytics</h1>
        </div>
        <p className="serif">
          Explore taste scores, quadrants, and arrival gaps across origin markets.
          Filter, sort, and export to identify untapped opportunities.
        </p>
      </div>

      {error ? <div className="sectionSm"><Banner tone="error">Failed to load data</Banner></div> : null}

      <section className="section">
        <div className="card stackSm">
          <h3 className="headingSm">Filters</h3>
          <div className="grid4">
            <label className="field">
              <span className="label">Region</span>
              <select className="select" value={regionFilter} onChange={(e) => setRegionFilter(e.target.value)}>
                <option value="all">All regions</option>
                {regions.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </label>
            <label className="field">
              <span className="label">Quadrant</span>
              <select className="select" value={quadrantFilter} onChange={(e) => setQuadrantFilter(e.target.value)}>
                <option value="all">All quadrants</option>
                <option value="untapped">Untapped</option>
                <option value="core">Core</option>
                <option value="habit">Habit</option>
                <option value="low_priority">Low Priority</option>
              </select>
            </label>
            <label className="field">
              <span className="label">Taste Score Range</span>
              <div className="row" style={{ gap: 8 }}>
                <input type="number" className="input" min="0" max="100" value={minTasteScore} onChange={(e) => setMinTasteScore(Math.min(parseInt(e.target.value) || 0, maxTasteScore))} placeholder="Min" />
                <input type="number" className="input" min="0" max="100" value={maxTasteScore} onChange={(e) => setMaxTasteScore(Math.max(parseInt(e.target.value) || 100, minTasteScore))} placeholder="Max" />
              </div>
            </label>
            <label className="field">
              <span className="label">Arrivals Share Range</span>
              <div className="row" style={{ gap: 8 }}>
                <input type="number" className="input" min="0" max="100" value={minArrivals} onChange={(e) => setMinArrivals(Math.min(parseInt(e.target.value) || 0, maxArrivals))} placeholder="Min %" />
                <input type="number" className="input" min="0" max="100" value={maxArrivals} onChange={(e) => setMaxArrivals(Math.max(parseInt(e.target.value) || 100, minArrivals))} placeholder="Max %" />
              </div>
            </label>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="spread">
          <h2 className="headingSm">Markets ({filteredMarkets.length})</h2>
          <button type="button" className="btnPrimary" onClick={exportCSV} disabled={filteredMarkets.length === 0}>
            Export CSV
          </button>
        </div>

        <div className="card">
          <div style={{ overflowX: "auto" }}>
            <table className="table">
              <thead>
                <tr>
                  <th onClick={() => handleSort("city")} style={{ cursor: "pointer" }}>City <span className="caption">{sortBy === "city" ? (sortDir === "asc" ? "↑" : "↓") : ""}</span></th>
                  <th>Country</th>
                  <th>Region</th>
                  <th onClick={() => handleSort("taste_score")} style={{ cursor: "pointer" }}>Taste Score <span className="caption">{sortBy === "taste_score" ? (sortDir === "asc" ? "↑" : "↓") : ""}</span></th>
                  <th onClick={() => handleSort("lift")} style={{ cursor: "pointer" }}>Lift <span className="caption">{sortBy === "lift" ? (sortDir === "asc" ? "↑" : "↓") : ""}</span></th>
                  <th>Coverage</th>
                  <th>Confidence</th>
                  <th onClick={() => handleSort("arrivals_share")} style={{ cursor: "pointer" }}>Arrivals % <span className="caption">{sortBy === "arrivals_share" ? (sortDir === "asc" ? "↑" : "↓") : ""}</span></th>
                  <th onClick={() => handleSort("gap")} style={{ cursor: "pointer" }}>Gap <span className="caption">{sortBy === "gap" ? (sortDir === "asc" ? "↑" : "↓") : ""}</span></th>
                  <th>Quadrant</th>
                </tr>
              </thead>
              <tbody>
                {filteredMarkets.map((m) => (
                  <tr key={m.market_id}>
                    <td className="num">{m.city}</td>
                    <td>{m.country_name}</td>
                    <td>{m.region}</td>
                    <td className="num">{m.taste_score?.toFixed(1) ?? "—"}</td>
                    <td className="num">{m.lift?.toFixed(4) ?? "—"}</td>
                    <td className="num">{(m.coverage * 100).toFixed(1)}%</td>
                    <td>
                      <span className={`pill ${m.confidence === "high" ? "confHigh" : m.confidence === "medium" ? "confMedium" : "confLow"}`}>
                        {m.confidence ?? "—"}
                      </span>
                    </td>
                    <td className="num">{m.arrivals_share?.toFixed(1) ?? "—"}%</td>
                    <td className="num">{m.gap?.toFixed(1) ?? "—"}</td>
                    <td>
                      <span className={`pill ${m.quadrant === "untapped" ? "pillGood" : m.quadrant === "core" ? "pillWarn" : m.quadrant === "habit" ? "pillWarn" : "pillBad"}`}>
                        {m.quadrant ?? "—"}
                      </span>
                    </td>
                  </tr>
                ))}
                {filteredMarkets.length === 0 && (
                  <tr>
                    <td colSpan={11} style={{ textAlign: "center", padding: 32 }}>
                      <EmptyState title="No markets match filters" />
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="section grid2">
        <TasteScoreChart markets={filteredMarkets} title="Top Taste Scores" />
        <QuadrantScatterChart markets={filteredMarkets} title="Quadrant: Taste Score vs Arrivals Share" />
      </section>

      <section className="section">
        <h2 className="headingSm">Run Comparison</h2>
        <p className="muted">Recent runs for comparison (click to load into analytics)</p>
        <div className="card">
          {runs.length === 0 ? (
            <EmptyState title="No runs yet" />
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.run_id} style={{ cursor: "pointer" }}>
                    <td className="mono">{r.run_id.slice(0, 8)}…</td>
                    <td>
                      <span className={`pill ${r.status === "done" ? "pillGood" : r.status === "partial" ? "pillWarn" : r.status === "failed" ? "pillBad" : "pillSky"}`}>
                        {r.status}
                      </span>
                    </td>
                    <td>{new Date(r.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </main>
  );
}
