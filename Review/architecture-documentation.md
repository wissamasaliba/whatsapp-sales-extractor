# Architecture Documentation
**Project:** WhatsApp Sales Extractor
**Generated:** 2026-02-22

---

## High-Level System Architecture

The application is a two-tier web system: a React single-page application (SPA) in the browser communicates over HTTP with a FastAPI backend. The backend orchestrates four sequential AI agents, each calling the Groq inference API, to transform an unstructured WhatsApp chat export into clean, validated sales records.

```
┌─────────────────────────────────────────────────────────┐
│                        BROWSER                          │
│                                                         │
│   ┌──────────┐   ┌─────────────┐   ┌────────────────┐  │
│   │  Navbar  │   │ UploadPanel │   │  SalesTable +  │  │
│   │          │   │ (drag/drop) │   │  ExportButton  │  │
│   └──────────┘   └──────┬──────┘   └───────┬────────┘  │
│                          │ POST /upload     │ POST /export│
│                          └────────┬─────────┘           │
└───────────────────────────────────│─────────────────────┘
                                    │ HTTP (Axios)
                                    ▼
┌─────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                       │
│                                                         │
│   ┌──────────────────────────────────────────────────┐  │
│   │              Orchestrator                        │  │
│   │                                                  │  │
│   │  ┌─────────────┐    ┌──────────────┐            │  │
│   │  │ ParserAgent │───▶│ExtractorAgent│            │  │
│   │  └─────────────┘    └──────┬───────┘            │  │
│   │                            │                    │  │
│   │  ┌──────────────┐   ┌──────▼──────┐            │  │
│   │  │  BugChecker  │◀──│ValidatorAgent│            │  │
│   │  └──────┬───────┘   └─────────────┘            │  │
│   │         │                                       │  │
│   └─────────│───────────────────────────────────────┘  │
│             │ JSON result                               │
│             ▼                                           │
│   ┌──────────────────┐   ┌──────────────────────────┐  │
│   │  /upload response│   │  excel_writer → .xlsx    │  │
│   └──────────────────┘   └──────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                        │ API calls
                        ▼
          ┌─────────────────────────┐
          │   Groq Inference API    │
          │   (qwen/qwen3-32b)      │
          └─────────────────────────┘
```

---

## Component Layers

### Layer 1 — Presentation (Browser)

| Component | Responsibility |
|-----------|---------------|
| `Navbar` | Branding — logo and app name |
| `UploadPanel` | File selection, drag-and-drop, upload progress |
| `SalesTable` | Display validated sales; collapsible error panel |
| `ExportButton` | Trigger Excel download |
| `App` | State owner — switches between upload and results views |
| `api/client.js` | HTTP abstraction — Axios instance, upload + export calls |

### Layer 2 — API Gateway (FastAPI)

| Module | Responsibility |
|--------|---------------|
| `main.py` | Route definitions, CORS middleware, request/response handling |
| `excel_writer.py` | Standalone utility — converts sales dicts to a styled `.xlsx` |

### Layer 3 — Agent Pipeline (Orchestrator)

| Agent | Input | Output |
|-------|-------|--------|
| `ParserAgent` | Raw .txt string | List of message dicts |
| `ExtractorAgent` | Message dicts | Raw sale dicts (unvalidated) |
| `ValidatorAgent` | Raw sale dicts | Validated + normalised sale dicts |
| `BugChecker` | Validated sale dicts | `{ sales, errors }` |

### Layer 4 — AI Inference (External)

| Service | Model | Usage |
|---------|-------|-------|
| Groq API | `qwen/qwen3-32b` | Sale extraction, record repair, anomaly audit |

---

## Data Flow — WhatsApp Upload to Excel Export

