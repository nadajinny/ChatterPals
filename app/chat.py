import uuid
from typing import Dict, List

from .analyze import analyze


class ChatSession:
    def __init__(self, text: str, max_q: int = 6):
        self.text = text
        self.result = analyze(text, max_questions=max_q)
        self.questions: List[str] = list(self.result.get('questions', []))
        # 후속 질문 템플릿(간단)
        self.followups = [
            "What trade-offs do you see here, and why?",
            "What additional data would strengthen your viewpoint?",
            "How does this relate to similar events or trends?",
            "If you were in charge, what would you prioritize first?",
            "What are possible unintended consequences to consider?",
        ]
        self.q_index = 0
        self.history: List[Dict] = []  # {role: 'user'|'ai', content: str}

    def first_question(self) -> str:
        if self.questions:
            return self.questions[0]
        return "What stands out to you about this content?"

    def next_question(self) -> str:
        self.q_index += 1
        if self.q_index < len(self.questions):
            return self.questions[self.q_index]
        # 없으면 followup에서 제공
        idx = self.q_index - len(self.questions)
        if idx < len(self.followups):
            return self.followups[idx]
        # 종료 멘트
        return "Thanks for the discussion. Any final thoughts?"


class ChatManager:
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}

    def start(self, text: str, max_q: int = 6) -> Dict:
        sid = str(uuid.uuid4())
        sess = ChatSession(text=text, max_q=max_q)
        self.sessions[sid] = sess
        first = sess.first_question()
        sess.history.append({"role": "ai", "content": first})
        return {
            "session_id": sid,
            "question": first,
            "meta": {
                "summary": sess.result.get('summary'),
                "topics": sess.result.get('topics'),
                "language_guess": sess.result.get('meta', {}).get('language_guess'),
            },
        }

    def reply(self, session_id: str, user_text: str) -> Dict:
        sess = self.sessions.get(session_id)
        if not sess:
            return {"error": "invalid_session"}
        sess.history.append({"role": "user", "content": user_text})
        q = sess.next_question()
        sess.history.append({"role": "ai", "content": q})
        done = q.startswith("Thanks for the discussion")
        return {"question": q, "done": done}


MANAGER = ChatManager()

