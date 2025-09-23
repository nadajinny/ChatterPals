import os
import asyncio
import subprocess
import shutil
from pathlib import Path
import traceback
from typing import List, Optional
import json

from fastapi import (
    FastAPI, HTTPException, Query, Response, APIRouter, UploadFile, File
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field  # 'pantic' -> 'pydantic' 오타 수정
from dotenv import load_dotenv, find_dotenv
import google.generativeai as genai
import requests

# 기존 ChatterPals 모듈 임포트
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

# --- 환경 변수 및 API 클라이언트 설정 ---
load_dotenv(find_dotenv())
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("'.env' 파일에 GOOGLE_API_KEY가 없습니다.")
genai.configure(api_key=GOOGLE_API_KEY)

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
if not ELEVEN_API_KEY:
    raise RuntimeError("'.env' 파일에 ELEVEN_API_KEY가 없습니다.")

# --- 메인 FastAPI 앱 초기화 ---
app = FastAPI(title="ChatterPals API", version="0.2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================================================================
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 음성 AI 어시스턴트 기능 ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# ===================================================================

voice_router = APIRouter(prefix="/voice", tags=["Voice Assistant"])

MODEL_STT = "gemini-1.5-flash"
MODEL_CHAT = "gemini-1.5-flash"
SYSTEM_PROMPT = "너는 친절하고 상냥한 AI 외국어 교육 어시스턴트야. 발음,회화, 문법등을 대화하면서 도와주는 선생님이지."

def transcode_to_wav_pcm16k(audio_bytes: bytes) -> bytes:
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise FileNotFoundError("FFmpeg가 설치되어 있지 않습니다. 시스템에 FFmpeg를 설치해주세요.")
    command = [
        ffmpeg_path, '-i', 'pipe:0', '-acodec', 'pcm_s16le',
        '-ar', '16000', '-ac', '1', '-f', 'wav', 'pipe:1'
    ]
    process = subprocess.run(command, input=audio_bytes, capture_output=True, check=True)
    return process.stdout

def synthesize_text(text: str) -> bytes:
    voice_id = "EXAVITQu4vr4xnSDxMaL"  # Rachel
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": ELEVEN_API_KEY, "Content-Type": "application/json"}
    payload = {
        "text": text, "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.content

async def stream_text_to_speech_bytes(text: str):
    try:
        audio_data = synthesize_text(text)
        yield audio_data
    except Exception as e:
        print(f"TTS 오류: {e}")
        yield b''

class VoiceTextInput(BaseModel):
    text: str

@voice_router.post("/get-ai-response")
async def get_ai_response(audio: UploadFile = File(...)):
    try:
        converted_audio = transcode_to_wav_pcm16k(await audio.read())
        stt_model = genai.GenerativeModel(MODEL_STT)
        audio_part = genai.protos.Part(inline_data=genai.protos.Blob(mime_type="audio/wav", data=converted_audio))
        stt_prompt = "다음 오디오를 듣고 받아적어 주세요. 인식이 안 되면 '인식 실패'라고 답하세요."
        stt_response = await stt_model.generate_content_async([stt_prompt, audio_part])
        transcript = stt_response.text.strip()
        if not transcript or "인식 실패" in transcript:
            raise ValueError("STT 인식에 실패했습니다.")
        chat_model = genai.GenerativeModel(MODEL_CHAT, system_instruction=SYSTEM_PROMPT)
        llm_response = await chat_model.generate_content_async(transcript)
        response_text = llm_response.text.strip()
        return JSONResponse(content={"transcript": transcript, "response_text": response_text})
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@voice_router.post("/get-ai-response-from-text")
async def get_ai_response_from_text(payload: VoiceTextInput):
    try:
        chat_model = genai.GenerativeModel(MODEL_CHAT, system_instruction=SYSTEM_PROMPT)
        llm_response = await chat_model.generate_content_async(payload.text)
        return JSONResponse(content={"response_text": llm_response.text.strip()})
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@voice_router.get("/tts")
async def tts_streaming_endpoint(text: str = Query(..., min_length=1)):
    return StreamingResponse(stream_text_to_speech_bytes(text), media_type="audio/wav")

app.include_router(voice_router)

@app.get("/voice_ui", response_class=HTMLResponse)
async def get_voice_ui_page():
    html_path = Path(__file__).parent / "voice_ui" / "Text_Audio" / "index.html"
    if not html_path.is_file():
        raise HTTPException(status_code=404, detail="voice_ui/Text_Audio/index.html not found")
    return html_path.read_text(encoding="utf-8")

# ===================================================================
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲ 음성 AI 어시스턴트 기능 끝 ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
# ===================================================================


# --- 기존 ChatterPals API ---
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
            try:
                payload_text, fetched_meta = extract_from_url(req.url.strip())
                meta = {**fetched_meta, "source_url": req.url}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

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
    if req.title: meta["title"] = req.title
    if req.url: meta["url"] = req.url
    if req.language: meta["language"] = req.language
    if req.selection_used is not None: meta["selection_used"] = req.selection_used
    if req.summary: meta["summary"] = req.summary
    if req.topics: meta["topics"] = req.topics

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
            try:
                payload_text, _meta = extract_from_url(req.url.strip())
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        if not payload_text:
            raise HTTPException(status_code=400, detail="토론을 시작할 텍스트가 없습니다. 내용을 직접 선택하거나, 분석 가능한 URL을 사용해 주세요.")

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
        "voice_ui": "GET /voice_ui",
    }

def run(host: str = "0.0.0.0", port: int = 8008):
    import uvicorn
    uvicorn.run("app.server:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    run()

