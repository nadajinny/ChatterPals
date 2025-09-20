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

let questionSaveBtn = null;
let currentQuestions = [];
let currentMeta = null;
let currentSummary = '';
let currentTopics = [];
let currentContext = null;

function resetQuestionState() {
  currentQuestions = [];
  currentMeta = null;
  currentSummary = '';
  currentTopics = [];
  currentContext = null;
  if (questionSaveBtn) questionSaveBtn.disabled = true;
}

function renderQuestions(questions, { placeholder } = {}) {
  const container = qs('questions');
  container.innerHTML = '';
  const list = Array.isArray(questions) ? [...questions] : [];
  if (!list.length) {
    if (placeholder) {
      const empty = document.createElement('div');
      empty.className = 'question-empty';
      empty.textContent = placeholder;
      container.appendChild(empty);
    }
    if (questionSaveBtn) questionSaveBtn.disabled = true;
    return;
  }

  currentQuestions = list;
  if (questionSaveBtn) questionSaveBtn.disabled = false;

  list.forEach((question, idx) => {
    const wrapper = document.createElement('div');
    wrapper.className = 'question-item';

    const qText = document.createElement('div');
    qText.className = 'question-text';
    qText.textContent = `${idx + 1}. ${question}`;

    const textarea = document.createElement('textarea');
    textarea.className = 'question-answer';
    textarea.rows = 3;
    textarea.placeholder = '답변을 입력하세요';

    wrapper.appendChild(qText);
    wrapper.appendChild(textarea);
    container.appendChild(wrapper);
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  const saved = await chrome.storage.sync.get(['server']);
  if (saved.server) qs('server').value = saved.server;

  questionSaveBtn = qs('saveQA');
  renderQuestions([], { placeholder: '질문이 생성되면 여기에 표시됩니다.' });

  qs('server').addEventListener('change', (e) => {
    chrome.storage.sync.set({ server: e.target.value.trim() });
  });

  qs('question').addEventListener('click', async () => {
    setResult('질문을 생성 중입니다...');
    resetQuestionState();
    renderQuestions([], { placeholder: '질문을 준비하고 있어요.' });
    const server = qs('server').value.trim();
    const maxq = parseInt(qs('maxq').value || '5', 10);
    const tab = await getActiveTab();
    const sel = await getSelectionText(tab.id);
    try {
      const payload = { max_questions: maxq };
      if (sel && sel.length > 20) {
        payload.text = sel;
      } else {
        payload.url = tab.url;
      }
      payload.title = tab.title || '';
      const res = await jsonFetch(`${server}/questions`, payload);
      if (res && Array.isArray(res.questions)) {
        if (res.questions.length) {
          renderQuestions(res.questions);
          currentMeta = res.meta || {};
          currentSummary = res.summary || currentMeta.summary || '';
          currentTopics = Array.isArray(res.topics) ? res.topics : currentMeta.topics || [];
          if (currentSummary && !currentMeta.summary) currentMeta.summary = currentSummary;
          if (currentTopics.length && !currentMeta.topics) currentMeta.topics = currentTopics;
          if (currentMeta.language_guess && !currentMeta.language) {
            currentMeta.language = currentMeta.language_guess;
          }
          currentContext = {
            url: tab.url,
            title: tab.title || '',
            selectionUsed: Boolean(payload.text),
            selectionText: payload.text ? sel : '',
          };
          setResult('생성된 질문에 답변을 입력해보세요.');
        } else {
          renderQuestions([], { placeholder: '생성된 질문이 없습니다.' });
          setResult('질문을 만들지 못했습니다.');
        }
      } else {
        renderQuestions([], { placeholder: '결과를 표시할 수 없습니다.' });
        setResult(res);
      }
    } catch (e) {
      setResult({ error: String(e) });
      renderQuestions([], { placeholder: '문제가 발생했습니다. 다시 시도해 주세요.' });
    }
  });

  if (questionSaveBtn) {
    questionSaveBtn.addEventListener('click', async () => {
      if (!currentQuestions.length) {
        setResult('저장할 질문이 없습니다.');
        return;
      }

      const server = qs('server').value.trim();
      const answerEls = Array.from(qs('questions').querySelectorAll('.question-answer'));
      const answers = answerEls.map((el) => el.value.trim());
      const items = currentQuestions.map((question, idx) => ({
        question,
        answer: answers[idx] || '',
      }));

      const selectionText = currentContext?.selectionText || '';
      const payload = {
        items,
        meta: currentMeta || {},
        summary: currentSummary,
        topics: currentTopics,
        url: currentContext?.url || '',
        title: currentContext?.title || '',
        selection_used: currentContext?.selectionUsed || false,
        selection_text: selectionText ? selectionText.slice(0, 4000) : '',
        language: currentMeta?.language || currentMeta?.language_guess || '',
      };

      setResult('기록을 저장 중입니다...');
      questionSaveBtn.disabled = true;
      try {
        const res = await jsonFetch(`${server}/records/questions`, payload);
        if (res && res.record_id) {
          setResult(`기록이 저장되었습니다. ID: ${res.record_id}`);
        } else {
          setResult(res);
        }
      } catch (e) {
        setResult({ error: String(e) });
      } finally {
        if (currentQuestions.length) {
          questionSaveBtn.disabled = false;
        }
      }
    });
  }

  let sessionId = null;

  qs('chatStart').addEventListener('click', async () => {
    setResult('Starting discussion...');
    const server = qs('server').value.trim();
    const maxq = parseInt(qs('maxq').value || '6', 10);
    const tab = await getActiveTab();
    const sel = await getSelectionText(tab.id);
    try {
      const payload = sel && sel.length > 20 ? { text: sel, max_questions: maxq } : { url: tab.url, max_questions: maxq };
      payload.title = tab.title || '';
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
          if (res.record_id) {
            setResult(`토론이 종료되고 기록(ID: ${res.record_id})이 저장되었습니다.`);
          }
        }
      }
    } catch (e) {
      setResult({ error: String(e) });
    }
  });
});
