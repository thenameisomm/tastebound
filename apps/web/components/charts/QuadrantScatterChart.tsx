"use client";

import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Label } from "recharts";
import type { MarketRow } from "@/lib/types";

const QUADRANT_COLORS = {
  untapped: "#097fe8",
  core: "#f64932",
  habit: "#ffb110",
  low_priority: "#62aef0",
  unknown: "#979797",
} as const;

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number; name: string; payload: { city: string; country: string; quadrant: string; arrivalsShare: number } }>; label?: string }) => {
  if (active && payload && payload.length > 0) {
    const item = payload[0];
    const city = item?.payload?.city ?? label ?? "";
    const country = item?.payload?.country ?? "";
    const quadrant = item?.payload?.quadrant ?? "";
    const arrivals = item?.payload?.arrivalsShare ?? 0;
    return (
      <div className="card" style={{ padding: "8px 12px", fontSize: 12 }}>
        <p>{city}, {country}</p>
        <p>Quadrant: {quadrant}</p>
        <p>Arrivals Share: {arrivals.toFixed(1)}%</p>
      </div>
    );
  }
  return null;
};

interface QuadrantScatterChartProps {
  markets: MarketRow[];
  title?: string;
}

export function QuadrantScatterChart({ markets, title = "Quadrant: Taste Score vs Arrivals Share" }: QuadrantScatterChartProps) {
  const data = markets
    .filter((m) => m.taste_score !== null && m.arrivals_share !== null)
    .map((m) => ({
      city: m.city,
      tasteScore: m.taste_score || 0,
      arrivalsShare: m.arrivals_share || 0,
      quadrant: m.quadrant || "unknown",
      country: m.country_name,
    }));

  if (data.length === 0) {
    return (
      <div className="card" style={{ minHeight: 300 }}>
        <p className="muted" style={{ textAlign: "center", padding: 48 }}>
          No data available for quadrant analysis
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 className="headingSm" style={{ marginBottom: 16 }}>{title}</h3>
      <div style={{ height: 350 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart data={data}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis
              type="number"
              dataKey="tasteScore"
              domain={[0, 100]}
              name="Taste Score (percentile)"
              tick={{ fontSize: 11 }}
              label={{ value: "Taste Score (percentile)", position: "bottom", offset: 20 }}
            />
            <YAxis
              type="number"
              dataKey="arrivalsShare"
              domain={[0, 100]}
              name="Arrivals Share (%)"
              tick={{ fontSize: 11 }}
              label={{ value: "Arrivals Share (%)", position: "left", offset: -40 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Scatter name="Markets" data={data}>
              {data.map((entry, index) => (
                <Cell key={`scatter-${index}`} fill={QUADRANT_COLORS[entry.quadrant as keyof typeof QUADRANT_COLORS]} stroke="transparent" />
              ))}
            </Scatter>
            <Label
              value="Untapped: High Taste, Low Arrivals"
              position={{ x: 75, y: 25 }}
              fill="#097fe8"
              fontSize={11}
              fontWeight={600}
            />
            <Label
              value="Core: High Taste, High Arrivals"
              position={{ x: 75, y: 85 }}
              fill="#f64932"
              fontSize={11}
              fontWeight={600}
            />
            <Label
              value="Habit: Low Taste, High Arrivals"
              position={{ x: 25, y: 85 }}
              fill="#ffb110"
              fontSize={11}
              fontWeight={600}
            />
            <Label
              value="Low Priority: Low Taste, Low Arrivals"
              position={{ x: 25, y: 25 }}
              fill="#62aef0"
              fontSize={11}
              fontWeight={600}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <div className="row" style={{ gap: 16, marginTop: 12, flexWrap: "wrap" }}>
        {(Object.keys(QUADRANT_COLORS) as Array<keyof typeof QUADRANT_COLORS>).map((quadrant) => (
          <span key={quadrant} className="pill" style={{ background: QUADRANT_COLORS[quadrant], color: quadrant === "habit" ? "#000" : "#fff" }}>
            {quadrant}
          </span>
        ))}
      </div>
    </div>
  );
}
