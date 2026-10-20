"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { MarketRow } from "@/lib/types";

interface TasteScoreChartProps {
  markets: MarketRow[];
  title?: string;
}

export const QUADRANT_COLORS: Record<string, string> = {
  untapped: "#d1ffca",
  core: "#fff100",
  habit: "#c7c7c7",
  low_priority: "#e9e9e9",
  unknown: "#bdbdbd",
};

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number; payload: { city: string } }>;
  label?: string;
}) => {
  if (!active || !payload || payload.length === 0) return null;
  const item = payload[0];
  const city = label ?? item?.payload?.city ?? "";
  const value = item?.value ?? 0;
  return (
    <div className="chartTooltip">
      <span className="chartTooltipLabel">{city}</span>
      <span className="chartTooltipValue">{value.toFixed(1)} taste score</span>
    </div>
  );
};

export function TasteScoreChart({ markets, title = "Top taste scores" }: TasteScoreChartProps) {
  const data = markets
    .filter((market) => market.taste_score !== null)
    .sort((a, b) => (b.taste_score || 0) - (a.taste_score || 0))
    .slice(0, 20)
    .map((market) => ({
      city: market.city,
      score: market.taste_score || 0,
      quadrant: market.quadrant || "unknown",
    }));

  if (data.length === 0) {
    return (
      <div className="chartCard" style={{ minHeight: 320 }}>
        <p className="muted" style={{ textAlign: "center", padding: 48 }}>
          No taste score data available
        </p>
      </div>
    );
  }

  return (
    <div className="chartCard">
      <div className="stackSm">
        <span className="kindTag">Distribution</span>
        <h3 className="headingSm">{title}</h3>
        <span className="caption">Taste score percentile · top 20 markets</span>
      </div>
      <div style={{ height: 320 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 4 }}>
            <CartesianGrid horizontal={false} stroke="#eeeeee" />
            <XAxis type="number" domain={[0, 100]} tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
            <YAxis
              type="category"
              dataKey="city"
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 10 }}
              width={104}
              interval={0}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f4f4f4" }} />
            <Bar dataKey="score" radius={[0, 2, 2, 0]} maxBarSize={16}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={QUADRANT_COLORS[entry.quadrant] ?? QUADRANT_COLORS.unknown} />
              ))}
            </Bar>
          </BarChart>
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
