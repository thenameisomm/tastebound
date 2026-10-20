"use client";

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceArea,
  ReferenceLine,
} from "recharts";
import type { MarketRow } from "@/lib/types";

const QUADRANT_COLORS: Record<string, string> = {
  untapped: "#d1ffca",
  core: "#fff100",
  habit: "#c7c7c7",
  low_priority: "#e9e9e9",
  unknown: "#bdbdbd",
};

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{
    payload: { city: string; country: string; quadrant: string; arrivalsShare: number; tasteScore: number };
  }>;
}) => {
  if (!active || !payload || payload.length === 0) return null;
  const item = payload[0]?.payload;
  if (!item) return null;
  return (
    <div className="chartTooltip">
      <span className="chartTooltipLabel">
        {item.city}, {item.country}
      </span>
      <span className="chartTooltipValue">
        Taste {item.tasteScore.toFixed(1)} · arrivals {item.arrivalsShare.toFixed(1)}%
      </span>
      <span className="chartTooltipMeta">{item.quadrant.replace("_", " ")}</span>
    </div>
  );
};

interface QuadrantScatterChartProps {
  markets: MarketRow[];
  title?: string;
}

export function QuadrantScatterChart({ markets, title = "Taste fit vs arrivals" }: QuadrantScatterChartProps) {
  const data = markets
    .filter((market) => market.taste_score !== null && market.arrivals_share !== null)
    .map((market) => ({
      city: market.city,
      tasteScore: market.taste_score || 0,
      arrivalsShare: market.arrivals_share || 0,
      quadrant: market.quadrant || "unknown",
      country: market.country_name,
    }));

  if (data.length === 0) {
    return (
      <div className="chartCard" style={{ minHeight: 320 }}>
        <p className="muted" style={{ textAlign: "center", padding: 48 }}>
          No data available for quadrant analysis
        </p>
      </div>
    );
  }

  return (
    <div className="chartCard">
      <div className="stackSm">
        <span className="kindTag">Quadrants</span>
        <h3 className="headingSm">{title}</h3>
        <span className="caption">X: taste score percentile · Y: arrivals share</span>
      </div>
      <div style={{ height: 340 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart data={data} margin={{ top: 12, right: 20, bottom: 12, left: 4 }}>
            <CartesianGrid stroke="#eeeeee" />
            <ReferenceArea
              x1={50}
              x2={100}
              y1={0}
              y2={50}
              fill="#d1ffca"
              fillOpacity={0.35}
              label={{ value: "UNTAPPED", position: "insideTopRight", fill: "#1a1a1a", fontSize: 9 }}
            />
            <ReferenceArea
              x1={50}
              x2={100}
              y1={50}
              y2={100}
              fill="#fff100"
              fillOpacity={0.22}
              label={{ value: "CORE", position: "insideTopRight", fill: "#1a1a1a", fontSize: 9 }}
            />
            <ReferenceArea
              x1={0}
              x2={50}
              y1={50}
              y2={100}
              fill="#c7c7c7"
              fillOpacity={0.24}
              label={{ value: "HABIT", position: "insideTopLeft", fill: "#1a1a1a", fontSize: 9 }}
            />
            <ReferenceArea
              x1={0}
              x2={50}
              y1={0}
              y2={50}
              fill="#e9e9e9"
              fillOpacity={0.4}
              label={{ value: "LOW PRIORITY", position: "insideBottomLeft", fill: "#5f5f5f", fontSize: 9 }}
            />
            <ReferenceLine x={50} stroke="#1a1a1a" strokeDasharray="2 4" strokeOpacity={0.35} />
            <ReferenceLine y={50} stroke="#1a1a1a" strokeDasharray="2 4" strokeOpacity={0.35} />
            <XAxis
              type="number"
              dataKey="tasteScore"
              domain={[0, 100]}
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 10 }}
            />
            <YAxis
              type="number"
              dataKey="arrivalsShare"
              domain={[0, 100]}
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 10 }}
              width={40}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: "2 4" }} />
            <Scatter name="Markets" data={data}>
              {data.map((entry, index) => (
                <Cell
                  key={`scatter-${index}`}
                  fill={QUADRANT_COLORS[entry.quadrant] ?? QUADRANT_COLORS.unknown}
                  stroke="#1a1a1a"
                  strokeWidth={0.75}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <div className="chartLegend">
        {Object.entries(QUADRANT_COLORS).map(([quadrant, color]) => (
          <span key={quadrant} className="legendItem">
            <span className="legendSwatch" style={{ background: color }} />
            {quadrant.replace("_", " ")}
          </span>
        ))}
      </div>
    </div>
  );
}
