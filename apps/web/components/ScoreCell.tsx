import { formatScore } from "@/lib/format";

export function ScoreCell({ score }: { score: number | null }) {
  if (score === null) {
    return <span className="faint">—</span>;
  }
  return (
    <span className="num" title="Taste score: percentile of lift across this run's markets (0–100)">
      <strong>{formatScore(score)}</strong>
    </span>
  );
}
