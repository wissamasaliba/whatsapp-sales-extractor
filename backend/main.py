from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import shutil
import os
import tempfile

from agents.orchestrator import Orchestrator
from excel_writer import write_to_excel

app = FastAPI(title="WhatsApp Sales Extractor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/upload")
async def upload_chat(file: UploadFile = File(...)):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt WhatsApp export files are accepted.")

    contents = await file.read()
    text = contents.decode("utf-8", errors="ignore")

    result = await orchestrator.run(text, filename=file.filename)

    return {"filename": file.filename, "sales": result["sales"], "errors": result.get("errors", [])}


@app.post("/export")
async def export_to_excel(payload: dict):
    sales = payload.get("sales", [])
    if not sales:
        raise HTTPException(status_code=400, detail="No sales data to export.")

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    tmp.close()

    write_to_excel(sales, tmp.name)

    return FileResponse(
        tmp.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="sales_export.xlsx",
    )
