# WhatsApp Sales Extractor

Upload a WhatsApp group/chat export (`.txt`) and get back a structured table of
sales records — with a one-click Excel export.

## How it works

```
.txt file → ParserAgent → ExtractorAgent → ValidatorAgent → BugChecker → Excel
```

1. **ParserAgent** — splits the raw export into individual messages.
2. **ExtractorAgent** — uses Groq (`qwen/qwen3-32b`) to identify sale events (product, quantity, price).
3. **ValidatorAgent** — normalises and fills in missing fields (e.g. derives total from unit × qty).
4. **BugChecker** — deduplicates records and flags arithmetic inconsistencies.
5. **Excel export** — downloads a formatted `.xlsx` file.

---

## Project structure

```
Whatsapp/
├── backend/
│   ├── main.py                  # FastAPI app & routes
│   ├── parser.py                # Raw WhatsApp text parser
│   ├── extractor.py             # Rule-based pre-filter + shared Groq client & model
│   ├── excel_writer.py          # openpyxl Excel writer
│   ├── agents/
│   │   ├── orchestrator.py      # Pipeline coordinator
│   │   ├── parser_agent.py      # Message parsing + Groq classification
│   │   ├── extractor_agent.py   # Groq-powered sale extraction
│   │   ├── validator_agent.py   # Data normalisation & Groq repair
│   │   └── bug_checker.py       # Dedup, arithmetic audit, Groq deep-check
│   ├── requirements.txt
│   └── .env                     # GROQ_API_KEY goes here
│
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── api/
│       │   └── client.js        # Axios API client
│       └── components/
│           ├── UploadPanel.jsx  # Drag-and-drop file uploader
│           ├── SalesTable.jsx   # Results table with error summary
│           └── ExportButton.jsx # Triggers Excel download
│
├── chats/                       # Drop your .txt exports here for testing
└── README.md
```

---

## Setup

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Edit `.env` and set your key:
```
GROQ_API_KEY=gsk_...
```

Start the server:
```bash
uvicorn main:app --reload
```

API runs at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

UI runs at `http://localhost:5173`.

---

## Exporting a WhatsApp chat

1. Open the chat in WhatsApp (mobile).
2. Tap ⋮ → **More** → **Export chat** → **Without media**.
3. Save the `.txt` file and drop it into the upload panel (or into `chats/`).

---

## Environment variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API key (backend `.env`) — get one at console.groq.com |
| `VITE_API_URL` | Backend base URL for the frontend (default: `http://localhost:8000`) |
