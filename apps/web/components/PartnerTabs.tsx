"use client";

import { useState } from "react";
import { formatLift } from "@/lib/format";
import type { PartnerOut } from "@/lib/types";

const TYPE_LABELS: Record<string, string> = {
  media: "Media",
  podcast: "Podcasts",
  brand: "Brands",
  creator: "Creators",
  venue: "Venues",
  other: "Other",
};

export function PartnerTabs({ partners }: { partners: Record<string, PartnerOut[]> }) {
  const types = Object.keys(partners).filter((type) => (partners[type] ?? []).length > 0);
  const [active, setActive] = useState(types[0] ?? "");
  if (types.length === 0) {
    return <p className="muted">No partners recorded for this market yet.</p>;
  }
  const rows = partners[active] ?? [];
  return (
    <div className="stack">
      <div className="tabs" role="tablist">
        {types.map((type) => (
          <button
            key={type}
            role="tab"
            aria-selected={active === type}
            className={active === type ? "tab tabActive" : "tab"}
            onClick={() => setActive(type)}
          >
            {TYPE_LABELS[type] ?? type} ({(partners[type] ?? []).length})
          </button>
        ))}
      </div>
      <ul>
        {rows.map((partner) => (
          <li key={`${partner.partner_type}-${partner.entity_id}`} className="partnerRow">
            <span className="partnerName">
              {partner.name}
              {partner.market_specific ? (
                <span className="pill pillGood" title="Found specifically for this market">
                  market-specific
                </span>
              ) : (
                <span className="pill" title="Found across the destination's profile">
                  profile-wide
                </span>
              )}
            </span>
            <span className="num caption" title="Taste lift of this partner against the destination profile">
              {formatLift(partner.lift)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
