"use client";

import { QUADRANT_HELP, QUADRANT_LABELS, formatScore, formatShare } from "@/lib/format";
import type { MarketRow, Quadrant } from "@/lib/types";

const WIDTH = 720;
const HEIGHT = 520;
const PAD = 56;

const QUADRANT_FILL: Record<Quadrant, string> = {
  untapped: "rgba(209, 255, 202, 0.55)",
  core: "rgba(255, 241, 0, 0.16)",
  habit: "rgba(199, 199, 199, 0.3)",
  low_priority: "rgba(0, 0, 0, 0.03)",
};

const QUADRANT_TEXT: Record<Quadrant, string> = {
  untapped: "#1a1a1a",
  core: "#1a1a1a",
  habit: "#1a1a1a",
  low_priority: "#5f5f5f",
};

export function GapQuadrant({
  markets,
  thresholds,
  runId,
}: {
  markets: MarketRow[];
  thresholds: Record<string, number>;
  runId: string;
}) {
  const points = markets.filter(
    (market) => market.taste_score !== null && market.arrivals_pct !== null,
  );
  if (points.length === 0) {
    return <p className="muted">No arrivals data yet — upload arrivals to see the gap view.</p>;
  }
  const tasteThreshold = (thresholds.gap_taste ?? 0.5) * 100;
  const arrivalsThreshold = thresholds.gap_arrivals ?? 0.5;

  const x = (arrivalsPct: number) => PAD + arrivalsPct * (WIDTH - PAD * 2);
  const y = (tasteScore: number) => HEIGHT - PAD - (tasteScore / 100) * (HEIGHT - PAD * 2);

  const midX = x(arrivalsThreshold);
  const midY = y(tasteThreshold);
  const placedLabels: Array<[number, number, number, number]> = [];

  return (
    <div className="quadrantWrap">
      <svg
        className="quadrant"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        aria-label={`Gap quadrant with ${points.length} markets. Untapped markets are top-left. The market table below lists every market with its quadrant.`}
      >
        <rect x={PAD} y={PAD} width={midX - PAD} height={midY - PAD} fill={QUADRANT_FILL.untapped} />
        <rect x={midX} y={PAD} width={WIDTH - PAD - midX} height={midY - PAD} fill={QUADRANT_FILL.core} />
        <rect x={PAD} y={midY} width={midX - PAD} height={HEIGHT - PAD - midY} fill={QUADRANT_FILL.low_priority} />
        <rect x={midX} y={midY} width={WIDTH - PAD - midX} height={HEIGHT - PAD - midY} fill={QUADRANT_FILL.habit} />

        <text className="quadrantZoneLabel" x={PAD + 12} y={PAD + 24} fill={QUADRANT_TEXT.untapped} paintOrder="stroke" stroke="rgba(246,245,244,0.9)" strokeWidth={4}>
          {QUADRANT_LABELS.untapped.toUpperCase()}
        </text>
        <text className="quadrantZoneLabel" x={WIDTH - PAD - 12} y={PAD + 24} fill={QUADRANT_TEXT.core} textAnchor="end" paintOrder="stroke" stroke="rgba(246,245,244,0.9)" strokeWidth={4}>
          {QUADRANT_LABELS.core.toUpperCase()}
        </text>
        <text className="quadrantZoneLabel" x={PAD + 12} y={HEIGHT - PAD - 12} fill={QUADRANT_TEXT.low_priority} paintOrder="stroke" stroke="rgba(246,245,244,0.9)" strokeWidth={4}>
          {QUADRANT_LABELS.low_priority.toUpperCase()}
        </text>
        <text className="quadrantZoneLabel" x={WIDTH - PAD - 12} y={HEIGHT - PAD - 12} fill={QUADRANT_TEXT.habit} textAnchor="end" paintOrder="stroke" stroke="rgba(246,245,244,0.9)" strokeWidth={4}>
          {QUADRANT_LABELS.habit.toUpperCase()}
        </text>

        <line x1={PAD} y1={HEIGHT - PAD} x2={WIDTH - PAD} y2={HEIGHT - PAD} stroke="rgba(0,0,0,0.2)" />
        <line x1={PAD} y1={PAD} x2={PAD} y2={HEIGHT - PAD} stroke="rgba(0,0,0,0.2)" />
        <line x1={midX} y1={PAD} x2={midX} y2={HEIGHT - PAD} stroke="rgba(0,0,0,0.12)" strokeDasharray="4 4" />
        <line x1={PAD} y1={midY} x2={WIDTH - PAD} y2={midY} stroke="rgba(0,0,0,0.12)" strokeDasharray="4 4" />

        <text className="quadrantAxisLabel" x={WIDTH / 2} y={HEIGHT - 16} fill="#5f5f5f" textAnchor="middle">
          Arrivals share percentile → more arrivals today
        </text>
        <text
          className="quadrantAxisLabel"
          x={16}
          y={HEIGHT / 2}
          fill="#5f5f5f"
          textAnchor="middle"
          transform={`rotate(-90 16 ${HEIGHT / 2})`}
        >
          Taste score percentile → stronger taste fit
        </text>

        {points.map((market) => {
          const pointX = x(market.arrivals_pct ?? 0);
          const pointY = y(market.taste_score ?? 0);
          const label = `${market.city}: taste ${formatScore(market.taste_score)}, arrivals ${formatShare(market.arrivals_pct)}, ${market.quadrant ? QUADRANT_LABELS[market.quadrant] : ""}`;
          const showLabel = (market.rank ?? 999) <= 12;
          let labelX = pointX + 10;
          const labelWidth = market.city.length * 6.2;
          if (labelX + labelWidth > WIDTH - PAD - 8) {
            labelX = pointX - 10 - labelWidth;
          }
          const labelY = pointY + 3.5;
          const labelBox: [number, number, number, number] = [
            labelX - 2,
            labelY - 10,
            labelX + labelWidth + 2,
            labelY + 5,
          ];
          const collides = placedLabels.some(
            ([left, top, right, bottom]) =>
              labelBox[0] < right &&
              labelBox[2] > left &&
              labelBox[1] < bottom &&
              labelBox[3] > top,
          );
          const drawLabel = showLabel && !collides;
          if (drawLabel) placedLabels.push(labelBox);
          return (
            <a
              key={market.market_id}
              href={`/runs/${runId}/markets/${market.market_id}`}
              aria-label={label}
            >
              <title>{`${label}${market.quadrant ? ` — ${QUADRANT_HELP[market.quadrant]}` : ""}`}</title>
              <circle
                className="quadrantPoint"
                cx={pointX}
                cy={pointY}
                r={market.confidence === "high" ? 7 : market.confidence === "medium" ? 6 : 5}
                fill={market.quadrant === "untapped" ? "#d1ffca" : "#1a1a1a"}
                opacity={market.confidence === "low" ? 0.55 : 1}
              />
              {drawLabel ? (
                <text className="quadrantPointLabel" x={labelX} y={labelY} fill="#1a1a1a">
                  {market.city}
                </text>
              ) : null}
            </a>
          );
        })}
      </svg>
    </div>
  );
}
