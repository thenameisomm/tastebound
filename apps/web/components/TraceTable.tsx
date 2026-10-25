"use client";

import { useEffect, useMemo, useState } from "react";
import { formatDate } from "@/lib/format";
import type { TraceItem } from "@/lib/types";

const KIND_LABELS: Record<string, string> = {
  qloo: "Qloo",
  llm: "LLM",
  tool: "Tool",
  event: "Event",
};

const KIND_CLASS: Record<string, string> = {
  qloo: "pill pillGood",
  llm: "pill pillWarm",
  tool: "pill",
  event: "pill pillMuted",
};

export function TraceTable({
  items,
  highlightCallId,
}: {
  items: TraceItem[];
  highlightCallId?: string | null;
}) {
  const [kind, setKind] = useState("all");
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (!highlightCallId) return;
    const row = document.getElementById(`call-${highlightCallId}`);
    row?.scrollIntoView({ block: "center" });
  }, [highlightCallId, items.length]);

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
      <div className="traceFilters">
        <label className="field">
          <span className="label">Kind</span>
          <select className="select" value={kind} onChange={(event) => setKind(event.target.value)}>
            <option value="all">All</option>
            <option value="qloo">Qloo calls</option>
            <option value="llm">LLM calls</option>
            <option value="tool">Tool calls</option>
            <option value="event">Events</option>
          </select>
        </label>
        <label className="field fieldGrow">
          <span className="label">Search</span>
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
          {visible.map((item, index) => {
            const callId =
              typeof item.detail.call_id === "string" ? item.detail.call_id : null;
            const highlighted = Boolean(callId && callId === highlightCallId);
            return (
              <details
                key={`${item.at}-${index}`}
                id={callId ? `call-${callId}` : undefined}
                className={highlighted ? "traceCard traceCardHighlight" : "traceCard"}
                open={highlighted || undefined}
              >
                <summary>
                  <span className={KIND_CLASS[item.kind] ?? "pill"}>
                    {KIND_LABELS[item.kind] ?? item.kind}
                  </span>
                  <strong className="traceStep">{item.step}</strong>
                  <span className="traceSummary">{item.summary}</span>
                  <span className="caption traceTime">{formatDate(item.at)}</span>
                </summary>
                <pre>{JSON.stringify(item.detail, null, 2)}</pre>
              </details>
            );
          })}
        </div>
      )}
    </div>
  );
}
