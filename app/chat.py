import uuid
from typing import Dict, List, Optional

from .analyze import analyze
from .records import save_discussion_record


class ChatSession:
    def __init__(self, text: str, max_q: int = 6, *, source_url: str = '', title: str = '', selection_text: str = ''):
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
        self.source_url = source_url
        self.title = title
        self.selection_text = selection_text
        self.record_id: Optional[str] = None

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

    def start(self, text: str, max_q: int = 6, *, source_url: str = '', title: str = '', selection_text: str = '') -> Dict:
        sid = str(uuid.uuid4())
        sess = ChatSession(text=text, max_q=max_q, source_url=source_url, title=title, selection_text=selection_text)
        self.sessions[sid] = sess
        first = sess.first_question()
        sess.history.append({"role": "ai", "content": first})
        record_meta = {
            'title': title,
            'url': source_url,
            'language': sess.result.get('meta', {}).get('language_guess'),
            'summary': sess.result.get('summary'),
            'topics': sess.result.get('topics'),
        }
        record = save_discussion_record(
            history=sess.history,
            initial_questions=sess.questions,
            meta=record_meta,
            source_text=(selection_text or text)[:4000],
            record_id=sess.record_id,
        )
        sess.record_id = record.get('id')
        return {
            "session_id": sid,
            "question": first,
            "meta": {
                "summary": sess.result.get('summary'),
                "topics": sess.result.get('topics'),
                "language_guess": sess.result.get('meta', {}).get('language_guess'),
                "title": title,
                "source_url": source_url,
            },
            "record_id": sess.record_id,
        }

    def reply(self, session_id: str, user_text: str) -> Dict:
        sess = self.sessions.get(session_id)
        if not sess:
            return {"error": "invalid_session"}
        sess.history.append({"role": "user", "content": user_text})
        q = sess.next_question()
        sess.history.append({"role": "ai", "content": q})
        done = q.startswith("Thanks for the discussion")
        record_meta = {
            'title': sess.title,
            'url': sess.source_url,
            'language': sess.result.get('meta', {}).get('language_guess'),
            'summary': sess.result.get('summary'),
            'topics': sess.result.get('topics'),
        }
        record = save_discussion_record(
            history=sess.history,
            initial_questions=sess.questions,
            meta=record_meta,
            source_text=(sess.selection_text or sess.text)[:4000],
            record_id=sess.record_id,
        )
        sess.record_id = record.get('id')
        response = {"question": q, "done": done, "record_id": sess.record_id}
        if done:
            self.sessions.pop(session_id, None)
        return response


MANAGER = ChatManager()