```
User selects .txt file
        │
        ▼
UploadPanel.handleFile()
  └── Validates extension (.txt only)
  └── Calls uploadChat(file) via Axios POST /upload
        │
        ▼
FastAPI: POST /upload
  └── Reads file bytes, decodes UTF-8
  └── Calls Orchestrator.run(text, filename)
        │
        ▼
┌─── Agent Pipeline ───────────────────────────────────┐
│                                                       │
│  1. ParserAgent.run(raw_text)                         │
│     └── parse_chat() splits text by TIMESTAMP_PATTERN │
│     └── Multi-line messages joined into single block  │
│     └── Returns: List[{ timestamp, sender, text,      │
│                          is_system }]                  │
│                                                       │
│  2. ExtractorAgent.run(messages)                      │
│     └── extract_sales_candidates() filters by regex   │
│          (price/quantity signals)                      │
│     └── Batches of 30 sent to Groq LLM               │
│     └── LLM returns JSON array of sale objects        │
│     └── Returns: List[raw_sale_dicts]                 │
│                                                       │
│  3. ValidatorAgent.run(sales)                         │
│     └── _split(): discard media placeholders,         │
│          coerce numerics, separate clean from broken  │
│     └── _fix_with_groq(): repair incomplete records   │
│     └── Returns: List[validated_sale_dicts]           │
│                                                       │
│  4. BugChecker.run(sales)                             │
│     └── _local_checks(): dedup, arithmetic check,    │
│          flag product-only records                    │
│     └── Groq audit: outliers, cross-record anomalies  │
│     └── Returns: { sales: [...], errors: [...] }      │
│                                                       │
└───────────────────────────────────────────────────────┘
        │
        ▼
FastAPI returns JSON:
  { filename, sales[], errors[], stats{} }
        │
        ▼
App.handleResult(data) stores result in React state
        │
        ├── SalesTable renders sales rows + error panel
        └── ExportButton becomes active
                │
                ▼
        User clicks "Export to Excel"
                │
                ▼
        ExportButton.handleExport()
          └── Calls exportToExcel(sales) via Axios POST /export
                │
                ▼
        FastAPI: POST /export
          └── write_to_excel(sales, tmp_path)
               └── Creates styled .xlsx with openpyxl
               └── Auto-fits column widths
          └── Returns FileResponse (binary .xlsx stream)
                │
                ▼
        Axios receives blob → creates object URL
          └── <a> click triggers browser download
          └── sales_export.xlsx saved to user's device
```

---

## Agent Orchestration Flow

```
Orchestrator.run(raw_text, filename)
        │
        ├─▶ ParserAgent.run(raw_text)
        │         │
        │         └── parse_chat() [rule-based, no API call]
        │         └── Returns messages[]
        │
        ├─▶ ExtractorAgent.run(messages[])
        │         │
        │         ├── extract_sales_candidates() [rule-based filter]
        │         │       └── Discards messages with no price/qty signals
        │         │
        │         └── Groq API ×N batches [LLM call]
        │                 └── Returns raw_sales[]
        │
        ├─▶ ValidatorAgent.run(raw_sales[])
        │         │
        │         ├── _split() [rule-based]
        │         │       ├── clean[]      ──────────────────┐
        │         │       └── needs_fix[]                    │
        │         │                                          │
        │         └── _fix_with_groq(needs_fix[]) [LLM call] │
        │                 └── fixed[]  ──────────────────────┤
        │                                                    │
        │         └── Returns clean[] + fixed[] ◀────────────┘
        │
        └─▶ BugChecker.run(validated_sales[])
                  │
                  ├── _local_checks() [rule-based]
                  │       ├── Dedup by (timestamp, sender, product)
                  │       ├── Auto-correct arithmetic mismatches
                  │       └── Flag product-only records
                  │
                  └── Groq audit [LLM call]
                          ├── Price outlier detection
                          ├── Remaining duplicate detection
                          └── Cross-record inconsistency flagging
                  │
                  └── Returns { sales[], errors[] }
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Rule-based pre-filter before LLM calls | Reduces API cost and latency by discarding irrelevant messages before sending to Groq |
| Batching in ExtractorAgent (30 per batch) | Stays within LLM context/token limits for large chats |
| Two-phase validation (local + LLM) | Fast deterministic checks run first; LLM used only for ambiguous cases |
| Shared Groq client in `extractor.py` | Single initialisation point imported by all agent modules |
| Async pipeline throughout | FastAPI + async agents allow non-blocking I/O for concurrent requests |
| Media placeholder filtering at two levels | ValidatorAgent and BugChecker both filter independently to prevent false error flags |

---

## CORS Configuration

The backend allows cross-origin requests from the Vite dev server and common React ports:

```python
allow_origins=["http://localhost:5173", "http://localhost:3000"]
```

For production deployment, restrict this to the actual frontend domain.

---

## Error Handling Strategy

| Layer | Approach |
|-------|----------|
| FastAPI endpoints | HTTPException with descriptive detail strings |
| ExtractorAgent | Silent skip on JSON parse failure; BugChecker flags the gap |
| ValidatorAgent | Falls back to empty list on LLM parse failure |
| BugChecker | Returns raw sales with a parse-failure error entry on LLM failure |
| Frontend upload | Surfaces `err.response?.data?.detail` or a generic fallback |
| Frontend export | Inline error message below the button |
