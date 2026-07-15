export default function Header() {
  return (
    <header className="border-b border-ink/10 bg-ink">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <div className="flex items-baseline gap-3">
          <span className="font-display text-xl font-semibold text-paper">Strategy Copilot</span>
          <span className="label-eyebrow text-gold-light">Hypothesis-driven analysis engine</span>
        </div>
        <nav className="flex items-center gap-6 text-sm text-paper/70">
          <a href="#knowledge-base" className="hover:text-paper">
            Knowledge base
          </a>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="rounded-sm border border-paper/20 px-3 py-1.5 text-paper hover:border-gold hover:text-gold-light"
          >
            View source
          </a>
        </nav>
      </div>
    </header>
  );
}
