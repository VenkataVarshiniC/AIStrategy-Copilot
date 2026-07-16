# AI Strategy Copilot — Backend

Hypothesis-driven consulting engine. Given a business question, it:

1. **Decomposes** the question into a MECE issue tree (3-5 branches, each a testable hypothesis)
2. **Retrieves** grounding evidence per branch via RAG over ingested source documents
3. **Runs quantitative analysis** where relevant (market sizing, financial ratios, sensitivity)
4. **Judges** each hypothesis as supported / refuted / inconclusive, strictly grounded in retrieved evidence
5. **Synthesizes** an answer-first recommendation (Pyramid Principle: headline → support → risks)
6. **Red-teams** its own recommendation — a separate adversarial pass argues against it, surfaces
   the strongest objection, and gives an adjusted confidence
7. **Checks precedents** — optionally pattern-matches the question against ingested case studies
8. **Exports** the whole analysis as a client-ready PowerPoint deck
9. **Compares scenarios** — runs two strategic options head-to-head through the full pipeline and
   produces a comparative verdict

## Architecture

```
app/
├── main.py                    # FastAPI app factory, route mounting
├── config.py                   # Settings (env-driven)
├── api/routes/
│   ├── health.py                # GET  /api/health
│   ├── ingestion.py              # POST /api/ingest/urls, /pdf, /precedents/urls
│   ├── analysis.py               # POST /api/analysis/run       <- main single-option endpoint
│   ├── comparison.py             # POST /api/comparison/run     <- two-option head-to-head
│   └── export.py                 # POST /api/export/pptx        <- deck generation
├── core/                      # Orchestration & reasoning
│   ├── issue_tree.py            # MECE decomposition (LLM)
│   ├── hypothesis_testing.py    # RAG-grounded evidence judgment (LLM)
│   ├── quant_router.py          # Routes branch -> analytics function
│   ├── synthesis.py             # Final recommendation roll-up (LLM)
│   ├── red_team.py              # Adversarial challenge of the recommendation (LLM)
│   ├── precedent_analysis.py    # Comparable-case pattern matching (LLM + RAG)
│   ├── scenario_comparison.py   # Runs two full analyses + head-to-head verdict
│   ├── confidence_utils.py      # Robust confidence-value parsing
│   └── orchestrator.py          # Ties the single-option pipeline together
├── export/
│   └── pptx_export.py           # AnalysisResponse -> python-pptx deck (bytes)
├── rag/                       # Retrieval-augmented generation
│   ├── ingestion.py              # URL/PDF scraping + chunking (evidence AND precedents)
│   ├── vector_store.py           # Chroma client, supports multiple named collections
│   └── retriever.py              # Query -> typed Evidence objects (evidence AND precedents)
├── analytics/                 # Deterministic, LLM-free quant functions
│   ├── market_sizing.py         # TAM/SAM/SOM, CAGR, projections
│   ├── financial_analysis.py    # Margins, NPV, payback, breakeven
│   └── sensitivity.py           # One-way sensitivity, scenario tables
├── llm/
│   └── groq_client.py           # Single point of contact with Groq's API
└── models/
    └── schemas.py               # Pydantic contracts shared end-to-end
```

## Pipeline flow

```
AnalysisRequest
      │
      ▼
generate_issue_tree()  ──▶  IssueTree (restated question + N MECE branches)
      │
      ▼  (per branch, throttled)
run_quant_for_branch()  ──▶  QuantResult (or None for qualitative branches)
      │
      ▼
test_hypothesis()  ──▶  retrieve_evidence() [RAG]  ──▶  HypothesisFinding
      │                                                  (status, so-what, confidence)
      ▼  (after all branches)
synthesize_recommendation()  ──▶  Recommendation (headline, summary, risks)
      │
      ▼
run_red_team_review()  ──▶  RedTeamCritique (strongest objection, verdict, adjusted confidence)
      │
      ▼
analyze_precedents()  ──▶  [PrecedentInsight] (optional — only if precedents were ingested)
      │
      ▼
AnalysisResponse  ──▶  optionally: POST /api/export/pptx  ──▶  client-ready deck
```

Scenario comparison (`/api/comparison/run`) runs this entire pipeline twice — once per
option — then adds one more LLM call to produce a head-to-head verdict.

