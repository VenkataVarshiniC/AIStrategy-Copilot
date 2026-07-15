export function cx(...classes) {
  return classes.filter(Boolean).join(" ");
}

export function formatPercent(value, digits = 0) {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatCurrency(value) {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatNumber(value, digits = 2) {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: digits }).format(value);
}

/** Maps a HypothesisStatus to display label, color token, and short symbol. */
export const STATUS_META = {
  supported: { label: "Supported", color: "signal-support", symbol: "✓" },
  partially_supported: { label: "Partially supported", color: "signal-partial", symbol: "◐" },
  refuted: { label: "Refuted", color: "signal-refute", symbol: "✕" },
  inconclusive: { label: "Inconclusive", color: "signal-pending", symbol: "?" },
  pending: { label: "Pending", color: "signal-pending", symbol: "…" },
};

export const ANALYSIS_TYPE_LABELS = {
  market_sizing: "Market sizing",
  financial_analysis: "Financial analysis",
  sensitivity: "Sensitivity analysis",
  qualitative: "Qualitative",
};
