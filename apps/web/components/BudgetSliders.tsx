"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { formatCurrency, formatShare } from "@/lib/format";
import { ErrorPanel } from "./ErrorPanel";
import type { AllocationResponse, MarketRow } from "@/lib/types";

export function BudgetSliders({ runId, markets }: { runId: string; markets: MarketRow[] }) {
  const eligible = useMemo(
    () => markets.filter((market) => market.taste_score !== null).sort((a, b) => (a.rank ?? 999) - (b.rank ?? 999)),
    [markets],
  );
  const [total, setTotal] = useState(250000);
  const [currency, setCurrency] = useState("EUR");
  const [mode, setMode] = useState<"grow_untapped" | "defend_core">("grow_untapped");
  const [locks, setLocks] = useState<Record<string, number>>({});
  const [allocation, setAllocation] = useState<AllocationResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const compute = async (nextLocks: Record<string, number>, nextTotal = total, nextMode = mode, nextCurrency = currency) => {
    setBusy(true);
    setError(null);
    try {
      const result = await api.post<AllocationResponse>(`/v1/runs/${runId}/allocation`, {
        total: nextTotal,
        currency: nextCurrency,
        mode: nextMode,
        locks: nextLocks,
      });
      setAllocation(result);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    void compute({});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId]);

  const shareByMarket = useMemo(() => {
    const map = new Map<string, number>();
    allocation?.shares.forEach((share) => map.set(share.market_id, share.share));
    return map;
  }, [allocation]);

  const amountByMarket = useMemo(() => {
    const map = new Map<string, number>();
    allocation?.shares.forEach((share) => map.set(share.market_id, share.amount));
    return map;
  }, [allocation]);

  const toggleLock = (market: MarketRow) => {
    const next = { ...locks };
    if (next[market.market_id] !== undefined) {
      delete next[market.market_id];
    } else {
      const share = shareByMarket.get(market.market_id) ?? 0;
      next[market.market_id] = Math.round(total * share);
    }
    setLocks(next);
    void compute(next);
  };

  return (
    <div className="stack">
      <div className="row">
        <label className="field" style={{ minWidth: 160 }}>
          <span className="caption">Total budget</span>
          <input
            className="input"
            type="number"
            min={1000}
            step={1000}
            value={total}
            onChange={(event) => setTotal(Number(event.target.value))}
          />
        </label>
        <label className="field" style={{ minWidth: 100 }}>
          <span className="caption">Currency</span>
          <select className="select" value={currency} onChange={(event) => setCurrency(event.target.value)}>
            {["EUR", "USD", "GBP"].map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="field" style={{ minWidth: 190 }}>
          <span className="caption">Mode</span>
          <select
            className="select"
            value={mode}
            onChange={(event) => setMode(event.target.value as "grow_untapped" | "defend_core")}
          >
            <option value="grow_untapped">Grow untapped</option>
            <option value="defend_core">Defend core</option>
          </select>
        </label>
        <button
          type="button"
          className="btnPrimary"
          style={{ alignSelf: "flex-end" }}
          disabled={busy}
          onClick={() => void compute(locks)}
        >
          {busy ? "Splitting…" : "Split budget"}
        </button>
      </div>

      {error ? <ErrorPanel error={error} onRetry={() => void compute(locks)} /> : null}

      {allocation ? (
        <div className="stackSm">
          <p className="caption">
            {mode === "grow_untapped"
              ? "Weighted by taste score, confidence and untapped gap."
              : "Weighted by taste score, confidence and today's arrivals."}{" "}
            Locks pin a market's amount before the rest is split.
          </p>
          <ul className="stackSm" style={{ listStyle: "none" }}>
            {allocation.shares.map((share) => {
              const market = eligible.find((item) => item.market_id === share.market_id);
              const locked = locks[share.market_id] !== undefined;
              return (
                <li key={share.market_id} className="row" style={{ gap: 12 }}>
                  <button
                    type="button"
                    className={locked ? "btnGhost btnSmall" : "btnOutline btnSmall"}
                    onClick={() => market && toggleLock(market)}
                    aria-pressed={locked}
                    title={locked ? "Unlock this market" : "Lock this market's current amount"}
                  >
                    {locked ? "Locked" : "Lock"}
                  </button>
                  <span style={{ flex: 1 }}>{share.city}</span>
                  <span className="num caption">{formatShare(share.share)}</span>
                  <span className="num" style={{ minWidth: 110, textAlign: "right" }}>
                    {formatCurrency(amountByMarket.get(share.market_id) ?? 0, allocation.currency)}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