## Setup

**1. Get a free Groq API key** (no credit card required):

1. Sign up at [console.groq.com](https://console.groq.com)
2. Go to **Settings → API Keys → Create API Key**
3. Copy the key (starts with `gsk_...`)

**2. Run the backend:**

```bash
cp .env.example .env          # then paste your key into GROQ_API_KEY
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Or with Docker:

```bash
docker compose up --build
```

API docs (Swagger) at `http://localhost:8000/docs`. Check `http://localhost:8000/api/health/`
first — it reports whether the Groq API key is valid and reachable.

**Free tier limits** (as of mid-2026, subject to change — check
[console.groq.com/settings/limits](https://console.groq.com/settings/limits)):
the default `llama-3.1-8b-instant` has a much higher free-tier request/token budget than
`llama-3.3-70b-versatile`, which matters a lot now — a single analysis run makes **8+
sequential calls** (issue tree, one per branch, synthesis, red-team, precedents), and
scenario comparison makes roughly double that. `GROQ_REQUEST_DELAY_SECONDS` (default 1.5s)
paces these automatically; raise it if you still see rate-limit warnings.

## Typical workflow

```bash
# 1. Ingest source material (SEC filings, market reports, news articles, etc.)
curl -X POST localhost:8000/api/ingest/urls \
  -H "Content-Type: application/json" \
  -d '{"source_urls": ["https://example.com/market-report"], "tags": {"sector": "EV"}}'

# 1b. Optional: ingest comparable case studies for precedent analysis
curl -X POST localhost:8000/api/ingest/precedents/urls \
  -H "Content-Type: application/json" \
  -d '{"source_urls": ["https://example.com/similar-market-entry-case-study"]}'

# 2. Run the full analysis (now includes red_team + precedents in the response)
curl -X POST localhost:8000/api/analysis/run \
  -H "Content-Type: application/json" \
  -d '{
        "question": "Should Acme Motors enter the Southeast Asian EV market?",
        "company_name": "Acme Motors",
        "industry": "Electric Vehicles",
        "max_branches": 4
      }' > analysis.json

# 3. Export that analysis as a client-ready slide deck
curl -X POST localhost:8000/api/export/pptx \
  -H "Content-Type: application/json" \
  -d @analysis.json \
  --output strategy-deck.pptx

# Or, compare two strategic options head-to-head instead of steps 2-3:
curl -X POST localhost:8000/api/comparison/run \
  -H "Content-Type: application/json" \
  -d '{
        "decision_context": "How should Acme Motors enter the Southeast Asian EV market?",
        "option_a": "Enter directly via a wholly-owned subsidiary",
        "option_b": "Enter via a joint venture with a local OEM",
        "company_name": "Acme Motors",
        "industry": "Electric Vehicles"
      }'
```



## Design principles baked into the code

- **Never fabricate confidence.** `hypothesis_testing.py` explicitly instructs the model to
  mark a branch `inconclusive` rather than invent support when evidence is sparse, and
  `confidence_utils.py` robustly parses whatever confidence format the model returns
  (percent-scale, string, word-scale) instead of crashing on anything but a clean float.
- **Technical failures are never disguised as findings.** A Groq rate limit, auth error, or
  connection failure is NOT the same thing as a genuine evidence-based "inconclusive" —
  the former is a bug/limit, the latter is a legitimate analytical outcome. `hypothesis_testing.py`
  and `synthesis.py` tag technical failures distinctly (so_what explicitly says so) and surface
  them in `AnalysisResponse.warnings`, so you can always tell the two apart.
- **Requests are throttled on purpose.** The pipeline fires 6+ sequential Groq calls per
  analysis run. `orchestrator.py` paces them with `GROQ_REQUEST_DELAY_SECONDS` (default 1.5s)
  to stay under the free tier's tokens-per-minute budget — this is what prevents "every branch
  after the first couple silently fails and shows inconclusive," which was the root cause of
  that exact symptom before this fix.
- **Every number is traceable.** `quant_router.py` labels all illustrative defaults so
  outputs never silently masquerade as real client data.
- **Deterministic analytics stay LLM-free.** `analytics/` has zero dependency on the LLM —
  same inputs always produce the same numbers, which is testable and auditable.
- **One LLM chokepoint.** All model calls go through `llm/groq_client.py`, so
  retry/model-swap/timeout logic lives in exactly one place. Swapping providers again
  later (local Ollama, Claude, OpenAI) means editing this one file only.
- **JSON truncation doesn't silently break a branch.** `complete_json` attempts to repair
  malformed/truncated JSON (unbalanced braces, trailing commas) before giving up, since a
  single dropped brace shouldn't force an otherwise-good finding to `inconclusive`.
- **Retries honor the server, not a guess.** On a 429, `groq_client.py` reads the `Retry-After`
  header Groq returns and waits exactly that long, rather than a blind exponential backoff that
  might not actually clear by the time it retries.

## Troubleshooting

**Every branch comes back "inconclusive" with no/low confidence**

Check `AnalysisResponse.warnings` in the JSON response first — this field exists specifically
to answer "why." Two distinct causes look identical in the UI but are very different:

1. **Empty knowledge base** (most common on a fresh setup): if you haven't called
   `/api/ingest/urls` or `/api/ingest/pdf` yet, there's no evidence to ground any finding in,
   and "inconclusive" is the *correct*, honest answer — not a bug. `warnings` will say so
   explicitly. Ingest something first (see the Typical Workflow section above).
2. **Groq rate limit hit mid-run**: the pipeline makes 6+ sequential calls per analysis
   (issue tree + one per branch + synthesis). On the free tier this can burst past the
   tokens-per-minute budget partway through a single run. `warnings` will list which branch(es)
   failed and why. If you see this: raise `GROQ_REQUEST_DELAY_SECONDS` in `.env` (try 3-4s),
   or confirm `GROQ_MODEL=llama-3.1-8b-instant` (much higher free-tier budget than the 70b
   model), or check your usage at
   [console.groq.com/settings/limits](https://console.groq.com/settings/limits).

**"GROQ_API_KEY is not set"**

You haven't added a key to `.env` yet. Sign up free at
[console.groq.com](https://console.groq.com), create a key under Settings → API Keys, and
set `GROQ_API_KEY=gsk_...` in your `.env` file. Restart uvicorn after editing `.env`.

**"Groq rejected the API key"**

Double-check you copied the full key (starts with `gsk_`) with no extra whitespace, and that
`.env` is in the `backend/` folder (not a subfolder) so `pydantic-settings` picks it up.

**"Groq free-tier rate limit hit and retries exhausted" (HTTP 429)**

The built-in retry logic already waits out Groq's own `Retry-After` header (up to 5 attempts)
before raising this — if you're still hitting it, the free tier is genuinely saturated for the
moment. Wait a minute, raise `GROQ_REQUEST_DELAY_SECONDS` in `.env`, check usage at
[console.groq.com/settings/limits](https://console.groq.com/settings/limits), or switch
`GROQ_MODEL` to `llama-3.1-8b-instant` (default), which has a much higher free-tier budget
than `llama-3.3-70b-versatile`.

**JSON parsing errors from `complete_json`**

Rare on Groq's larger models, but if it happens often, `complete_json` already attempts an
automatic repair (truncated JSON, trailing commas) before raising — check the logs for a
"recovered via repair" warning vs. a hard failure. If hard failures persist, try switching
`GROQ_MODEL` to `llama-3.3-70b-versatile` — stronger structured-output reliability, at the
cost of a tighter free-tier rate limit (see the rate-limit note above).

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

Covers the deterministic analytics and chunking logic — no Groq API key or network call
required. LLM-dependent pipeline stages are best verified via the running API once
`GROQ_API_KEY` is set.

## Roadmap (post-MVP)

- Structured parameter extraction from ingested docs to auto-populate `quant_params`
  instead of relying on caller-supplied or default figures
- Streaming responses so the frontend can render the issue tree as it's generated
- Auth + per-user knowledge bases
- PDF export alongside PPTX (same `AnalysisResponse` → different renderer)
- Multi-round red-team (a rebuttal pass after the initial challenge, mirroring a real back-and-forth)
- N-way scenario comparison (more than two options) instead of the current pairwise-only mode
