import re
from html.parser import HTMLParser
from urllib import request, error
from typing import Tuple, Dict


UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _decode_best(data: bytes, content_type: str = "") -> Tuple[str, str]:
    """Try to decode bytes → str using likely encodings.
    Returns (text, encoding).
    """
    charset = None
    if content_type:
        m = re.search(r"charset=([^;]+)", content_type, re.I)
        if m:
            charset = m.group(1).strip().lower()
    candidates = []
    if charset:
        candidates.append(charset)
    candidates += ["utf-8", "euc-kr", "cp949", "latin-1"]
    for enc in candidates:
        try:
            return data.decode(enc), enc
        except Exception:
            continue
    return data.decode("utf-8", errors="ignore"), "utf-8"


def fetch_url(url: str, timeout: float = 10.0) -> Tuple[str, Dict]:
    """Fetch URL and return HTML string and meta info."""
    req = request.Request(url, headers={"User-Agent": UA})
    with request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        ctype = resp.headers.get("Content-Type", "")
        text, enc = _decode_best(raw, ctype)
        return text, {
            "final_url": getattr(resp, 'url', url),
            "status": resp.status,
            "content_type": ctype,
            "encoding": enc,
            "length": len(text),
        }


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._texts = []
        self._skip = 0  # inside script/style/noscript

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):  # skip content
            self._skip += 1
        elif tag in ("p", "br", "div", "section", "article", "li", "h1", "h2", "h3", "h4"):
            self._texts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip > 0:
            self._skip -= 1
        elif tag in ("p", "div", "section", "article", "li"):
            self._texts.append("\n")

    def handle_data(self, data):
        if self._skip:
            return
        if data and not data.isspace():
            self._texts.append(data)

    def text(self) -> str:
        joined = "".join(self._texts)
        # collapse whitespace
        joined = re.sub(r"\s+", " ", joined)
        # restore simple newlines around periods to help sentence splitters
        joined = re.sub(r"\s*\.(\s+)", ". \\1", joined)
        return joined.strip()


def html_to_text(html: str, max_chars: int = 30000) -> str:
    parser = _TextExtractor()
    # limit input size to protect memory
    html = html[: max_chars * 4]
    parser.feed(html)
    return parser.text()[:max_chars]


def extract_from_url(url: str, timeout: float = 10.0) -> Tuple[str, Dict]:
    html, meta = fetch_url(url, timeout=timeout)
    text = html_to_text(html)
    meta = {**meta, "extracted_chars": len(text)}
    return text, meta

