# AI Strategy Copilot — Frontend

React + Vite + Tailwind client for the Strategy Copilot backend. Renders the
issue tree, evidence-grounded findings, and answer-first recommendation as
they come back from `/api/analysis/run`.

## Structure

```
src/
├── main.jsx, App.jsx        # Entry point + top-level composition
├── index.css                  # Tailwind directives + base styles
├── api/                       # Thin fetch wrappers, one file per backend router
│   ├── client.js               # Base fetch logic, error normalization
│   ├── analysis.js             # POST /api/analysis/run
│   ├── ingestion.js            # /api/ingest/* endpoints
│   └── health.js               # GET /api/health/
├── hooks/
│   └── useAnalysis.js          # Request lifecycle state machine (idle/loading/success/error)
├── lib/
│   ├── types.js                 # JSDoc mirrors of backend Pydantic schemas
│   └── utils.js                 # Formatting helpers, status/style lookup maps
└── components/
    ├── layout/                   # Header, Shell (two-column app frame)
    ├── question/                 # QuestionForm — the primary input
    ├── ingestion/                 # IngestPanel — knowledge base uploader
    ├── issuetree/                  # IssueTreeView, BranchCard
    ├── findings/                   # EvidenceList, QuantResultView
    ├── recommendation/              # RecommendationSummary
    └── common/                      # StatusBadge, ConfidenceMeter, Loading/Empty/Error states
```

## Design system

- **Colors**: deep ink navy (`#0B1D33`) + warm gold accent (`#B08D57`) on a
  paper-white background — a consulting-deck palette rather than a generic
  SaaS one. Status colors (support/refute/partial/pending) are semantic, not decorative.
- **Type**: Source Serif 4 for headlines (the "deck" voice), Inter for UI, IBM Plex Mono
  for data/labels — mirrors how a real consulting deliverable separates narrative from data.
- **Signature element**: the issue tree renders as numbered branch cards that visually
  fill in with evidence, quant charts, and a status badge as the pipeline completes —
  making the MECE structure the literal shape of the page, not just a concept.

## Setup

```bash
cp .env.example .env      # set VITE_API_BASE_URL if backend isn't on localhost:8000
npm install
npm run dev
```

Runs at `http://localhost:5173`. The Vite dev server also proxies `/api/*` to
the backend (see `vite.config.js`), so `VITE_API_BASE_URL` can usually be left empty in dev.

## Data flow

```
QuestionForm (submit)
      │
      ▼
useAnalysis.submit() ──▶ POST /api/analysis/run ──▶ AnalysisResponse
      │
      ▼
App.jsx renders:
  RecommendationSummary  ← result.recommendation
  IssueTreeView           ← result.issue_tree + result.findings
      └─ BranchCard (×N)   ← one per issue-tree branch
            ├─ StatusBadge
            ├─ QuantResultView   (if branch had a quant model)
            ├─ EvidenceList       (retrieved RAG snippets)
            └─ ConfidenceMeter
```

## Notes

- Plain JavaScript (JSX) rather than TypeScript for MVP speed — `lib/types.js`
  keeps the same documentation value via JSDoc typedefs without a build step.
- No client-side state management library — one custom hook (`useAnalysis`)
  is enough for this request/response shape. Add React Query if the app grows
  multi-request caching needs.
- Tailwind dynamic class names are avoided (e.g. in `StatusBadge`) since the
  JIT compiler only picks up complete class strings from source.

## Roadmap (post-MVP)

- Streaming the issue tree branch-by-branch as the backend generates it,
  instead of one blocking request
- Export the rendered analysis to PDF/PPTX (pairs with the backend's planned
  slide-export feature)
- Session history so past analyses can be revisited without re-running them
