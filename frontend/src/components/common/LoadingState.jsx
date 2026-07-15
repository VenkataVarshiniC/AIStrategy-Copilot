const STAGES = [
  "Restating the question",
  "Building the MECE issue tree",
  "Retrieving grounding evidence",
  "Running quantitative analysis",
  "Testing each hypothesis",
  "Synthesizing the recommendation",
];

export default function LoadingState() {
  return (
    <div className="panel flex flex-col items-center gap-6 px-8 py-16 text-center">
      <div className="relative h-10 w-10">
        <div className="absolute inset-0 animate-spin rounded-full border-2 border-ink/10 border-t-gold" />
      </div>
      <div>
        <p className="font-display text-lg text-ink">Running the engagement</p>
        <p className="mt-1 text-sm text-slate">This mirrors how a case team would actually work the problem.</p>
      </div>
      <ol className="flex flex-col gap-2 text-left">
        {STAGES.map((stage, i) => (
          <li key={stage} className="flex items-center gap-2.5 text-sm text-slate">
            <span className="label-eyebrow w-5 shrink-0 text-right text-ink/30">{i + 1}</span>
            {stage}
          </li>
        ))}
      </ol>
    </div>
  );
}
