import json
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .analyze import analyze
from .chat import MANAGER as CHAT_MANAGER
from .extract import extract_from_url
from .records import (
    get_record,
    list_records,
    record_to_pdf,
    records_to_pdf,
    save_questions_record,
)


app = FastAPI(title="ChatterPals API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="Input text to analyze")
    max_questions: int = Field(5, ge=1, le=20)


class AnalyzeUrlRequest(BaseModel):
    url: str = Field(..., description="Source URL to fetch")
    max_questions: int = Field(5, ge=1, le=20)


class QuestionsRequest(BaseModel):
    text: Optional[str] = Field(None, description="Selected text content")
    url: Optional[str] = Field(None, description="Fallback URL to fetch")
    title: Optional[str] = Field(None, description="Page title")
    max_questions: int = Field(5, ge=1, le=20)


class QuestionAnswerItem(BaseModel):
    question: str
    answer: str = ""


class SaveQuestionsRequest(BaseModel):
    items: Optional[List[QuestionAnswerItem]] = None
    questions: Optional[List[str]] = None
    answers: Optional[List[str]] = None
    meta: Optional[dict] = None
    title: Optional[str] = None
    url: Optional[str] = None
    summary: Optional[str] = None
    topics: Optional[List[str]] = None
    language: Optional[str] = None
    selection_used: Optional[bool] = None
    selection_text: Optional[str] = Field(None, max_length=4000)


class ChatStartRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    max_questions: int = Field(6, ge=1, le=20)


class ChatReplyRequest(BaseModel):
    session_id: str
    answer: str


@app.post("/analyze")
def post_analyze(req: AnalyzeRequest):
    try:
        result = analyze(req.text.strip(), max_questions=req.max_questions)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return result


@app.post("/analyze_url")
def post_analyze_url(req: AnalyzeUrlRequest):
    try:
        text, meta = extract_from_url(req.url.strip())
        result = analyze(text, max_questions=req.max_questions)
        result["meta"] = {**result.get("meta", {}), **meta, "source_url": req.url}
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/questions")
def post_questions(req: QuestionsRequest):
    payload_text = (req.text or "").strip()
    max_q = req.max_questions
    meta = {}
    try:
        if not payload_text:
            if not req.url:
                raise HTTPException(status_code=400, detail="Missing text or url")
            payload_text, fetched_meta = extract_from_url(req.url.strip())
            meta = {**fetched_meta, "source_url": req.url}

        analysis = analyze(payload_text, max_questions=max_q)
        questions = analysis.get("questions", [])
        meta = {**analysis.get("meta", {}), **meta}
        meta["selection_used"] = bool(req.text)
        if req.title:
            meta["title"] = req.title
        if analysis.get("summary"):
            meta.setdefault("summary", analysis["summary"])
        if analysis.get("topics"):
            meta.setdefault("topics", analysis["topics"])

        response = {
            "questions": questions,
            "summary": analysis.get("summary"),
            "topics": analysis.get("topics"),
            "meta": meta,
        }
        return response
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/records/questions")
def post_save_questions(req: SaveQuestionsRequest):
    items: List[QuestionAnswerItem] = req.items or []
    if not items and req.questions:
        for idx, question in enumerate(req.questions):
            answer = ""
            if req.answers and idx < len(req.answers):
                answer = req.answers[idx]
            if question:
                items.append(QuestionAnswerItem(question=question, answer=answer))

    if not items:
        raise HTTPException(status_code=400, detail="Missing items to save")

    meta = req.meta or {}
    if req.title:
        meta["title"] = req.title
    if req.url:
        meta["url"] = req.url
    if req.language:
        meta["language"] = req.language
    if req.selection_used is not None:
        meta["selection_used"] = req.selection_used
    if req.summary:
        meta["summary"] = req.summary
    if req.topics:
        meta["topics"] = req.topics

    items_serialized = [item.model_dump() for item in items]

    try:
        record = save_questions_record(
            items_serialized,
            meta,
            source_text=(req.selection_text or "").strip(),
        )
        return {"record_id": record.get("id"), "created_at": record.get("created_at")}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/chat/start")
def post_chat_start(req: ChatStartRequest):
    payload_text = (req.text or "").strip()
    try:
        if not payload_text and req.url:
            payload_text, _meta = extract_from_url(req.url.strip())
        if not payload_text:
            raise HTTPException(status_code=400, detail="Missing text or url")

        started = CHAT_MANAGER.start(
            payload_text,
            max_q=req.max_questions,
            source_url=req.url or "",
            title=req.title or "",
            selection_text=req.text or "",
        )
        return started
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/chat/reply")
def post_chat_reply(req: ChatReplyRequest):
    try:
        result = CHAT_MANAGER.reply(req.session_id.strip(), req.answer.strip())
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/records")
def get_records(date: Optional[str] = Query(None, description="YYYY-MM-DD filter")):
    try:
        records = list_records(date=date)
        return {"records": records}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/records/export.pdf")
def get_records_export(ids: List[str] = Query(..., alias="ids")):
    try:
        record_ids: List[str] = []
        for value in ids:
            record_ids.extend([v.strip() for v in value.split(",") if v.strip()])
        if not record_ids:
            raise ValueError
        pdf_bytes = records_to_pdf(record_ids)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except ValueError:
        raise HTTPException(status_code=404, detail="records_not_found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/records/{record_id}.pdf")
def get_record_pdf(record_id: str):
    record = get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="record_not_found")
    try:
        pdf_bytes = record_to_pdf(record)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/records/{record_id}")
def get_record_json(record_id: str):
    record = get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="record_not_found")
    return record


@app.get("/")
def get_root():
    return {
        "message": "ChatterPals API",
        "endpoints": [
            "POST /analyze",
            "POST /analyze_url",
            "POST /questions",
            "POST /records/questions",
            "POST /chat/start",
            "POST /chat/reply",
            "GET /records",
            "GET /records/{id}",
            "GET /records/{id}.pdf",
            "GET /records/export.pdf",
        ],
    }


def run(host: str = "0.0.0.0", port: int = 8008):
    import uvicorn

    uvicorn.run("app.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run()
