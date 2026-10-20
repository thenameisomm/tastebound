"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Banner } from "@/components/Banner";
import { TasteScoreChart } from "@/components/charts/TasteScoreChart";
import { QuadrantScatterChart } from "@/components/charts/QuadrantScatterChart";
import type { ArrivalsSampleOut, DemoResponse, MarketListResponse, MarketRow } from "@/lib/types";

export default function AnalyticsPage() {
  const [markets, setMarkets] = useState<MarketRow[]>([]);
  const [samples, setSamples] = useState<ArrivalsSampleOut[]>([]);
  const [demoDestination, setDemoDestination] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);

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
    setError(null);
    try {
      const [demoPayload, samplesPayload] = await Promise.all([
        api.get<DemoResponse>("/v1/demo"),
        api.get<ArrivalsSampleOut[]>("/v1/arrivals/samples"),
      ]);
      const marketPayload = await api.get<MarketListResponse>(
        `/v1/runs/${demoPayload.run_id}/markets`,
      );
      setMarkets(marketPayload.markets);
      setSamples(samplesPayload);
      setDemoDestination(demoPayload.destination);
    } catch (err) {
      setError(err);
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
  const untappedCount = filteredMarkets.filter((market) => market.quadrant === "untapped").length;
  const highConfidenceCount = filteredMarkets.filter((market) => market.confidence === "high").length;

  const handleSort = (field: typeof sortBy) => {
    if (sortBy === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(field);
      setSortDir("desc");
    }
  };

  const resetFilters = () => {
    setRegionFilter("all");
    setQuadrantFilter("all");
    setMinTasteScore(0);
    setMaxTasteScore(100);
    setMinArrivals(0);
    setMaxArrivals(100);
    setSortBy("taste_score");
    setSortDir("desc");
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
      <div className="pageHero">
        <div className="pageHeroMain">
          <span className="eyebrow">Analytics</span>
          <h1 className="heading">Market analytics</h1>
          <p className="pageLead">
            Explore taste fit, quadrants and arrival gaps across origin markets. Filter, sort and
            export to find the places where interest runs ahead of the crowd.
          </p>
          {demoDestination ? (
            <p className="pageMeta">
              <span>Sample run: {demoDestination}</span>
              <span>Arrivals attached</span>
              <span>Scores from Qloo</span>
            </p>
          ) : null}
        </div>
      </div>

      {error ? (
        <div className="sectionSm">
          <Banner tone="error">Failed to load data</Banner>
        </div>
      ) : null}

      <div className="statGrid sectionSm">
        <div className="stat">
          <span className="statLabel">In view</span>
          <span className="statValue">{filteredMarkets.length}</span>
          <span className="statNote">of {markets.length} scored markets</span>
        </div>
        <div className="stat">
          <span className="statLabel">Untapped</span>
          <span className="statValue">{untappedCount}</span>
          <span className="statNote">taste ahead of arrivals</span>
        </div>
        <div className="stat">
          <span className="statLabel">High confidence</span>
          <span className="statValue">{highConfidenceCount}</span>
          <span className="statNote">Qloo confidence high</span>
        </div>
        <div className="stat statDark">
          <span className="statLabel">Arrivals</span>
          <span className="statValue">{samples.length}</span>
          <span className="statNote">samples loaded</span>
        </div>
      </div>

      <section className="section">
        <div className="filterPanel stack">
          <div className="spread">
            <div className="stackSm">
              <span className="kindTag">Filters</span>
              <h2 className="headingSm">Narrow the market set</h2>
            </div>
            <button type="button" className="btnGhost btnSmall" onClick={resetFilters}>
              Reset
            </button>
          </div>
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
              <span className="label">Taste score range</span>
              <div className="row" style={{ gap: 8 }}>
                <input type="number" className="input" min="0" max="100" value={minTasteScore} onChange={(e) => setMinTasteScore(Math.min(parseInt(e.target.value) || 0, maxTasteScore))} placeholder="Min" aria-label="Minimum taste score" />
                <input type="number" className="input" min="0" max="100" value={maxTasteScore} onChange={(e) => setMaxTasteScore(Math.max(parseInt(e.target.value) || 100, minTasteScore))} placeholder="Max" aria-label="Maximum taste score" />
              </div>
            </label>
            <label className="field">
              <span className="label">Arrivals share range</span>
              <div className="row" style={{ gap: 8 }}>
                <input type="number" className="input" min="0" max="100" value={minArrivals} onChange={(e) => setMinArrivals(Math.min(parseInt(e.target.value) || 0, maxArrivals))} placeholder="Min %" aria-label="Minimum arrivals share" />
                <input type="number" className="input" min="0" max="100" value={maxArrivals} onChange={(e) => setMaxArrivals(Math.max(parseInt(e.target.value) || 100, minArrivals))} placeholder="Max %" aria-label="Maximum arrivals share" />
              </div>
            </label>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="sectionHeader">
          <div className="stackSm">
            <span className="kindTag">Market table</span>
            <h2 className="headingSm">Markets ({filteredMarkets.length})</h2>
          </div>
          <div className="row" style={{ gap: 12 }}>
            <span className="caption">
              Sorted by {sortBy.replace(/_/g, " ")} · {sortDir === "asc" ? "ascending" : "descending"}
            </span>
            <button type="button" className="btnPrimary" onClick={exportCSV} disabled={filteredMarkets.length === 0}>
              Export CSV
            </button>
          </div>
        </div>

        <div className="tableCard">
          <div style={{ overflowX: "auto" }}>
            <table className="table">
              <thead>
                <tr>
                  <th scope="col" aria-sort={sortBy === "city" ? (sortDir === "asc" ? "ascending" : "descending") : "none"}>
                    <button type="button" className="sortButton" onClick={() => handleSort("city")}>
                      City <span aria-hidden="true">{sortBy === "city" ? (sortDir === "asc" ? "↑" : "↓") : ""}</span>
                    </button>
                  </th>
                  <th scope="col">Country</th>
                  <th scope="col">Region</th>
                  <th scope="col" aria-sort={sortBy === "taste_score" ? (sortDir === "asc" ? "ascending" : "descending") : "none"}>
                    <button type="button" className="sortButton" onClick={() => handleSort("taste_score")}>
                      Taste score <span aria-hidden="true">{sortBy === "taste_score" ? (sortDir === "asc" ? "↑" : "↓") : ""}</span>
                    </button>
                  </th>
                  <th scope="col" aria-sort={sortBy === "lift" ? (sortDir === "asc" ? "ascending" : "descending") : "none"}>
                    <button type="button" className="sortButton" onClick={() => handleSort("lift")}>
                      Lift <span aria-hidden="true">{sortBy === "lift" ? (sortDir === "asc" ? "↑" : "↓") : ""}</span>
                    </button>
                  </th>
                  <th scope="col">Coverage</th>
                  <th scope="col">Confidence</th>
                  <th scope="col" aria-sort={sortBy === "arrivals_share" ? (sortDir === "asc" ? "ascending" : "descending") : "none"}>
                    <button type="button" className="sortButton" onClick={() => handleSort("arrivals_share")}>
                      Arrivals % <span aria-hidden="true">{sortBy === "arrivals_share" ? (sortDir === "asc" ? "↑" : "↓") : ""}</span>
                    </button>
                  </th>
                  <th scope="col" aria-sort={sortBy === "gap" ? (sortDir === "asc" ? "ascending" : "descending") : "none"}>
                    <button type="button" className="sortButton" onClick={() => handleSort("gap")}>
                      Gap <span aria-hidden="true">{sortBy === "gap" ? (sortDir === "asc" ? "↑" : "↓") : ""}</span>
                    </button>
                  </th>
                  <th scope="col">Quadrant</th>
                </tr>
              </thead>
              <tbody>
                {filteredMarkets.map((m) => (
                  <tr key={m.market_id}>
                    <td><span className="tableCity">{m.city}</span></td>
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
                    <td colSpan={10} className="tableEmpty">
                      No markets match these filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="section grid2">
        <TasteScoreChart markets={filteredMarkets} title="Top taste scores" />
        <QuadrantScatterChart markets={filteredMarkets} title="Taste fit vs arrivals" />
      </section>
    </main>
  );
}
