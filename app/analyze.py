import re
from collections import Counter
from typing import List, Dict, Tuple

from .stopwords import STOPWORDS


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> List[str]:
    # 기본 문장 분리기
    # '.', '!', '?' 기준으로 분리하고 잡음을 최소화합니다.
    chunks = re.split(r"(?<=[.!?])\s+", text.strip())
    return [c.strip() for c in chunks if c and not c.isspace()]


def tokenize(text: str) -> List[str]:
    # 영문 알파벳 기반 토큰 추출(소문자 변환)
    return re.findall(r"[A-Za-z][A-Za-z\-']+", text.lower())


def keyword_counts(text: str, top_k: int = 12) -> List[Tuple[str, int]]:
    tokens = [t for t in tokenize(text) if t not in STOPWORDS and len(t) > 2]
    freq = Counter(tokens)
    return freq.most_common(top_k)


def extract_keywords(text: str, top_k: int = 8) -> List[str]:
    return [w for w, _ in keyword_counts(text, max(top_k * 2, 12))][:top_k]


def guess_language(text: str) -> str:
    # 매우 단순한 판별: 한글 포함 시 'ko', 아니면 'en'
    if re.search(r"[\uac00-\ud7af]", text):
        return 'ko'
    return 'en'


def summarize_text(text: str, max_sentences: int = 2) -> str:
    # 단순 빈도 기반 추출 요약기
    sentences = split_sentences(text)
    if not sentences:
        return _normalize(text[:160])

    freq = dict(keyword_counts(text, top_k=64))
    if not freq:
        return " ".join(sentences[:max_sentences])

    scores: List[Tuple[float, str]] = []
    for s in sentences:
        tokens = tokenize(s)
        if not tokens:
            continue
        score = sum(freq.get(t, 0) for t in tokens) / (len(tokens) + 1e-6)
        scores.append((score, s))

    scores.sort(key=lambda x: x[0], reverse=True)
    selected = [s for _, s in scores[:max_sentences]]
    # 가독성을 위해 원문 순서 유지
    selected_sorted = sorted(selected, key=lambda s: sentences.index(s))
    return _normalize(" ".join(selected_sorted))


def extract_entities_like(text: str) -> Dict[str, List[str]]:
    # 휴리스틱: 대문자로 시작하는 연속 어구를 고유명사 유사 패턴으로 간주, 간단한 장소 단서 포함
    propns = re.findall(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b", text)
    # 흔한 문장 시작어 제거
    common = {"The", "This", "That", "A", "An", "But", "And", "However", "In", "On"}
    propns = [p for p in propns if p.split()[0] not in common]

    # 장소 관련 단서(키워드)
    location_cues = [
        'city', 'province', 'county', 'district', 'state', 'village', 'town', 'island', 'river'
    ]
    locations: List[str] = []
    for m in re.finditer(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(city|province|county|district|state)\b", text):
        locations.append(m.group(0))

    return {
        'proper_nouns': list(dict.fromkeys(propns))[:8],
        'locations': list(dict.fromkeys(locations))[:4],
    }


def generate_questions(topics: List[str], summary: str, entities: Dict[str, List[str]], max_q: int = 5) -> List[str]:
    if not topics and not summary:
        return [
            "What stands out to you about this content?",
            "What key points do you think are most important?",
        ][:max_q]

    topic = topics[0] if topics else "this topic"
    topic2 = topics[1] if len(topics) > 1 else topic
    # 빈 리스트가 존재할 때 get(...)[0]로 접근하면 IndexError가 발생할 수 있으므로 안전 처리
    locs = entities.get('locations') or []
    propns = entities.get('proper_nouns') or []
    location = (locs[0] if len(locs) > 0 else None) or (propns[0] if len(propns) > 0 else None)

    base = []
    base.append(f"How would you summarize the core issue around {topic}?")
    if location:
        base.append(f"What potential impacts could this have on people in {location}?")
    base.append(f"Which evidence in the text supports claims about {topic2}?")
    base.append(f"What are possible solutions or next steps regarding {topic}?")
    base.append(f"What risks or uncertainties remain about {topic} and why?")
    base.append("What is your personal perspective on this situation?")

    # 중복 제거 및 개수 제한
    seen = set()
    deduped = []
    for q in base:
        if q not in seen:
            deduped.append(q)
            seen.add(q)
        if len(deduped) >= max_q:
            break
    return deduped


def analyze(text: str, max_questions: int = 5) -> Dict:
    text = _normalize(text)
    lang = guess_language(text)
    topics = extract_keywords(text, top_k=8)
    summary = summarize_text(text, max_sentences=2)
    entities = extract_entities_like(text)
    questions = generate_questions(topics, summary, entities, max_q=max_questions)

    return {
        'summary': summary,
        'topics': topics,
        'questions': questions,
        'meta': {
            'language_guess': lang,
            'entities': entities,
            'length': len(text),
        }
    }
