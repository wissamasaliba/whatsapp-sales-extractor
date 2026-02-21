# Technical Documentation
**Project:** WhatsApp Sales Extractor
**Version:** 1.0.0
**Generated:** 2026-02-22

---

## Overview

WhatsApp Sales Extractor is a full-stack web application that accepts a WhatsApp group chat export (.txt), runs it through a four-stage AI agent pipeline powered by the Groq API, and returns a structured list of sales records that can be downloaded as an Excel file.

---

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend framework | FastAPI | Latest |
| ASGI server | Uvicorn | Latest |
| AI / LLM API | Groq (qwen/qwen3-32b) | 1.0.0+ |
| Excel generation | openpyxl | Latest |
| Environment config | python-dotenv | Latest |
| Frontend framework | React | 18+ |
| Frontend build tool | Vite | Latest |
| HTTP client | Axios | Latest |
| Language (backend) | Python | 3.10+ |
| Language (frontend) | JavaScript (JSX) | ES2022 |

---

## Project Structure

```
whatsapp-sales-extractor/
├── backend/
│   ├── main.py                  # FastAPI app — endpoints and CORS
│   ├── parser.py                # Rule-based WhatsApp .txt parser
│   ├── extractor.py             # Regex pre-filter + Groq client setup
│   ├── excel_writer.py          # openpyxl Excel file generator
│   └── agents/
│       ├── __init__.py
│       ├── orchestrator.py      # Pipeline coordinator
│       ├── parser_agent.py      # Agent 1: message parsing
│       ├── extractor_agent.py   # Agent 2: sale extraction via LLM
│       ├── validator_agent.py   # Agent 3: validation and normalisation
│       └── bug_checker.py       # Agent 4: anomaly detection and dedup
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx             # React entry point
│       ├── index.css            # Global reset and shared button classes
│       ├── App.jsx              # Root component — upload / results state
│       ├── api/
│       │   └── client.js        # Axios instance + API call functions
│       └── components/
│           ├── Navbar.jsx       # Top navigation bar with logo
│           ├── UploadPanel.jsx  # Drag-and-drop file upload
│           ├── SalesTable.jsx   # Results table with error summary
│           └── ExportButton.jsx # Excel download trigger
├── qa/
│   ├── frontend-visual-review.md   # Visual QA agent instructions
│   └── validate-visual-aspect.md   # Visual validation agent instructions
├── Review/
│   ├── code-reviewer.md            # Code review agent instructions
│   ├── review-results.md           # This review output
│   ├── technical-documentation.md  # This document
│   └── architecture-documentation.md
└── .env                            # Environment variables (not committed)
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | API key for the Groq inference API |
| `VITE_API_URL` | No | Frontend override for backend URL (default: `http://localhost:8000`) |

Create a `.env` file in the `backend/` directory (or project root) with:

```env
GROQ_API_KEY=your_groq_api_key_here
```

---

## Installation & Running

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher
- A Groq API key (free tier available at console.groq.com)

### Backend Setup

```bash
cd backend
pip install fastapi uvicorn groq openpyxl python-dotenv
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:5173`.

---

## Backend API Endpoints

### GET /health

Liveness probe to confirm the API is running.

**Request:** No body required.

**Response:**
```json
{ "status": "ok" }
```

---

### POST /upload

Accept a WhatsApp exported .txt file, run the full agent pipeline, and return structured sales data.

**Request:**
- Content-Type: `multipart/form-data`
- Field: `file` — a `.txt` WhatsApp export file

**Response (200):**
```json
{
  "filename": "chat.txt",
  "sales": [
    {
      "timestamp": "12/31/24, 3:45 PM",
      "sender": "John",
      "product": "Widget A",
      "quantity": 10,
      "unit_price": 5.00,
      "total_price": 50.00,
      "currency": "USD",
      "notes": ""
    }
  ],
  "errors": [
    {
      "record": { "..." : "..." },
      "reason": "Arithmetic mismatch: 3 × 10.0 = 30.0, but total_price = 25.0."
    }
  ],
  "stats": {
    "messages_parsed": 142,
    "candidates_found": 18,
    "valid_sales": 15,
    "flagged_errors": 2
  }
}
```

**Error (400):**
```json
{ "detail": "Only .txt WhatsApp export files are accepted." }
```

