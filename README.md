ChatterPals-jh — 화면 텍스트 맥락 Q&A (MVP)

개요
- 목표: 화면에 보이는 텍스트(예: 웹 기사)를 입력으로 받아 맥락을 파악하고 핵심 토픽을 식별하여 사용자가 생각을 확장할 수 있도록 “영어 질문”을 생성합니다.
- 범위(MVP): 외부 의존성 없이 로컬에서 동작하는 HTTP 서비스. 텍스트를 받아 요약, 토픽, 질문을 반환합니다. 이후 OCR/웹 추출, LLM 연동으로 확장 가능하도록 설계했습니다.

빠른 시작
- 요구 사항: Python 3.9+
- 서버 실행(권장): 프로젝트 루트에서 `python3 -m app.server`
- 또는(실행 권한 부여 후):
  - `chmod +x app/server.py`
  - 루트에서: `./app/server.py`
  - `app` 폴더에서: `./server.py`
- 텍스트 분석 예시(curl):
  - `curl -s -X POST http://localhost:8008/analyze -H 'Content-Type: application/json' -d '{"text":"Jeonju city hit by heavy rain with widespread damage reported..."}' | jq`
 - 브라우저 테스트 페이지: `http://127.0.0.1:8008/` 접속 후 텍스트 입력 → Analyze

API
- POST `/analyze`
  - 요청 JSON:
    - `text`: string (필수) – 화면에서 추출한 원문 텍스트(기사 전체 또는 선택 영역)
    - `source_url`: string (선택) – 페이지 URL(참고용)
    - `max_questions`: int (선택, 기본 5)
  - 응답 JSON:
    - `summary`: 짧은 요약 문자열
    - `topics`: 핵심 키워드/토픽 문자열 배열
    - `questions`: 텍스트에 맞춘 영어 질문 배열
    - `meta`: 부가 정보(언어 추정, 엔티티 유사 정보, 길이 등)

설계 노트
- 외부 의존성 없음: 불용어/토큰화/빈도 기반의 간단한 휴리스틱으로 오프라인 동작.
- 플러그형 프로바이더: `app/providers.py`에 LLM 교체를 염두에 둔 인터페이스가 있습니다. 나중에 질문/요약 생성을 LLM API로 라우팅 가능.
- 확장 로드맵:
  - 입력: OCR(Tesseract 등) 또는 브라우저 확장으로 가시 텍스트 자동 수집
  - NLP: 휴리스틱 요약 → LLM(`SummaryProvider`), 질문 생성 → LLM(`QuestionProvider`)
  - 다국어: 현재는 질문을 영어로만 생성. 이후 출력 언어 옵션 추가 예정

개발 팁
- 빠른 반복을 위해 `/analyze` 엔드포인트에 원문 텍스트를 바로 POST 하세요.
- 휴리스틱 요약 특성상 1–8K자 정도 분량에서 품질이 더 안정적입니다.

추가 예시
- 브라우저 테스트 페이지: `http://127.0.0.1:8008/` 접속 → 텍스트/URL 입력 후 버튼 클릭
- URL 분석(curl):
  - `curl -s -X POST http://localhost:8008/analyze_url -H 'Content-Type: application/json' -d '{\"url\":\"https://example.com/article\"}' | jq`
- 영어 토론 시작(curl):
  - `curl -s -X POST http://localhost:8008/chat/start -H 'Content-Type: application/json' -d '{\"url\":\"https://example.com/article\"}' | jq`
  - 답변 전송: `curl -s -X POST http://localhost:8008/chat/reply -H 'Content-Type: application/json' -d '{\"session_id\":\"<위 session_id>\", \"answer\":\"I think ...\"}' | jq`

추가 엔드포인트
- POST `/analyze_url`
  - 요청: `{ url: string, max_questions?: number }`
  - 설명: URL에서 텍스트를 추출해 분석 결과 반환

- POST `/chat/start`
  - 요청: `{ text?: string, url?: string, max_questions?: number }`
  - 설명: 영어 토론 세션 시작, 첫 질문과 `session_id` 반환

- POST `/chat/reply`
  - 요청: `{ session_id: string, answer: string }`
  - 설명: 사용자 답변을 받고 다음 영어 질문 반환

브라우저 확장(Chrome, MV3)
- 위치: `ext/chrome`
- 기능: 현재 탭의 선택 텍스트가 있으면 그것을, 없으면 현재 탭 URL을 로컬 서버로 전송
- 제공 버튼:
  - Analyze: `/analyze`(선택 텍스트) 또는 `/analyze_url`(URL)
  - Discuss (EN): `/chat/start`로 토론 세션 시작 → 팝업 내에서 답변/다음 질문 진행
- 서버 주소 입력란: 기본 `http://127.0.0.1:8008` (변경 가능, 동기 저장)

설치 방법
1) 크롬에서 개발자 모드 ON → 확장 프로그램 → 압축해제된 확장 프로그램을 로드
2) 폴더 선택: 이 리포지토리의 `ext/chrome`
3) 로컬 서버 실행: `python3 -m app.server`
4) 아무 페이지나 열고 확장 아이콘 클릭 → Analyze 또는 Discuss (EN)

주의
- 사내 프록시/보안 정책에 따라 `http://127.0.0.1:8008` 접근이 제한될 수 있습니다. 필요 시 `http://localhost:8008`로 바꾸세요(서버는 CORS 허용).
