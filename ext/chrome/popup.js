const qs = (id) => document.getElementById(id);

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function getSelectionText(tabId) {
  try {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId },
      func: () => window.getSelection ? (window.getSelection().toString() || '') : ''
    });
    return result || '';
  } catch (e) {
    return '';
  }
}

async function jsonFetch(url, obj) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(obj || {})
  });
  const text = await res.text();
  try { return JSON.parse(text); } catch { return { error: 'non_json', raw: text, status: res.status }; }
}

function setResult(obj) {
  qs('result').textContent = typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2);
}

document.addEventListener('DOMContentLoaded', async () => {
  const saved = await chrome.storage.sync.get(['server']);
  if (saved.server) qs('server').value = saved.server;

  qs('server').addEventListener('change', (e) => {
    chrome.storage.sync.set({ server: e.target.value.trim() });
  });

  qs('analyze').addEventListener('click', async () => {
    setResult('Analyzing...');
    const server = qs('server').value.trim();
    const maxq = parseInt(qs('maxq').value || '5', 10);
    const tab = await getActiveTab();
    const sel = await getSelectionText(tab.id);
    try {
      if (sel && sel.length > 20) {
        const res = await jsonFetch(`${server}/analyze`, { text: sel, max_questions: maxq });
        setResult(res);
      } else {
        const res = await jsonFetch(`${server}/analyze_url`, { url: tab.url, max_questions: maxq });
        setResult(res);
      }
    } catch (e) {
      setResult({ error: String(e) });
    }
  });

  let sessionId = null;

  qs('chatStart').addEventListener('click', async () => {
    setResult('Starting discussion...');
    const server = qs('server').value.trim();
    const maxq = parseInt(qs('maxq').value || '6', 10);
    const tab = await getActiveTab();
    const sel = await getSelectionText(tab.id);
    try {
      const payload = sel && sel.length > 20 ? { text: sel, max_questions: maxq } : { url: tab.url, max_questions: maxq };
      const res = await jsonFetch(`${server}/chat/start`, payload);
      setResult(res);
      if (res.session_id) {
        sessionId = res.session_id;
        qs('chat').style.display = 'block';
        qs('sid').textContent = sessionId;
        qs('q').textContent = res.question || '(none)';
        qs('answer').focus();
      }
    } catch (e) {
      setResult({ error: String(e) });
    }
  });

  qs('send').addEventListener('click', async () => {
    const server = qs('server').value.trim();
    const answer = qs('answer').value.trim();
    if (!sessionId) { setResult({ error: 'no_session' }); return; }
    setResult('Sending answer...');
    try {
      const res = await jsonFetch(`${server}/chat/reply`, { session_id: sessionId, answer });
      setResult(res);
      if (res.question) {
        qs('q').textContent = res.question;
        qs('answer').value = '';
        if (res.done) {
          qs('send').disabled = true;
          qs('answer').disabled = true;
        }
      }
    } catch (e) {
      setResult({ error: String(e) });
    }
  });
});

