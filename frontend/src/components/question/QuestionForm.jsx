import { useState } from "react";

const EXAMPLE_QUESTIONS = [
  "Should Acme Motors enter the Southeast Asian EV market?",
  "Should we acquire our closest regional competitor?",
  "Is now the right time to launch a direct-to-consumer channel?",
];

/**
 * @param {{ onSubmit: (payload: object) => void, disabled: boolean }} props
 */
export default function QuestionForm({ onSubmit, disabled }) {
  const [question, setQuestion] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [industry, setIndustry] = useState("");
  const [additionalContext, setAdditionalContext] = useState("");
  const [maxBranches, setMaxBranches] = useState(4);
  const [showAdvanced, setShowAdvanced] = useState(false);

  function handleSubmit(e) {
    e.preventDefault();
    if (!question.trim()) return;
    onSubmit({
      question: question.trim(),
      company_name: companyName.trim() || undefined,
      industry: industry.trim() || undefined,
      additional_context: additionalContext.trim() || undefined,
      max_branches: maxBranches,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="panel flex flex-col gap-5 p-6">
      <div>
        <span className="label-eyebrow text-gold">The engagement</span>
        <h2 className="mt-1 font-display text-lg text-ink">Pose the business question</h2>
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="question" className="text-sm font-medium text-ink">
          Business question
        </label>
        <textarea
          id="question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. Should Acme Motors enter the Southeast Asian EV market?"
          rows={3}
          required
          className="resize-none rounded-sm border border-ink/15 bg-white px-3 py-2 text-sm text-ink placeholder:text-slate/60 focus-visible:border-gold"
        />
        <div className="flex flex-wrap gap-1.5 pt-1">
          {EXAMPLE_QUESTIONS.map((ex) => (
            <button
              type="button"
              key={ex}
              onClick={() => setQuestion(ex)}
              className="rounded-full border border-ink/10 px-2.5 py-1 text-xs text-slate hover:border-gold hover:text-ink"
            >
              {ex.length > 42 ? `${ex.slice(0, 42)}…` : ex}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="company" className="text-sm font-medium text-ink">
            Company
          </label>
          <input
            id="company"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            placeholder="Optional"
            className="rounded-sm border border-ink/15 bg-white px-3 py-2 text-sm text-ink placeholder:text-slate/60 focus-visible:border-gold"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="industry" className="text-sm font-medium text-ink">
            Industry
          </label>
          <input
            id="industry"
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            placeholder="Optional"
            className="rounded-sm border border-ink/15 bg-white px-3 py-2 text-sm text-ink placeholder:text-slate/60 focus-visible:border-gold"
          />
        </div>
      </div>

      <button
        type="button"
        onClick={() => setShowAdvanced((v) => !v)}
        className="self-start text-xs font-medium text-slate hover:text-ink"
      >
        {showAdvanced ? "− Hide advanced options" : "+ Advanced options"}
      </button>

      {showAdvanced && (
        <div className="flex flex-col gap-4 border-t border-ink/10 pt-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="context" className="text-sm font-medium text-ink">
              Additional context
            </label>
            <textarea
              id="context"
              value={additionalContext}
              onChange={(e) => setAdditionalContext(e.target.value)}
              placeholder="Constraints, prior findings, or anything the analysis should account for"
              rows={2}
              className="resize-none rounded-sm border border-ink/15 bg-white px-3 py-2 text-sm text-ink placeholder:text-slate/60 focus-visible:border-gold"
            />
          </div>
          <div className="flex items-center justify-between">
            <label htmlFor="branches" className="text-sm font-medium text-ink">
              Issue tree branches
            </label>
            <input
              id="branches"
              type="number"
              min={2}
              max={6}
              value={maxBranches}
              onChange={(e) => setMaxBranches(Number(e.target.value))}
              className="w-16 rounded-sm border border-ink/15 bg-white px-2 py-1 text-center text-sm text-ink focus-visible:border-gold"
            />
          </div>
        </div>
      )}

      <button
        type="submit"
        disabled={disabled || !question.trim()}
        className="mt-1 rounded-sm bg-ink px-4 py-2.5 text-sm font-medium text-paper transition hover:bg-ink-light disabled:cursor-not-allowed disabled:opacity-40"
      >
        {disabled ? "Running analysis…" : "Run analysis"}
      </button>
    </form>
  );
}
