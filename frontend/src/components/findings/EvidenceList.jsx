/**
 * @param {{ evidence: import("../../lib/types.js").Evidence[] }} props
 */
export default function EvidenceList({ evidence }) {
  if (!evidence || evidence.length === 0) {
    return <p className="text-xs italic text-slate/60">No grounding evidence retrieved for this branch.</p>;
  }

  return (
    <div>
      <span className="label-eyebrow">Evidence ({evidence.length})</span>
      <ul className="mt-1.5 flex flex-col gap-2">
        {evidence.map((e, i) => (
          <li key={`${e.source}-${i}`} className="rounded-sm bg-ink/[0.03] p-2.5 text-xs text-slate">
            <p className="leading-relaxed">{e.snippet}</p>
            <div className="mt-1.5 flex items-center justify-between">
              <span className="truncate font-mono text-[10px] text-ink/40">{e.source}</span>
              <span className="shrink-0 font-mono text-[10px] text-ink/40">match {(e.score * 100).toFixed(0)}%</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
