export default function EmptyState() {
  return (
    <div className="panel flex flex-col items-center gap-3 px-8 py-16 text-center">
      <span className="label-eyebrow text-gold">Awaiting a question</span>
      <p className="max-w-md font-display text-xl text-ink">
        Pose the business question on the left, and the issue tree, evidence, and recommendation will build here.
      </p>
    </div>
  );
}
