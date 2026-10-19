"use client";

import { useRouter } from "next/navigation";
import { QUADRANT_HELP, QUADRANT_LABELS, formatScore, formatShare } from "@/lib/format";
import type { MarketRow, Quadrant } from "@/lib/types";

const WIDTH = 720;
const HEIGHT = 520;
const PAD = 56;

const QUADRANT_FILL: Record<Quadrant, string> = {
  untapped: "rgba(217, 242, 227, 0.55)",
  core: "rgba(230, 243, 254, 0.65)",
  habit: "rgba(255, 233, 199, 0.5)",
  low_priority: "rgba(0, 0, 0, 0.03)",
};

const QUADRANT_TEXT: Record<Quadrant, string> = {
  untapped: "#116b3a",
  core: "#0a4d8c",
  habit: "#8a5300",
  low_priority: "rgba(0, 0, 0, 0.45)",
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
  const router = useRouter();
  const points = markets.filter(
    (market) => market.taste_score !== null && market.arrivals_pct !== null,
  );
  if (points.length === 0) {
    return <p className="muted">No arrivals data yet — upload arrivals to see the gap view.</p>;
  }
  const tasteThreshold = (thresholds.gap_taste ?? 0.5) * 100;
  const arrivalsThreshold = (thresholds.gap_arrivals ?? 0.5) * 100;

  const x = (arrivalsPct: number) => PAD + (arrivalsPct / 100) * (WIDTH - PAD * 2);
  const y = (tasteScore: number) => HEIGHT - PAD - (tasteScore / 100) * (HEIGHT - PAD * 2);

  const midX = x(arrivalsThreshold);
  const midY = y(tasteThreshold);

  return (
    <div className="quadrantWrap">
      <svg
        className="quadrant"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label={`Gap quadrant with ${points.length} markets. Untapped markets are top-left. The market table below lists every market with its quadrant.`}
      >
        <rect x={PAD} y={PAD} width={midX - PAD} height={midY - PAD} fill={QUADRANT_FILL.untapped} />
        <rect x={midX} y={PAD} width={WIDTH - PAD - midX} height={midY - PAD} fill={QUADRANT_FILL.core} />
        <rect x={PAD} y={midY} width={midX - PAD} height={HEIGHT - PAD - midY} fill={QUADRANT_FILL.low_priority} />
        <rect x={midX} y={midY} width={WIDTH - PAD - midX} height={HEIGHT - PAD - midY} fill={QUADRANT_FILL.habit} />

        <text x={PAD + 12} y={PAD + 24} fill={QUADRANT_TEXT.untapped} fontSize={15} fontWeight={600}>
          {QUADRANT_LABELS.untapped}
        </text>
        <text x={WIDTH - PAD - 12} y={PAD + 24} fill={QUADRANT_TEXT.core} fontSize={15} fontWeight={600} textAnchor="end">
          {QUADRANT_LABELS.core}
        </text>
        <text x={PAD + 12} y={HEIGHT - PAD - 12} fill={QUADRANT_TEXT.low_priority} fontSize={15} fontWeight={600}>
          {QUADRANT_LABELS.low_priority}
        </text>
        <text x={WIDTH - PAD - 12} y={HEIGHT - PAD - 12} fill={QUADRANT_TEXT.habit} fontSize={15} fontWeight={600} textAnchor="end">
          {QUADRANT_LABELS.habit}
        </text>

        <line x1={PAD} y1={HEIGHT - PAD} x2={WIDTH - PAD} y2={HEIGHT - PAD} stroke="rgba(0,0,0,0.2)" />
        <line x1={PAD} y1={PAD} x2={PAD} y2={HEIGHT - PAD} stroke="rgba(0,0,0,0.2)" />
        <line x1={midX} y1={PAD} x2={midX} y2={HEIGHT - PAD} stroke="rgba(0,0,0,0.12)" strokeDasharray="4 4" />
        <line x1={PAD} y1={midY} x2={WIDTH - PAD} y2={midY} stroke="rgba(0,0,0,0.12)" strokeDasharray="4 4" />

        <text x={WIDTH / 2} y={HEIGHT - 16} fontSize={13} fill="rgba(0,0,0,0.55)" textAnchor="middle">
          Arrivals share percentile → more arrivals today
        </text>
        <text
          x={16}
          y={HEIGHT / 2}
          fontSize={13}
          fill="rgba(0,0,0,0.55)"
          textAnchor="middle"
          transform={`rotate(-90 16 ${HEIGHT / 2})`}
        >
          Taste score percentile → stronger taste fit
        </text>

        {points.map((market) => {
          const pointX = x(market.arrivals_pct ?? 0);
          const pointY = y(market.taste_score ?? 0);
          const label = `${market.city}: taste ${formatScore(market.taste_score)}, arrivals ${formatShare(market.arrivals_pct)}, ${market.quadrant ? QUADRANT_LABELS[market.quadrant] : ""}`;
          return (
            <g
              key={market.market_id}
              className="quadrantPoint"
              role="link"
              tabIndex={0}
              aria-label={label}
              onClick={() => router.push(`/runs/${runId}/markets/${market.market_id}`)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  router.push(`/runs/${runId}/markets/${market.market_id}`);
                }
              }}
            >
              <title>{`${label}${market.quadrant ? ` — ${QUADRANT_HELP[market.quadrant]}` : ""}`}</title>
              <circle
                cx={pointX}
                cy={pointY}
                r={market.confidence === "high" ? 7 : market.confidence === "medium" ? 6 : 5}
                fill={market.quadrant === "untapped" ? "#097fe8" : "#615d59"}
                opacity={market.confidence === "low" ? 0.55 : 0.9}
              />
              <text x={pointX + 10} y={pointY + 4} fontSize={12} fill="rgba(0,0,0,0.75)">
                {market.city}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
