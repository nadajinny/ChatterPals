import re
from collections import Counter
from typing import List, Dict, Tuple

from .stopwords import STOPWORDS

KO_STOPWORDS = {
    '그리고', '그러나', '하지만', '그러면서', '그러니까', '그는', '그녀는', '그들이', '그가',
    '그녀가', '그동안', '이번', '지난', '또한', '또', '다만', '이미', '여전히', '가장', '정도',
    '위해', '위해서', '대한', '대한민국', '에서는', '에서', '으로', '으로써', '으로서', '부터',
    '까지', '통해', '관련', '관해', '관한', '대해', '대해서', '등', '등의', '등을', '등이',
    '등도', '등과', '때문', '때문에', '이날', '이후', '이전', '이상', '이하', '이외', '이렇게',
    '이같이', '이같은', '이처럼', '이에', '이는', '이와', '있다', '있어', '있는', '있으며',
    '없다', '없어', '없이', '했다', '하며', '한다고', '밝혔다', '말했다', '전했다', '지적했다',
    '언급했다', '강조했다', '설명했다', '이라며', '이라고', '라는', '지난해', '오는', '오늘',
    '내일', '오전', '오후', '기자', '연합뉴스', '뉴스', '사진', '제공'
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> List[str]:
    # 기본 문장 분리기
    # '.', '!', '?' 기준으로 분리하고 잡음을 최소화합니다.
    chunks = re.split(r"(?<=[.!?])\s+", text.strip())
    return [c.strip() for c in chunks if c and not c.isspace()]


def tokenize(text: str, lang: str = 'en') -> List[str]:
    # 영문 알파벳 기반 토큰 추출(소문자 변환)
    tokens = re.findall(r"[A-Za-z][A-Za-z\-']+", text.lower())
    if lang == 'ko':
        # 한글 음절 기반 토큰 추가(길이 2 이상)
        tokens += re.findall(r"[\uac00-\ud7af]{2,}", text)
    return tokens


def keyword_counts(text: str, top_k: int = 12, lang: str = 'en') -> List[Tuple[str, int]]:
    tokens = tokenize(text, lang=lang)
    if lang == 'ko':
        stopwords = STOPWORDS | KO_STOPWORDS
        filtered = [t for t in tokens if t not in stopwords and len(t) > 1]
    else:
        filtered = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    freq = Counter(filtered)
    return freq.most_common(top_k)


def extract_keywords(text: str, top_k: int = 8, lang: str = 'en') -> List[str]:
    return [w for w, _ in keyword_counts(text, max(top_k * 2, 12), lang=lang)][:top_k]


def guess_language(text: str) -> str:
    # 매우 단순한 판별: 한글 포함 시 'ko', 아니면 'en'
    if re.search(r"[\uac00-\ud7af]", text):
        return 'ko'
    return 'en'


def summarize_text(text: str, max_sentences: int = 2, lang: str = 'en') -> str:
    # 단순 빈도 기반 추출 요약기
    sentences = split_sentences(text)
    if not sentences:
        return _normalize(text[:160])

    freq = dict(keyword_counts(text, top_k=64, lang=lang))
    if not freq:
        return " ".join(sentences[:max_sentences])

    scores: List[Tuple[float, str]] = []
    for s in sentences:
        tokens = tokenize(s, lang=lang)
        if not tokens:
            continue
        score = sum(freq.get(t, 0) for t in tokens) / (len(tokens) + 1e-6)
        scores.append((score, s))

    scores.sort(key=lambda x: x[0], reverse=True)
    selected = [s for _, s in scores[:max_sentences]]
    # 가독성을 위해 원문 순서 유지
    selected_sorted = sorted(selected, key=lambda s: sentences.index(s))
    return _normalize(" ".join(selected_sorted))


def extract_entities_like(text: str, lang: str = 'en') -> Dict[str, List[str]]:
    # 휴리스틱: 대문자로 시작하는 연속 어구를 고유명사 유사 패턴으로 간주, 간단한 장소 단서 포함
    if lang == 'ko':
        tokens = [t for t, _ in keyword_counts(text, top_k=32, lang=lang)]
        propns = [t for t in tokens if len(t) > 1 and t not in KO_STOPWORDS]
        locations: List[str] = []
        for m in re.finditer(r"([\uac00-\ud7af]{2,})(시|도|군|구|읍|면|동|리)", text):
            locations.append("".join(m.groups()))
        return {
            'proper_nouns': propns[:8],
            'locations': list(dict.fromkeys(locations))[:4],
        }
    propns = re.findall(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b", text)
    # 흔한 문장 시작어 제거
    common = {"The", "This", "That", "A", "An", "But", "And", "However", "In", "On"}
    propns = [p for p in propns if p.split()[0] not in common]

    locations: List[str] = []
    for m in re.finditer(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(city|province|county|district|state)\b", text):
        locations.append(m.group(0))

    return {
        'proper_nouns': list(dict.fromkeys(propns))[:8],
        'locations': list(dict.fromkeys(locations))[:4],
    }


def generate_questions(topics: List[str], summary: str, entities: Dict[str, List[str]], max_q: int = 5, lang: str = 'en') -> List[str]:
    if not topics and summary:
        summary_tokens = tokenize(summary, lang=lang)
        if lang == 'ko':
            stopwords = STOPWORDS | KO_STOPWORDS
            summary_tokens = [t for t in summary_tokens if t not in stopwords and len(t) > 1]
        else:
            summary_tokens = [t for t in summary_tokens if t not in STOPWORDS and len(t) > 2]
        counts = Counter(summary_tokens)
        if counts:
            topics = [w for w, _ in counts.most_common(2)]
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
    topics = extract_keywords(text, top_k=8, lang=lang)
    summary = summarize_text(text, max_sentences=2, lang=lang)
    entities = extract_entities_like(text, lang=lang)
    questions = generate_questions(topics, summary, entities, max_q=max_questions, lang=lang)

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
