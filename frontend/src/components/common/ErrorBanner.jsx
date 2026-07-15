export default function ErrorBanner({ message, onRetry }) {
  return (
    <div className="panel border-signal-refute/30 flex flex-col gap-3 px-6 py-5">
      <div>
        <p className="text-sm font-semibold text-signal-refute">The analysis couldn't complete</p>
        <p className="mt-1 text-sm text-slate">{message}</p>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="self-start rounded-sm border border-ink/15 px-3 py-1.5 text-xs font-medium text-ink hover:bg-ink/5"
        >
          Try again
        </button>
      )}
    </div>
  );
}
