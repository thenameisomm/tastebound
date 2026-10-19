"use client";

import { useMemo, useState } from "react";
import { formatDate } from "@/lib/format";
import type { TraceItem } from "@/lib/types";

const KIND_LABELS: Record<string, string> = {
  qloo: "Qloo",
  llm: "LLM",
  tool: "Tool",
  event: "Event",
};

const KIND_CLASS: Record<string, string> = {
  qloo: "pill pillSky",
  llm: "pill pillWarm",
  tool: "pill pillGood",
  event: "pill",
};

export function TraceTable({ items }: { items: TraceItem[] }) {
  const [kind, setKind] = useState("all");
  const [query, setQuery] = useState("");

  const visible = useMemo(
    () =>
      items.filter((item) => {
        if (kind !== "all" && item.kind !== kind) return false;
        if (query && !`${item.step} ${item.summary}`.toLowerCase().includes(query.toLowerCase()))
          return false;
        return true;
      }),
    [items, kind, query],
  );

  return (
    <div className="stack">
      <div className="row">
        <label className="field" style={{ minWidth: 140 }}>
          <span className="caption">Kind</span>
          <select className="select" value={kind} onChange={(event) => setKind(event.target.value)}>
            <option value="all">All</option>
            <option value="qloo">Qloo calls</option>
            <option value="llm">LLM calls</option>
            <option value="tool">Tool calls</option>
            <option value="event">Events</option>
          </select>
        </label>
        <label className="field" style={{ flex: 1, minWidth: 200 }}>
          <span className="caption">Search</span>
          <input
            className="input"
            type="search"
            placeholder="Step or summary"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
      </div>

      {visible.length === 0 ? (
        <div className="empty">Nothing matches these filters.</div>
      ) : (
        <div className="stackSm">
          {visible.map((item, index) => (
            <details key={`${item.at}-${index}`} className="card cardTight">
              <summary style={{ cursor: "pointer", listStyle: "none" }}>
                <span className="row" style={{ gap: 8 }}>
                  <span className={KIND_CLASS[item.kind] ?? "pill"}>{KIND_LABELS[item.kind] ?? item.kind}</span>
                  <strong style={{ fontSize: 14 }}>{item.step}</strong>
                  <span className="muted" style={{ flex: 1, fontSize: 14 }}>
                    {item.summary}
                  </span>
                  <span className="caption">{formatDate(item.at)}</span>
                </span>
              </summary>
              <pre
                className="mono"
                style={{
                  marginTop: 12,
                  padding: 12,
                  background: "rgba(0,0,0,0.03)",
                  borderRadius: 8,
                  overflowX: "auto",
                }}
              >
                {JSON.stringify(item.detail, null, 2)}
              </pre>
            </details>
          ))}
        </div>
      )}
    </div>
  );
}
