import type { AngleEvidence } from "@/lib/types";

export function EvidenceList({ evidence }: { evidence: AngleEvidence[] }) {
  if (evidence.length === 0) {
    return <span className="faint caption">No evidence recorded</span>;
  }
  return (
    <div className="row" style={{ gap: 6 }}>
      {evidence.map((item) => (
        <span
          key={item.id}
          className="sourceChip"
          title={
            item.source_call_id
              ? `From Qloo call ${item.source_call_id}`
              : "Derived from this run's Qloo results"
          }
        >
          {item.label}
          {item.value !== null && item.value !== undefined ? `: ${item.value}` : ""}
        </span>
      ))}
    </div>
  );
}
