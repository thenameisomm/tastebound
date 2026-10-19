"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { MarketRow } from "@/lib/types";

interface TasteScoreChartProps {
  markets: MarketRow[];
  title?: string;
}

export function TasteScoreChart({ markets, title = "Taste Score Distribution" }: TasteScoreChartProps) {
  const data = markets
    .filter((m) => m.taste_score !== null)
    .sort((a, b) => (b.taste_score || 0) - (a.taste_score || 0))
    .slice(0, 20)
    .map((m) => ({
      city: m.city,
      score: m.taste_score || 0,
      quadrant: m.quadrant || "unknown",
    }));

  const quadrantColors: Record<string, string> = {
    untapped: "#097fe8",
    core: "#f64932",
    habit: "#ffb110",
    low_priority: "#62aef0",
    unknown: "#979797",
  };

  if (data.length === 0) {
    return (
      <div className="card" style={{ minHeight: 300 }}>
        <p className="muted" style={{ textAlign: "center", padding: 48 }}>
          No taste score data available
        </p>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number; name: string; payload: { city: string } }>; label?: string }) => {
    if (active && payload && payload.length > 0) {
      const item = payload[0];
      const city = label ?? item?.payload?.city ?? "";
      const value = item?.value ?? 0;
      return (
        <div className="card" style={{ padding: "8px 12px", fontSize: 12 }}>
          <p>{city}</p>
          <p>{value.toFixed(1)} Taste Score</p>
        </div>
      );
    }
    return null;
  };

  if (data.length === 0) {
    return (
      <div className="card" style={{ minHeight: 300 }}>
        <p className="muted" style={{ textAlign: "center", padding: 48 }}>
          No taste score data available
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      {title && <h3 className="headingSm" style={{ marginBottom: 16 }}>{title}</h3>}
      <div style={{ height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis type="number" tick={{ fontSize: 11 }} />
            <YAxis
              type="category"
              dataKey="city"
              tick={{ fontSize: 11 }}
              width={120}
              interval={0}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="score" radius={[0, 4, 4, 0]}>
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={quadrantColors[data[index]?.quadrant || "unknown"]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="row" style={{ gap: 16, marginTop: 12, flexWrap: "wrap" }}>
        {Object.entries(quadrantColors).map(([quadrant, color]) => (
          <span key={quadrant} className="pill" style={{ background: color, color: quadrant === "habit" ? "#000" : "#fff" }}>
            {quadrant}
          </span>
        ))}
      </div>
    </div>
  );
}
