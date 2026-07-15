import { formatCurrency, formatNumber, formatPercent } from "../../lib/utils.js";

/**
 * @param {{ result: import("../../lib/types.js").QuantResult }} props
 */
export default function QuantResultView({ result }) {
  return (
    <div className="rounded-sm border border-gold/20 bg-gold/[0.04] p-3">
      <span className="label-eyebrow text-gold-dark">Quantitative analysis · {result.method}</span>

      {result.method === "tam_sam_som" && <TamSamSomView outputs={result.outputs} />}
      {result.method === "profitability_ratios" && <RatiosView outputs={result.outputs} />}
      {result.method === "one_way_sensitivity" && <SensitivityView outputs={result.outputs} />}

      {result.narrative && <p className="mt-2 text-xs leading-relaxed text-ink/80">{result.narrative}</p>}
    </div>
  );
}

function TamSamSomView({ outputs }) {
  const rows = [
    { label: "TAM", value: outputs.tam },
    { label: "SAM", value: outputs.sam },
    { label: "SOM", value: outputs.som },
  ];
  const max = outputs.tam || 1;

  return (
    <div className="mt-2 flex flex-col gap-1.5">
      {rows.map((row) => (
        <div key={row.label} className="flex items-center gap-2">
          <span className="w-8 font-mono text-[11px] text-ink/60">{row.label}</span>
          <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-ink/5">
            <div
              className="h-full rounded-full bg-gold"
              style={{ width: `${Math.max((row.value / max) * 100, 3)}%` }}
            />
          </div>
          <span className="w-20 shrink-0 text-right font-mono text-[11px] text-ink/70">
            {formatCurrency(row.value)}
          </span>
        </div>
      ))}
    </div>
  );
}

function RatiosView({ outputs }) {
  const entries = [
    { label: "Gross margin", value: outputs.gross_margin },
    { label: "Operating margin", value: outputs.operating_margin },
    { label: "Net margin", value: outputs.net_margin },
  ];
  return (
    <div className="mt-2 grid grid-cols-3 gap-2">
      {entries.map((e) => (
        <div key={e.label} className="rounded-sm bg-white/70 p-2 text-center">
          <p className="font-mono text-sm font-medium text-ink">{formatPercent(e.value, 1)}</p>
          <p className="mt-0.5 text-[10px] text-slate">{e.label}</p>
        </div>
      ))}
    </div>
  );
}

function SensitivityView({ outputs }) {
  const sweep = outputs.sweep || [];
  if (sweep.length === 0) return null;
  const values = sweep.map((s) => s.output);
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;

  return (
    <div className="mt-2 flex h-16 items-end gap-1">
      {sweep.map((point, i) => (
        <div key={i} className="flex flex-1 flex-col items-center gap-1">
          <div
            className="w-full rounded-t-sm bg-gold/70"
            style={{ height: `${Math.max(((point.output - min) / range) * 100, 6)}%` }}
            title={`Input ${formatNumber(point.input)} → Output ${formatNumber(point.output)}`}
          />
          <span className="font-mono text-[9px] text-ink/40">{formatNumber(point.input, 0)}</span>
        </div>
      ))}
    </div>
  );
}
