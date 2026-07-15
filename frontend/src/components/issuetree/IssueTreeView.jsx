import BranchCard from "./BranchCard.jsx";

/**
 * @param {{
 *   issueTree: import("../../lib/types.js").IssueTree,
 *   findings: import("../../lib/types.js").HypothesisFinding[]
 * }} props
 */
export default function IssueTreeView({ issueTree, findings }) {
  const findingByBranch = Object.fromEntries((findings || []).map((f) => [f.branch_id, f]));

  return (
    <div className="flex flex-col gap-6">
      <div className="panel p-6">
        <span className="label-eyebrow text-gold">Restated question</span>
        <p className="mt-1.5 font-display text-xl leading-snug text-ink">{issueTree.restated_question}</p>
      </div>

      <div>
        <div className="mb-3 flex items-center gap-2">
          <span className="label-eyebrow text-ink/50">MECE issue tree</span>
          <div className="h-px flex-1 bg-ink/10" />
          <span className="label-eyebrow text-ink/50">{issueTree.branches.length} branches</span>
        </div>
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {issueTree.branches.map((branch, i) => (
            <BranchCard key={branch.id} branch={branch} finding={findingByBranch[branch.id]} index={i} />
          ))}
        </div>
      </div>
    </div>
  );
}
