import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import io

from backend.analytics import get_data_info, get_stats, get_plots
from backend.chatbot import datasets, chat as chatbot_chat

app = FastAPI(title="CSV Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    data_id: str
    message: str
    history: list = []


@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    data_id = str(uuid.uuid4())
    info = get_data_info(df)
    stats = get_stats(df)
    plots, corr_matrix = get_plots(df)
    datasets[data_id] = {
        "df": df,
        "filename": file.filename,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "info": info,
        "stats": stats,
        "plots": plots,
        "correlation_matrix_base64": corr_matrix,
    }
    return {
        "data_id": data_id,
        "filename": file.filename,
        "rows": info["rows"],
        "columns": info["columns"],
        "dtypes": info["dtypes"],
    }


@app.get("/api/data/{data_id}/info")
async def data_info(data_id: str):
    if data_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    ds = datasets[data_id]
    return {
        "data_id": data_id,
        "filename": ds["filename"],
        "rows": ds["info"]["rows"],
        "columns": ds["info"]["columns"],
        "dtypes": ds["info"]["dtypes"],
        "missing": ds["info"]["missing"],
        "preview": ds["info"]["preview"],
    }


@app.get("/api/data/{data_id}/stats")
async def data_stats(data_id: str):
    if data_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    ds = datasets[data_id]
    return {
        "data_id": data_id,
        "numeric": ds["stats"]["numeric"],
        "categorical": ds["stats"]["categorical"],
        "correlations": ds["stats"]["correlations"],
    }


@app.get("/api/data/{data_id}/plots")
async def data_plots(
    data_id: str,
    columns: Optional[str] = Query(None),
):
    if data_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    ds = datasets[data_id]
    if columns:
        col_list = [c.strip() for c in columns.split(",")]
        plots = [p for p in ds["plots"] if p["column"] in col_list]
    else:
        plots = ds["plots"]
    return {
        "data_id": data_id,
        "plots": plots,
        "correlation_matrix_base64": ds.get("correlation_matrix_base64"),
    }


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if req.data_id not in datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    result = chatbot_chat(req.message, req.history, req.data_id)
    return result


@app.get("/api/uploads")
async def list_uploads():
    uploads = []
    for data_id, ds in datasets.items():
        uploads.append({
            "data_id": data_id,
            "filename": ds["filename"],
            "uploaded_at": ds["uploaded_at"],
        })
    return {"uploads": uploads}
