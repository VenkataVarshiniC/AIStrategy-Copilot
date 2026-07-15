import { ANALYSIS_TYPE_LABELS } from "../../lib/utils.js";
import StatusBadge from "../common/StatusBadge.jsx";
import ConfidenceMeter from "../common/ConfidenceMeter.jsx";
import EvidenceList from "../findings/EvidenceList.jsx";
import QuantResultView from "../findings/QuantResultView.jsx";

/**
 * @param {{
 *   branch: import("../../lib/types.js").IssueBranch,
 *   finding?: import("../../lib/types.js").HypothesisFinding,
 *   index: number
 * }} props
 */
export default function BranchCard({ branch, finding, index }) {
  return (
    <div className="panel flex flex-col gap-4 p-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <span className="label-eyebrow mt-1 text-ink/30">{String(index + 1).padStart(2, "0")}</span>
          <div>
            <span className="label-eyebrow text-gold">{ANALYSIS_TYPE_LABELS[branch.analysis_type]}</span>
            <h3 className="mt-0.5 font-display text-lg text-ink">{branch.title}</h3>
          </div>
        </div>
        {finding && <StatusBadge status={finding.status} />}
      </div>

      <p className="border-l-2 border-gold/40 pl-3 text-sm italic text-slate">{branch.hypothesis}</p>

      {branch.key_questions?.length > 0 && (
        <ul className="flex flex-col gap-1">
          {branch.key_questions.map((q) => (
            <li key={q} className="flex gap-2 text-sm text-slate">
              <span className="text-ink/30">—</span>
              {q}
            </li>
          ))}
        </ul>
      )}

      {finding ? (
        <div className="flex flex-col gap-4 border-t border-ink/10 pt-4">
          <div>
            <span className="label-eyebrow">So what</span>
            <p className="mt-1 text-sm leading-relaxed text-ink">{finding.so_what}</p>
          </div>

          {finding.quant_result && <QuantResultView result={finding.quant_result} />}

          {finding.evidence?.length > 0 && <EvidenceList evidence={finding.evidence} />}

          <ConfidenceMeter value={finding.confidence} />
        </div>
      ) : (
        <div className="border-t border-ink/10 pt-4 text-sm text-slate/60">Awaiting analysis…</div>
      )}
    </div>
  );
}
