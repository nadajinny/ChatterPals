#!/usr/bin/env python3
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

try:
    # 권장: 패키지 모듈 방식으로 실행 (python -m app.server)
    from .analyze import analyze
except Exception:
    # 대안: 스크립트를 직접 실행해도 동작하도록 처리 (python app/server.py 또는 ./server.py)
    import os, sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from app.analyze import analyze
    from app.extract import extract_from_url
    from app.chat import MANAGER as CHAT_MANAGER
else:
    # 패키지 임포트 성공 시
    from .extract import extract_from_url
    from .chat import MANAGER as CHAT_MANAGER


class Handler(BaseHTTPRequestHandler):
    def _send_body(self, code: int, body: bytes, content_type: str):
        self.send_response(code)
        # CORS 허용(로컬 테스트 및 브라우저 확장 대비)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _send(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self._send_body(code, body, 'application/json; charset=utf-8')

    def do_POST(self):
        if self.path == '/analyze':
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                self._send(411, {'error': 'Content-Length required'})
                return

            data = self.rfile.read(length) if length > 0 else b''
            try:
                req = json.loads(data.decode('utf-8')) if data else {}
            except Exception:
                self._send(400, {'error': 'Invalid JSON'})
                return

            text = (req.get('text') or '').strip()
            max_q = req.get('max_questions') or 5
            if not text:
                self._send(400, {'error': 'Missing required field: text'})
                return

            try:
                result = analyze(text, max_questions=int(max_q))
                self._send(200, result)
            except Exception as e:
                self._send(500, {'error': 'Internal error', 'detail': str(e)})
            return

        if self.path == '/analyze_url':
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                self._send(411, {'error': 'Content-Length required'})
                return

            data = self.rfile.read(length) if length > 0 else b''
            try:
                req = json.loads(data.decode('utf-8')) if data else {}
            except Exception:
                self._send(400, {'error': 'Invalid JSON'})
                return

            url = (req.get('url') or '').strip()
            max_q = req.get('max_questions') or 5
            if not url:
                self._send(400, {'error': 'Missing required field: url'})
                return

            try:
                text, meta = extract_from_url(url)
                result = analyze(text, max_questions=int(max_q))
                result['meta'] = {**result.get('meta', {}), **meta, 'source_url': url}
                self._send(200, result)
            except Exception as e:
                self._send(500, {'error': 'fetch_or_analyze_failed', 'detail': str(e)})
            return

        if self.path == '/chat/start':
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                self._send(411, {'error': 'Content-Length required'})
                return
            data = self.rfile.read(length) if length > 0 else b''
            try:
                req = json.loads(data.decode('utf-8')) if data else {}
            except Exception:
                self._send(400, {'error': 'Invalid JSON'})
                return

            text = (req.get('text') or '').strip()
            url = (req.get('url') or '').strip()
            max_q = req.get('max_questions') or 6
            try:
                if not text and url:
                    text, _meta = extract_from_url(url)
                if not text:
                    self._send(400, {'error': 'Missing text or url'})
                    return
                started = CHAT_MANAGER.start(text, max_q=int(max_q))
                self._send(200, started)
            except Exception as e:
                self._send(500, {'error': 'chat_start_failed', 'detail': str(e)})
            return

        if self.path == '/chat/reply':
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                self._send(411, {'error': 'Content-Length required'})
                return
            data = self.rfile.read(length) if length > 0 else b''
            try:
                req = json.loads(data.decode('utf-8')) if data else {}
            except Exception:
                self._send(400, {'error': 'Invalid JSON'})
                return
            session_id = (req.get('session_id') or '').strip()
            answer = (req.get('answer') or '').strip()
            if not session_id:
                self._send(400, {'error': 'Missing session_id'})
                return
            try:
                out = CHAT_MANAGER.reply(session_id, answer)
                self._send(200, out)
            except Exception as e:
                self._send(500, {'error': 'chat_reply_failed', 'detail': str(e)})
            return

        self._send(404, {'error': 'Not found'})

        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            self._send(411, {'error': 'Content-Length required'})
            return

        data = self.rfile.read(length) if length > 0 else b''
        try:
            req = json.loads(data.decode('utf-8')) if data else {}
        except Exception:
            self._send(400, {'error': 'Invalid JSON'})
            return

        text = (req.get('text') or '').strip()
        max_q = req.get('max_questions') or 5
        if not text:
            self._send(400, {'error': 'Missing required field: text'})
            return

        try:
            result = analyze(text, max_questions=int(max_q))
            self._send(200, result)
        except Exception as e:
            self._send(500, {'error': 'Internal error', 'detail': str(e)})

    def do_GET(self):
        if self.path == '/':
            # 간단한 테스트 페이지(텍스트 입력 → /analyze 호출)
            html = (
                """
                <!doctype html>
                <html lang="ko">
                <head>
                  <meta charset="utf-8" />
                  <meta name="viewport" content="width=device-width, initial-scale=1" />
                  <title>ChatterPals-jh · Analyze</title>
                  <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 24px; }
                    textarea { width: 100%; height: 180px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
                    pre { background: #f6f8fa; padding: 12px; overflow: auto; }
                    .row { margin-bottom: 12px; }
                    input[type=text] { width: 100%; }
                    .buttons { display: flex; gap: 8px; align-items: center; }
                  </style>
                </head>
                <body>
                  <h1>화면 텍스트 분석 (MVP)</h1>
                  <div class="row">
                    <label>텍스트</label><br />
                    <textarea id="text" placeholder="여기에 기사/텍스트를 붙여넣으세요"></textarea>
                  </div>
                  <div class="row">
                    <label>URL</label><br/>
                    <input id="url" type="text" placeholder="https://..." />
                  </div>
                  <div class="row">
                    <label>max_questions</label>
                    <input id="maxq" type="number" value="5" min="1" max="10" />
                    <span class="buttons">
                      <button id="run">텍스트 분석</button>
                      <button id="runUrl">URL 분석</button>
                      <button id="chatStart">영어 토론 시작</button>
                    </span>
                  </div>
                  <pre id="out">결과가 여기에 표시됩니다.</pre>

                  <div id="chatPanel" style="margin-top:16px; padding-top:12px; border-top:1px solid #ddd; display:none;">
                    <div><strong>Chat session</strong>: <code id="sid">-</code></div>
                    <div style="margin-top:8px;">AI 질문: <span id="q">(없음)</span></div>
                    <div class="row" style="margin-top:8px;">
                      <input id="answer" type="text" placeholder="영어로 답변 입력" />
                      <button id="send">Send</button>
                    </div>
                  </div>

                  <script>
                    const $ = (id) => document.getElementById(id);
                    async function jsonFetch(path, obj) {
                      const res = await fetch(path, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(obj || {})
                      });
                      const text = await res.text();
                      try { return JSON.parse(text); } catch { return { error: 'non_json', raw: text, status: res.status }; }
                    }
                    $('run').addEventListener('click', async () => {
                      const text = $('text').value.trim();
                      const maxq = parseInt($('maxq').value || '5', 10);
                      $('out').textContent = '요청 중...';
                      try {
                        const res = await fetch('/analyze', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ text, max_questions: maxq })
                        });
                        const data = await res.json();
                        $('out').textContent = JSON.stringify(data, null, 2);
                      } catch (e) {
                        $('out').textContent = '오류: ' + e;
                      }
                    });

                    $('runUrl').addEventListener('click', async () => {
                      const url = $('url').value.trim();
                      const maxq = parseInt($('maxq').value || '5', 10);
                      $('out').textContent = 'URL 가져오는 중...';
                      try {
                        const res = await fetch('/analyze_url', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ url, max_questions: maxq })
                        });
                        const data = await res.json();
                        $('out').textContent = JSON.stringify(data, null, 2);
                      } catch (e) {
                        $('out').textContent = '오류: ' + e;
                      }
                    });

                    $('chatStart').addEventListener('click', async () => {
                      const text = $('text').value.trim();
                      const url = $('url').value.trim();
                      const maxq = parseInt($('maxq').value || '6', 10);
                      $('out').textContent = '세션 시작 중...';
                      try {
                        const data = await jsonFetch('/chat/start', { text, url, max_questions: maxq });
                        $('out').textContent = JSON.stringify(data, null, 2);
                        if (data.session_id) {
                          $('chatPanel').style.display = 'block';
                          $('sid').textContent = data.session_id;
                          $('q').textContent = data.question || '(none)';
                          $('answer').focus();
                        }
                      } catch (e) {
                        $('out').textContent = '오류: ' + e;
                      }
                    });

                    $('send').addEventListener('click', async () => {
                      const session_id = $('sid').textContent;
                      const answer = $('answer').value.trim();
                      if (!session_id || session_id === '-') { alert('세션 없음'); return; }
                      $('out').textContent = '응답 전송 중...';
                      try {
                        const data = await jsonFetch('/chat/reply', { session_id, answer });
                        $('out').textContent = JSON.stringify(data, null, 2);
                        if (data.question) {
                          $('q').textContent = data.question;
                          $('answer').value = '';
                          if (data.done) {
                            $('send').disabled = true;
                            $('answer').disabled = true;
                          }
                        }
                      } catch (e) {
                        $('out').textContent = '오류: ' + e;
                      }
                    });
                  </script>
                </body>
                </html>
                """
            ).encode('utf-8')
            self._send_body(200, html, 'text/html; charset=utf-8')
            return

        if self.path == '/favicon.ico':
            # 파비콘 없음 → 본문 없이 204
            self._send_body(204, b'', 'image/x-icon')
            return

        self._send(404, {'error': 'Not found'})

    def do_OPTIONS(self):
        # CORS preflight 허용
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def run(host: str = '127.0.0.1', port: int = 8008):
    httpd = HTTPServer((host, port), Handler)
    print(f"[analyze] listening on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == '__main__':
    run()
