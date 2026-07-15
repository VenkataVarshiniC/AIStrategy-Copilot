import { formatPercent } from "../../lib/utils.js";

/**
 * @param {{ value: number, label?: string, dark?: boolean }} props
 */
export default function ConfidenceMeter({ value, label = "Confidence", dark = false }) {
  const pct = Math.round((value ?? 0) * 100);
  const tone = pct >= 70 ? "bg-signal-support" : pct >= 40 ? "bg-signal-partial" : "bg-signal-refute";

  return (
    <div className="flex items-center gap-2">
      <span className={`label-eyebrow shrink-0 ${dark ? "text-paper/50" : ""}`}>{label}</span>
      <div className={`h-1.5 w-20 overflow-hidden rounded-full ${dark ? "bg-paper/15" : "bg-ink/10"}`}>
        <div className={`h-full rounded-full ${tone}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`font-mono text-xs ${dark ? "text-paper/70" : "text-slate"}`}>{formatPercent(value)}</span>
    </div>
  );
}
