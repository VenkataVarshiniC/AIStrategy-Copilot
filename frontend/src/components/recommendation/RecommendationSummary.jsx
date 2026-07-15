import ConfidenceMeter from "../common/ConfidenceMeter.jsx";

/**
 * @param {{ recommendation: import("../../lib/types.js").Recommendation }} props
 */
export default function RecommendationSummary({ recommendation }) {
  return (
    <div className="panel relative overflow-hidden border-ink bg-ink p-7">
      <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-gold/10" aria-hidden="true" />

      <span className="label-eyebrow text-gold-light">Recommendation</span>
      <h2 className="mt-2 font-display text-2xl font-semibold leading-tight text-paper">{recommendation.headline}</h2>
      <p className="mt-3 max-w-3xl text-sm leading-relaxed text-paper/80">{recommendation.executive_summary}</p>

      <div className="mt-5 grid grid-cols-1 gap-6 border-t border-paper/10 pt-5 md:grid-cols-2">
        <div>
          <span className="label-eyebrow text-paper/50">Supporting points</span>
          <ul className="mt-2 flex flex-col gap-1.5">
            {recommendation.supporting_points.map((point, i) => (
              <li key={i} className="flex gap-2 text-sm text-paper/85">
                <span className="text-gold-light">+</span>
                {point}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <span className="label-eyebrow text-paper/50">Risks &amp; caveats</span>
          <ul className="mt-2 flex flex-col gap-1.5">
            {recommendation.risks_and_caveats.map((risk, i) => (
              <li key={i} className="flex gap-2 text-sm text-paper/85">
                <span className="text-signal-refute">!</span>
                {risk}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-5 border-t border-paper/10 pt-4">
        <ConfidenceMeter value={recommendation.confidence} label="Overall confidence" dark />
      </div>
    </div>
  );
}
