import os
import traceback
import json #
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv, find_dotenv
import google.generativeai as genai

# --- 로컬 모듈 임포트 ---
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

# --- FastAPI 앱 초기화 ---
app = FastAPI(title="ChatterPals Text API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic 데이터 모델 정의 ---
class QuestionsRequest(BaseModel):
    text: Optional[str] = None
    max_questions: int = Field(5, ge=1, le=20)

class QuestionAnswerItem(BaseModel):
    question: str
    answer: str = ""

class SaveQuestionsRequest(BaseModel):
    items: List[QuestionAnswerItem]
    summary: Optional[str] = None
    topics: Optional[List[str]] = None
    selection_text: Optional[str] = Field(None, max_length=4000)

# --- 신규 평가 기능 모델 추가 ---
class EvaluationRequest(BaseModel):
    items: List[QuestionAnswerItem]

class EvaluationScores(BaseModel):
    grammar: int
    vocabulary: int
    clarity: int

class EvaluationResult(BaseModel):
    scores: EvaluationScores
    feedback: str

class EvaluatedItem(BaseModel):
    question: str
    answer: str
    evaluation: EvaluationResult

class SaveEvaluationRequest(BaseModel):
    summary: str
    topics: List[str]
    items: List[EvaluatedItem]
    source_text: str

class ChatStartRequest(BaseModel):
    text: str
    max_questions: int = Field(6, ge=1, le=20)

class ChatReplyRequest(BaseModel):
    session_id: str
    answer: str

# --- API 엔드포인트 ---
@app.get("/")
def get_status():
    return {"status": "Text server is running"}

@app.post("/questions")
def post_questions(req: QuestionsRequest):
    try:
        return analyze((req.text or "").strip(), max_questions=req.max_questions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# ✅ [신규] 답변 평가 API
EVALUATION_MODEL = "gemini-1.5-flash"
EVALUATION_PROMPT_TEMPLATE = """
    당신은 외국어 학습자의 답변을 평가하는 AI 선생님입니다. 다음은 학생이 질문에 대해 작성한 답변입니다.
    - 질문: "{question}"
    - 학생 답변: "{answer}"
    아래의 세 가지 기준에 따라 답변을 평가하고, 각 항목별 점수(1~5점)와 구체적인 서술형 피드백을 JSON 형식으로 반환해 주세요.
    1.  **문법 및 정확성 (Grammar & Accuracy):** 문법 오류, 단어 선택의 정확성 평가
    2.  **어휘 사용 (Vocabulary Usage):** 사용된 어휘의 수준과 다양성 평가
    3.  **논리 및 명확성 (Clarity & Coherence):** 답변의 구조적 논리성과 명확성 평가
    피드백은 칭찬과 개선점을 모두 포함하고, 해당 사항을 반영한 예시 답변도 반환하여 주세요. 분량은 공백 포함 400자 이내로 제한하여 대답합니다.
    JSON 출력 예시: {{"scores": {{"grammar": 4, "vocabulary": 3, "clarity": 5}}, "feedback": "문법적으로는 훌륭하지만..."}}
    """

@app.post("/evaluate/answers", tags=["Answer Evaluation"])
async def evaluate_answers(req: EvaluationRequest):
    try:
        model = genai.GenerativeModel(EVALUATION_MODEL)
        evaluations = []
        for item in req.items:
            if not item.answer or not item.answer.strip():
                evaluations.append({
                    "question": item.question, "answer": item.answer,
                    "evaluation": {"scores": {"grammar": 0, "vocabulary": 0, "clarity": 0}, "feedback": "답변이 입력되지 않았습니다."}
                })
                continue

            prompt = EVALUATION_PROMPT_TEMPLATE.format(question=item.question, answer=item.answer)
            response = await model.generate_content_async(prompt)
            # AI 응답에서 JSON 부분만 깔끔하게 추출
            cleaned_json_str = response.text.strip().replace('```json', '').replace('```', '').strip()
            evaluation_data = json.loads(cleaned_json_str)
            evaluations.append({"question": item.question, "answer": item.answer, "evaluation": evaluation_data})
        return {"evaluations": evaluations}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"답변 평가 중 오류가 발생했습니다: {e}")

# ✅ [신규] 평가 결과 저장 API
@app.post("/records/save_evaluation", tags=["Records"])
def save_evaluated_record(req: SaveEvaluationRequest):
    try:
        # Pydantic 모델을 Python 딕셔너리로 변환
        items_to_save = [item.dict() for item in req.items]
        meta = {"summary": req.summary, "topics": req.topics}
        
        # records.py의 save_questions_record 함수를 evaluation_results와 함께 호출
        saved_record = save_questions_record(
            items=items_to_save,
            meta=meta,
            source_text=req.source_text,
            evaluation_results={"evaluations": items_to_save} # 평가 결과를 함께 저장
        )
        return saved_record
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"평가 기록 저장 실패: {e}")


@app.post("/records/questions")
def post_save_questions(req: SaveQuestionsRequest):
    try:
        items_serialized = [item.model_dump() for item in req.items]
        meta = {"summary": req.summary, "topics": req.topics}
        record = save_questions_record(
            items_serialized,
            meta,
            source_text=(req.selection_text or "").strip(),
        )
        return {"record_id": record.get("id"), "created_at": record.get("created_at")}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to save record.")

@app.post("/chat/start")
def post_chat_start(req: ChatStartRequest):
    try:
        return CHAT_MANAGER.start(req.text, max_q=req.max_questions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/reply")
def post_chat_reply(req: ChatReplyRequest):
    try:
        result = CHAT_MANAGER.reply(req.session_id.strip(), req.answer.strip())
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/records")
def get_records_list(date: Optional[str] = Query(None, description="YYYY-MM-DD filter")):
    try:
        return {"records": list_records(date=date)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/records/{record_id}")
def get_record_details(record_id: str):
    record = get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@app.get("/records/{record_id}.pdf")
def get_record_as_pdf(record_id: str):
    record = get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    pdf_bytes = record_to_pdf(record)
    return Response(content=pdf_bytes, media_type="application/pdf")


# --- 서버 실행 ---
def run(host: str = "0.0.0.0", port: int = 8008):
    import uvicorn
    print(f"Starting Text Server on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=True)

if __name__ == "__main__":
    run()