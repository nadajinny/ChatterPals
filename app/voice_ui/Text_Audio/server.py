import os
import io
import asyncio
import subprocess
import shutil
from pathlib import Path
from contextlib import asynccontextmanager
import traceback
import uvicorn

from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv, find_dotenv

import google.generativeai as genai
import requests
from pydantic import BaseModel

# --- 환경 변수 로딩 ---
# 이 파일의 상위 디렉토리들에서 .env 파일을 찾습니다. (프로젝트 루트에 위치해야 함)
load_dotenv(find_dotenv())
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("'.env' 파일에 GOOGLE_API_KEY가 없습니다.")

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
if not ELEVEN_API_KEY:
    raise RuntimeError("'.env' 파일에 ELEVEN_API_KEY가 없습니다.")


# --- 모델 설정 ---
# 유효한 모델명으로 수정합니다.
MODEL_STT = "gemini-1.5-flash"
MODEL_CHAT = "gemini-1.5-flash"
API_TIMEOUT = 150.0
SYSTEM_PROMPT = "너는 친절하고 상냥한 AI 외국어 교육 어시스턴트야. 발음,회화, 문법등을 대화하면서 도와주는 선생님이지."

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Gemini API 클라이언트 초기화")
    genai.configure(api_key=API_KEY)
    yield
    print("서버 종료")

app = FastAPI(lifespan=lifespan)

# --- 미들웨어 설정 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 모든 출처 허용
    allow_credentials=True,
    allow_methods=["*"], # 모든 HTTP 메소드 허용
    allow_headers=["*"]  # 모든 헤더 허용
)

# --- 정적 파일 제공 ---
STATIC_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_file_path = STATIC_DIR / "index.html"
    if html_file_path.is_file():
        return HTMLResponse(content=html_file_path.read_text(encoding="utf-8"))
    raise HTTPException(status_code=404, detail="index.html not found")

# --- Helper Functions ---
def transcode_to_wav_pcm16k(audio_bytes: bytes) -> bytes:
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise FileNotFoundError("FFmpeg가 설치되어 있지 않습니다. 시스템에 FFmpeg를 설치해주세요.")
    command = [
        ffmpeg_path,
        '-i', 'pipe:0',
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        '-f', 'wav',
        'pipe:1'
    ]
    process = subprocess.run(command, input=audio_bytes, capture_output=True, check=True)
    return process.stdout

def synthesize_text(text: str) -> bytes:
    voice_id = "EXAVITQu4vr4xnSDxMaL"  # Rachel
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": ELEVEN_API_KEY, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status() # 오류 발생 시 예외를 발생시킴
    return response.content

async def stream_text_to_speech_bytes(text: str):
    try:
        print(f"[TTS] '{text[:30]}...' 음성 합성 중...")
        audio_data = synthesize_text(text)
        print("[TTS] 생성 완료")
        yield audio_data
    except Exception as e:
        print(f"TTS 오류: {e}")
        yield b''

# --- API Endpoints ---
@app.post("/api/get-ai-response")
async def get_ai_response(audio: UploadFile = File(...)):
    try:
        print("[1/3] 오디오 변환 중...")
        input_audio_bytes = await audio.read()
        converted_audio = transcode_to_wav_pcm16k(input_audio_bytes)
        print("[1/3] 변환 완료")

        print("[2/3] STT 실행 중...")
        stt_model = genai.GenerativeModel(MODEL_STT)
        audio_part = genai.protos.Part(inline_data=genai.protos.Blob(mime_type="audio/wav", data=converted_audio))
        stt_prompt = "다음 오디오를 듣고 받아적어 주세요. 인식이 안 되면 '인식 실패'라고 답하세요."
        stt_response = await asyncio.wait_for(
            stt_model.generate_content_async([stt_prompt, audio_part]), timeout=API_TIMEOUT
        )
        transcript = stt_response.text.strip()
        print(f"[2/3] STT 결과: {transcript}")

        if not transcript or "인식 실패" in transcript:
            raise ValueError("STT 인식에 실패했습니다.")

        print("[3/3] Gemini 응답 생성 중...")
        chat_model = genai.GenerativeModel(MODEL_CHAT, system_instruction=SYSTEM_PROMPT)
        llm_response = await asyncio.wait_for(
            chat_model.generate_content_async(transcript), timeout=API_TIMEOUT
        )
        response_text = llm_response.text.strip()
        print(f"[3/3] Gemini 응답: {response_text}")

        return JSONResponse(content={"transcript": transcript, "response_text": response_text})
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class TextInput(BaseModel):
    text: str

@app.post("/api/get-ai-response-from-text")
async def get_ai_response_from_text(payload: TextInput):
    try:
        print(f"[텍스트 입력] Gemini 요청: {payload.text}")
        chat_model = genai.GenerativeModel(MODEL_CHAT, system_instruction=SYSTEM_PROMPT)
        llm_response = await asyncio.wait_for(
            chat_model.generate_content_async(payload.text), timeout=API_TIMEOUT
        )
        response_text = llm_response.text.strip()
        print(f"[텍스트 입력] Gemini 응답: {response_text}")
        return JSONResponse(content={"response_text": response_text})
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tts")
async def tts_streaming_endpoint(text: str = Query(..., min_length=1)):
    return StreamingResponse(stream_text_to_speech_bytes(text), media_type="audio/wav")

# --- 서버 직접 실행 ---
if __name__ == "__main__":
    print("Voice UI 서버를 http://127.0.0.1:8001 에서 시작합니다.")
    uvicorn.run(app, host="0.0.0.0", port=8001)
