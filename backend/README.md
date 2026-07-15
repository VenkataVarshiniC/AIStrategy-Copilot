# AI Strategy Copilot — Backend

Hypothesis-driven consulting engine. Given a business question, it:

1. **Decomposes** the question into a MECE issue tree (3-5 branches, each a testable hypothesis)
2. **Retrieves** grounding evidence per branch via RAG over ingested source documents
3. **Runs quantitative analysis** where relevant (market sizing, financial ratios, sensitivity)
4. **Judges** each hypothesis as supported / refuted / inconclusive, strictly grounded in retrieved evidence
5. **Synthesizes** an answer-first recommendation (Pyramid Principle: headline → support → risks)

## Architecture

```
app/
├── main.py                 # FastAPI app factory, route mounting
├── config.py                # Settings (env-driven)
├── api/routes/
│   ├── health.py            # GET  /api/health
│   ├── ingestion.py          # POST /api/ingest/urls, /api/ingest/pdf
│   └── analysis.py           # POST /api/analysis/run   <- main endpoint
├── core/                     # Orchestration & reasoning
│   ├── issue_tree.py          # MECE decomposition (LLM)
│   ├── hypothesis_testing.py  # RAG-grounded evidence judgment (LLM)
│   ├── quant_router.py        # Routes branch -> analytics function
│   ├── synthesis.py           # Final recommendation roll-up (LLM)
│   └── orchestrator.py        # Ties the above into one pipeline
├── rag/                      # Retrieval-augmented generation
│   ├── ingestion.py            # URL/PDF scraping + chunking
│   ├── vector_store.py         # Chroma persistent client
│   └── retriever.py            # Query -> typed Evidence objects
├── analytics/                # Deterministic, LLM-free quant functions
│   ├── market_sizing.py        # TAM/SAM/SOM, CAGR, projections
│   ├── financial_analysis.py   # Margins, NPV, payback, breakeven
│   └── sensitivity.py          # One-way sensitivity, scenario tables
├── llm/
│   └── ollama_client.py        # Single point of contact with the local model (Ollama)
└── models/
    └── schemas.py              # Pydantic contracts shared end-to-end
```

## Pipeline flow

```
AnalysisRequest
      │
      ▼
generate_issue_tree()  ──▶  IssueTree (restated question + N MECE branches)
      │
      ▼  (per branch)
run_quant_for_branch()  ──▶  QuantResult (or None for qualitative branches)
      │
      ▼
test_hypothesis()  ──▶  retrieve_evidence() [RAG]  ──▶  HypothesisFinding
      │                                                  (status, so-what, confidence)
      ▼  (after all branches)
synthesize_recommendation()  ──▶  Recommendation (headline, summary, risks)
      │
      ▼
AnalysisResponse
```

## Setup

**1. Install Ollama and pull a model** (one-time, no account/API key needed):

```bash
# Install from https://ollama.com/download, then:
ollama pull llama3.1
```

Ollama runs a local server on `http://localhost:11434` automatically after install —
nothing else to configure. Bigger/better models (if your machine can handle them):
`ollama pull llama3.1:70b` or `ollama pull mistral-nemo`, then set `OLLAMA_MODEL`
in `.env` to match.

**2. Run the backend:**

```bash
cp .env.example .env          # defaults already point at localhost:11434
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Or with Docker (note: Ollama itself still runs on your host machine, not in the container —
use `OLLAMA_BASE_URL=http://host.docker.internal:11434` in `.env` if running the backend via Docker):

```bash
docker compose up --build
```

API docs (Swagger) at `http://localhost:8000/docs`. Check `http://localhost:8000/api/health/`
first — it reports whether Ollama is reachable and whether the configured model is pulled.

## Typical workflow

```bash
# 1. Ingest source material (SEC filings, market reports, news articles, etc.)
curl -X POST localhost:8000/api/ingest/urls \
  -H "Content-Type: application/json" \
  -d '{"source_urls": ["https://example.com/market-report"], "tags": {"sector": "EV"}}'

# 2. Run the full analysis
curl -X POST localhost:8000/api/analysis/run \
  -H "Content-Type: application/json" \
  -d '{
        "question": "Should Acme Motors enter the Southeast Asian EV market?",
        "company_name": "Acme Motors",
        "industry": "Electric Vehicles",
        "max_branches": 4
      }'
```

## Design principles baked into the code

- **Never fabricate confidence.** `hypothesis_testing.py` explicitly instructs the model to
  mark a branch `inconclusive` rather than invent support when evidence is sparse.
- **Every number is traceable.** `quant_router.py` labels all illustrative defaults so
  outputs never silently masquerade as real client data.
- **Deterministic analytics stay LLM-free.** `analytics/` has zero dependency on the LLM —
  same inputs always produce the same numbers, which is testable and auditable.
- **One LLM chokepoint.** All model calls go through `llm/ollama_client.py`, so
  retry/model-swap/timeout logic lives in exactly one place. Swapping to a cloud
  provider later (or back to Claude) means editing this one file only.

## Troubleshooting

**"Couldn't reach Ollama at http://localhost:11434"**

Ollama isn't running. It normally starts automatically after install and stays running
in the background. If not, start it manually in a separate terminal:
```bash
ollama serve
```
Then confirm the model is actually pulled (this is a one-time multi-GB download):
```bash
ollama list
ollama pull llama3.1   # if it's not in the list above
```

**Responses are slow or the model seems to "hang"**

Local models run on your CPU/GPU, not a data center — a single analysis makes several
sequential LLM calls (issue tree → per-branch judgment ×N → synthesis), so expect it to
take noticeably longer than a cloud API, especially on a laptop without a dedicated GPU.
If it's painfully slow, try a smaller model: `ollama pull llama3.1:8b` (this is
already the default tag) or `ollama pull phi3` for an even lighter option.

**JSON parsing errors from `complete_json`**

Smaller/quantized models occasionally drift from valid JSON even with `format: "json"`
enabled. If this happens often, switch to a stronger model (`ollama pull mistral-nemo`
or a larger Llama variant) — JSON reliability scales with model size.

**Windows: `chroma-hnswlib` fails to build wheel / "Microsoft Visual C++ 14.0 required"**

This happens when pip can't find a prebuilt wheel for `chroma-hnswlib` for your
Python version and falls back to compiling it from C++ source. Fix, in order of preference:

1. **Use Python 3.11 or 3.12** in your virtual environment — these have prebuilt
   wheels available for `chroma-hnswlib` on Windows, so pip never needs to compile anything:
   ```bash
   py -3.11 -m venv .venv
   .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. If you must use your current Python version, install the
   [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   (select "Desktop development with C++" during install), then re-run `pip install -r requirements.txt`.
3. As a fallback, install a prebuilt wheel directly before the rest of requirements:
   ```bash
   pip install chroma-hnswlib --only-binary :all:
   pip install -r requirements.txt
   ```

## Tests

```bash
pytest
```

Covers the deterministic analytics and chunking logic — no Ollama or model download
required. LLM-dependent pipeline stages are best verified via the running API once
Ollama is installed and a model is pulled.

## Roadmap (post-MVP)

- Structured parameter extraction from ingested docs to auto-populate `quant_params`
  instead of relying on caller-supplied or default figures
- Slide/PDF export of `AnalysisResponse` (python-pptx) for a true "consulting deliverable" output
- Streaming responses so the frontend can render the issue tree as it's generated
- Auth + per-user knowledge bases
