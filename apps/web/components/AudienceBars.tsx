import { formatShare } from "@/lib/format";
import type { AudienceRow } from "@/lib/types";

export function AudienceBars({ audience }: { audience: AudienceRow[] }) {
  if (audience.length === 0) {
    return <p className="muted">No audience data for this market yet.</p>;
  }
  const max = Math.max(...audience.map((row) => row.over_index ?? 0), 1.2);
  return (
    <div className="bars">
      {audience.map((row) => {
        const width = row.over_index === null ? 0 : Math.max((row.over_index / max) * 100, 2);
        return (
          <div key={`${row.dimension}-${row.band}-${row.label}`} className="barRow">
            <div>
              <div style={{ fontWeight: 500 }}>{row.label}</div>
              <div className="caption">{row.dimension}</div>
            </div>
            <div
              className="barTrack"
              title={`${row.label}: ${formatShare(row.share)} of this market's audience vs ${formatShare(row.baseline_share)} baseline`}
            >
              <div
                className={row.over_index !== null && row.over_index >= 1 ? "barFill" : "barFill barFillAlt"}
                style={{ width: `${width}%` }}
              />
            </div>
            <div className="num caption" style={{ textAlign: "right" }}>
              {row.over_index === null ? "—" : `${row.over_index.toFixed(2)}×`}
            </div>
          </div>
        );
      })}
    </div>
  );
}