---

### POST /export

Generate and download an Excel file from a provided sales array.

**Request:**
- Content-Type: `application/json`
```json
{
  "sales": [ { "timestamp": "...", "sender": "...", "product": "...", ... } ]
}
```

**Response (200):**
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename="sales_export.xlsx"`
- Body: Binary `.xlsx` file stream

**Error (400):**
```json
{ "detail": "No sales data to export." }
```

---

## Agent Descriptions

### Agent 1 — ParserAgent (`agents/parser_agent.py`)

**Purpose:** Convert raw WhatsApp .txt export text into a structured list of message dicts.

**How it works:**
1. Delegates to `parse_chat()` from `parser.py`, which uses a regex (`TIMESTAMP_PATTERN`) to split the text line by line.
2. Multi-line messages are joined into a single text block.
3. System messages (e.g. encryption notices) are tagged `is_system: true`.
4. Returns a list of dicts with keys: `timestamp`, `sender`, `text`, `is_system`.

**Optional method — `classify_messages()`:** Sends a batch of 50 messages to the Groq LLM to classify them as sale-related or not. Used when rule-based pre-filtering produces too many false positives.

---

### Agent 2 — ExtractorAgent (`agents/extractor_agent.py`)

**Purpose:** Extract structured sale records from pre-filtered messages using the Groq LLM.

**How it works:**
1. Applies a regex pre-filter (`extract_sales_candidates()` from `extractor.py`) to discard messages with no price or quantity signals, reducing API cost.
2. Groups remaining candidates into batches of 30.
3. Sends each batch to `qwen/qwen3-32b` with a strict system prompt requesting a JSON array of sale objects.
4. Failed JSON parses are silently skipped; gaps will be surfaced by BugChecker.

**Output fields per sale:** `timestamp`, `sender`, `product`, `quantity`, `unit_price`, `total_price`, `currency`, `notes`.

---

### Agent 3 — ValidatorAgent (`agents/validator_agent.py`)

**Purpose:** Clean, normalise, and validate raw sale records from ExtractorAgent.

**How it works:**
1. `_split()` — partitions records into clean ones and those needing repair. Media-only placeholders are silently discarded.
2. `_coerce_numerics()` — converts string prices (e.g. `"R$12,50"`) to floats.
3. `_is_valid()` — checks that `timestamp`, `sender`, and `product` are all present.
4. `_fix_with_groq()` — sends invalid records to the LLM with a repair prompt: infer missing fields from context, standardise currency to ISO codes, do not invent data.

**Required fields:** `timestamp`, `sender`, `product`

---

### Agent 4 — BugChecker (`agents/bug_checker.py`)

**Purpose:** Scan the full validated sales set for duplicates, arithmetic errors, and anomalies.

**How it works:**
1. **Local checks (no API call):**
   - Discard media-only placeholders.
   - Deduplicate by `(timestamp, sender, product)` key.
   - Flag arithmetic mismatches where `qty × unit_price` diverges from `total_price` by more than 5%; auto-corrects `total_price`.
   - Flag records with a product but no price or quantity.
2. **LLM deep audit:** Sends the cleaned list to Groq to detect cross-record anomalies (price outliers, suspicious duplicates, remaining inconsistencies).
3. Returns a combined `{ sales, errors }` dict.

---

## Frontend Components

### `App.jsx`
Root component. Holds a single `result` state: `null` → shows `UploadPanel`; populated → shows the toolbar, `SalesTable`, and `ExportButton`.

### `Navbar.jsx`
Full-width dark navigation bar with company logo (`assets/logo.jpg`) and application name.

### `UploadPanel.jsx`
Drag-and-drop zone for `.txt` files. Shows an animated progress bar during upload. Calls `POST /upload` via `api/client.js`.

### `SalesTable.jsx`
Renders validated sales in a striped table. Displays a collapsible auditor-issues panel above the table when errors are present.

### `ExportButton.jsx`
Calls `POST /export` and triggers a browser file download of the returned `.xlsx` blob. Disabled and visually muted when no sales are loaded.

### `api/client.js`
Centralised Axios instance pointed at `VITE_API_URL` (default `http://localhost:8000`) with a 2-minute timeout for slow LLM calls. Exports `uploadChat()` and `exportToExcel()`.
