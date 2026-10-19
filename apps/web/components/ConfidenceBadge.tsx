import { confidenceClass, confidenceHelp } from "@/lib/format";
import type { MarketRow } from "@/lib/types";

export function ConfidenceBadge({ confidence }: { confidence: MarketRow["confidence"] }) {
  return (
    <span className={confidenceClass(confidence)} title={confidenceHelp(confidence)}>
      {confidence}
    </span>
  );
}
