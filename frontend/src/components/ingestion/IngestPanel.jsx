import { useEffect, useState } from "react";
import { getIngestionStatus, ingestPdf, ingestUrls, resetKnowledgeBase } from "../../api/ingestion.js";

export default function IngestPanel() {
  const [urlInput, setUrlInput] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | done | error
  const [message, setMessage] = useState("");
  const [chunkCount, setChunkCount] = useState(null);

  useEffect(() => {
    refreshStatus();
  }, []);

  async function refreshStatus() {
    try {
      const res = await getIngestionStatus();
      setChunkCount(res.total_chunks);
    } catch {
      setChunkCount(null);
    }
  }

  async function handleIngestUrls() {
    const urls = urlInput
      .split("\n")
      .map((u) => u.trim())
      .filter(Boolean);
    if (urls.length === 0) return;

    setStatus("loading");
    setMessage("");
    try {
      const res = await ingestUrls(urls);
      setMessage(`Ingested ${res.total_chunks} chunks from ${urls.length} source${urls.length > 1 ? "s" : ""}.`);
      setStatus("done");
      setUrlInput("");
      refreshStatus();
    } catch (e) {
      setMessage("Couldn't ingest those URLs. Check the backend logs for details.");
      setStatus("error");
    }
  }

  async function handleFileUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setStatus("loading");
    setMessage("");
    try {
      const res = await ingestPdf(file);
      setMessage(`Ingested ${res.chunks_ingested} chunks from ${res.filename}.`);
      setStatus("done");
      refreshStatus();
    } catch {
      setMessage("Couldn't ingest that PDF. Check the backend logs for details.");
      setStatus("error");
    } finally {
      e.target.value = "";
    }
  }

  async function handleReset() {
    if (!window.confirm("Clear all ingested documents from the knowledge base?")) return;
    await resetKnowledgeBase();
    setMessage("Knowledge base cleared.");
    setStatus("done");
    refreshStatus();
  }

  return (
    <div id="knowledge-base" className="panel flex flex-col gap-4 p-6">
      <div className="flex items-start justify-between">
        <div>
          <span className="label-eyebrow text-gold">Grounding evidence</span>
          <h2 className="mt-1 font-display text-lg text-ink">Knowledge base</h2>
        </div>
        <span className="rounded-full bg-ink/5 px-2.5 py-1 font-mono text-xs text-slate">
          {chunkCount ?? "—"} chunks
        </span>
      </div>

      <p className="text-sm text-slate">
        Every claim in the analysis is grounded in what's ingested here. Add source URLs (market reports, filings,
        news) or upload a PDF before running an analysis for citable evidence.
      </p>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="urls" className="text-sm font-medium text-ink">
          Source URLs (one per line)
        </label>
        <textarea
          id="urls"
          value={urlInput}
          onChange={(e) => setUrlInput(e.target.value)}
          rows={3}
          placeholder="https://example.com/market-report"
          className="resize-none rounded-sm border border-ink/15 bg-white px-3 py-2 text-sm text-ink placeholder:text-slate/60 focus-visible:border-gold"
        />
        <button
          type="button"
          onClick={handleIngestUrls}
          disabled={status === "loading" || !urlInput.trim()}
          className="mt-1 self-start rounded-sm border border-ink/15 px-3 py-1.5 text-xs font-medium text-ink hover:bg-ink/5 disabled:opacity-40"
        >
          Ingest URLs
        </button>
      </div>

      <div className="flex flex-col gap-1.5 border-t border-ink/10 pt-4">
        <label htmlFor="pdf-upload" className="text-sm font-medium text-ink">
          Upload PDF
        </label>
        <input
          id="pdf-upload"
          type="file"
          accept="application/pdf"
          onChange={handleFileUpload}
          disabled={status === "loading"}
          className="text-sm text-slate file:mr-3 file:rounded-sm file:border file:border-ink/15 file:bg-white file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-ink hover:file:bg-ink/5"
        />
      </div>

      {message && (
        <p className={`text-xs ${status === "error" ? "text-signal-refute" : "text-signal-support"}`}>{message}</p>
      )}

      {chunkCount > 0 && (
        <button
          type="button"
          onClick={handleReset}
          className="self-start text-xs text-slate underline decoration-dotted hover:text-signal-refute"
        >
          Clear knowledge base
        </button>
      )}
    </div>
  );
}
