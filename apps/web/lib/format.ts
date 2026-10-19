import type { MarketRow, Quadrant } from "./types";

export function formatScore(score: number | null | undefined): string {
  if (score === null || score === undefined) return "—";
  return score.toFixed(2);
}

export function formatLift(lift: number | null | undefined): string {
  if (lift === null || lift === undefined) return "—";
  const sign = lift >= 0 ? "+" : "";
  return `${sign}${lift.toFixed(4)}`;
}

export function formatPercent(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatShare(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toFixed(2)}%`;
}

export function formatCurrency(amount: number, currency: string): string {
  try {
    return new Intl.NumberFormat("en", {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(amount);
  } catch {
    return `${amount.toFixed(0)} ${currency}`;
  }
}

export const QUADRANT_LABELS: Record<Quadrant, string> = {
  untapped: "Untapped",
  core: "Core",
  habit: "Habit",
  low_priority: "Low priority",
};

export const QUADRANT_HELP: Record<Quadrant, string> = {
  untapped: "Strong taste fit, few arrivals today — the opportunity.",
  core: "Strong taste fit and strong arrivals — defend it.",
  habit: "Weak taste fit but strong arrivals — a habit market.",
  low_priority: "Weak on both — not worth budget now.",
};

export function quadrantClass(quadrant: Quadrant | null): string {
  switch (quadrant) {
    case "untapped":
      return "pill pillGood";
    case "core":
      return "pill pillSky";
    case "habit":
      return "pill pillWarn";
    case "low_priority":
      return "pill";
    default:
      return "pill";
  }
}

export function confidenceClass(confidence: MarketRow["confidence"]): string {
  switch (confidence) {
    case "high":
      return "pill confHigh";
    case "medium":
      return "pill confMedium";
    default:
      return "pill confLow";
  }
}

export function confidenceHelp(confidence: MarketRow["confidence"]): string {
  switch (confidence) {
    case "high":
      return "High: full coverage of the profile and stable lift.";
    case "medium":
      return "Medium: partial coverage of the profile.";
    default:
      return "Low: thin data — treat with caution.";
  }
}

export function flagLabel(flag: string): string {
  switch (flag) {
    case "thin_data":
      return "Thin data";
    case "no_explainability":
      return "No explainability";
    default:
      return flag;
  }
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("en-GB", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return value;
  }
}
