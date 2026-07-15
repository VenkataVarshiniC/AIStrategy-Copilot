import { STATUS_META } from "../../lib/utils.js";

// Tailwind's JIT scanner only picks up class names that appear as complete
// strings in source, so dynamic template interpolation (e.g. `border-${x}/30`)
// silently fails to generate CSS. This static map keeps every class string whole.
const BADGE_CLASSES = {
  supported: "border-signal-support/30 bg-signal-support/10 text-signal-support",
  partially_supported: "border-signal-partial/30 bg-signal-partial/10 text-signal-partial",
  refuted: "border-signal-refute/30 bg-signal-refute/10 text-signal-refute",
  inconclusive: "border-signal-pending/30 bg-signal-pending/10 text-signal-pending",
  pending: "border-signal-pending/30 bg-signal-pending/10 text-signal-pending",
};

/**
 * @param {{ status: import("../../lib/types.js").HypothesisStatus }} props
 */
export default function StatusBadge({ status }) {
  const meta = STATUS_META[status] || STATUS_META.pending;
  const classes = BADGE_CLASSES[status] || BADGE_CLASSES.pending;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${classes}`}
    >
      <span aria-hidden="true">{meta.symbol}</span>
      {meta.label}
    </span>
  );
}
