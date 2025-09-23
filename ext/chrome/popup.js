// frontend.js
// ============================================================================
// ChatterPals Extension Frontend Script
// - Handles text analysis (selection & full page), Q/A session management,
//   chat discussion flow, and voice input/output with AI response playback.
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  // --------------------------------------------------------------------------
  // UI ELEMENT REFERENCES
  // --------------------------------------------------------------------------
  const serverInput   = document.getElementById('server');
  const maxqInput     = document.getElementById('maxq');
  const questionBtn   = document.getElementById('question');     // Selection-based analysis
  const analyzeAllBtn = document.getElementById('analyzeAll');   // Full-page analysis
  const saveQABtn     = document.getElementById('saveQA');
  const chatStartBtn  = document.getElementById('chatStart');
  const resultDiv     = document.getElementById('result');
  const questionsDiv  = document.getElementById('questions');
  const chatDiv       = document.getElementById('chat');
  const sidSpan       = document.getElementById('sid');
  const qSpan         = document.getElementById('q');
  const answerInput   = document.getElementById('answer');
  const sendBtn       = document.getElementById('send');
  const recordBtn     = document.getElementById('recordBtn');
  const voiceStatusEl = document.getElementById('voiceStatus');
  const transcriptEl  = document.getElementById('transcript');
  const voiceAnswerEl = document.getElementById('voiceAnswer');
  const audioPlayer   = document.getElementById('audioPlayer');

  // --------------------------------------------------------------------------
  // STATE VARIABLES
  // --------------------------------------------------------------------------
  let currentQuestions = [];
  let currentMeta = {};
  let mediaRecorder, audioChunks = [];

  // --------------------------------------------------------------------------
  // UTILITY: Normalize Question Object into Text
  // Ensures safe string extraction from various AI response formats
  // --------------------------------------------------------------------------
  function extractQuestionText(q) {
    if (typeof q === 'string') return q.trim();
    if (q && typeof q === 'object') {
      const candidates = ['question', 'text', 'prompt', 'content', 'title', 'q'];
      for (const key of candidates) {
        if (typeof q[key] === 'string' && q[key].trim()) return q[key].trim();
      }
      if (Array.isArray(q.messages)) {
        const m = q.messages.find(m => typeof m.content === 'string' && m.content.trim());
        if (m) return m.content.trim();
      }
      return JSON.stringify(q);
    }
    return '';
  }

  // --------------------------------------------------------------------------
  // UTILITY: Extract summary string from result panel
  // --------------------------------------------------------------------------
  function extractSummaryFromResult() {
    const t = (resultDiv.textContent || '').trim();
    return t.startsWith('요약: ') ? t.slice(4).trim() : t;
  }

  // --------------------------------------------------------------------------
  // RENDER: Display generated questions and attach editable answers
  // --------------------------------------------------------------------------
  function displayQuestions(questions, meta) {
    questionsDiv.innerHTML = '';
    currentQuestions = questions || [];
    currentMeta = meta || {};

    if (!questions || questions.length === 0) {
      questionsDiv.innerHTML = '<div class="question-empty">생성된 질문이 없습니다.</div>';
      saveQABtn.disabled = true;
      return;
    }

    questions.forEach((q, index) => {
      const questionText = extractQuestionText(q);
      const item = document.createElement('div');
      item.className = 'question-item';
      item.innerHTML = `
        <div class="question-text">${index + 1}. ${questionText}</div>
        <textarea class="question-answer" data-index="${index}" placeholder="답변을 입력하세요..."></textarea>
      `;
      questionsDiv.appendChild(item);
    });

    saveQABtn.disabled = false;
  }

  // --------------------------------------------------------------------------
  // API WRAPPER: Unified fetch call with error handling
  // --------------------------------------------------------------------------
  async function apiCall(endpoint, body) {
    const server = serverInput.value.trim();
    if (!server) {
      resultDiv.textContent = 'Error: 서버 주소를 입력하세요.';
      throw new Error('서버 주소 없음');
    }
    try {
      const response = await fetch(`${server}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || `HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      resultDiv.textContent = `Error: ${error.message}`;
      throw error;
    }
  }

  // --------------------------------------------------------------------------
  // CORE: Generate questions based on input text
  // --------------------------------------------------------------------------
  function generateQuestions(text, url, title) {
    if (!text || text.trim().length === 0) {
      resultDiv.textContent = '분석할 텍스트가 없습니다. 웹페이지에서 텍스트를 선택하거나 전체 분석을 사용하세요.';
      return;
    }
    resultDiv.textContent = 'AI가 텍스트를 분석하고 있습니다...';
    questionsDiv.innerHTML = '';
    saveQABtn.disabled = true;
    chatStartBtn.disabled = true;

    const max_questions = parseInt(maxqInput.value, 10);
    const body = { text, url, title, max_questions };

    apiCall('/questions', body).then(data => {
      resultDiv.textContent = `요약: ${data.summary || '없음'}`;
      displayQuestions(data.questions, data.meta);
      chatStartBtn.disabled = !data.questions || data.questions.length === 0;
    }).catch(() => {});
  }

  // --------------------------------------------------------------------------
  // EVENT: Selection-based analysis
  // --------------------------------------------------------------------------
  questionBtn.addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs && tabs.length > 0) {
        chrome.scripting.executeScript({
          target: { tabId: tabs[0].id },
          function: () => window.getSelection().toString(),
        }, (injectionResults) => {
          if (chrome.runtime.lastError) {
            console.error(chrome.runtime.lastError);
            resultDiv.textContent = 'Error: 현재 페이지의 텍스트를 가져올 수 없습니다.';
            return;
          }
          const selection = injectionResults[0].result;
          generateQuestions(selection, tabs[0].url, tabs[0].title);
        });
      }
    });
  });

  // --------------------------------------------------------------------------
  // EVENT: Full-page analysis
  // --------------------------------------------------------------------------
  if (analyzeAllBtn) {
    analyzeAllBtn.addEventListener('click', () => {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs && tabs.length > 0) {
          chrome.scripting.executeScript({
            target: { tabId: tabs[0].id },
            function: () => {
              const pick = (...sels) => sels.map(s => document.querySelector(s)).find(Boolean);
              const node = pick('article','main','[role="main"]','#content','.post','.article','.readable','.entry','.markdown-body') || document.body;
              const textFrom = (el) => (el && (el.innerText || el.textContent) || '').trim();
              let text = textFrom(node);
              if (text.length < 400) text = textFrom(document.body);
              return text.replace(/\s+\n/g, '\n').replace(/\n{3,}/g, '\n\n');
            }
          }, (injectionResults) => {
            if (chrome.runtime.lastError) {
              console.error(chrome.runtime.lastError);
              resultDiv.textContent = 'Error: 페이지 텍스트를 가져올 수 없습니다.';
              return;
            }
            const fullText = injectionResults[0].result || '';
            generateQuestions(fullText, tabs[0].url, tabs[0].title);
          });
        }
      });
    });
  }

  // --------------------------------------------------------------------------
  // EVENT: Save Q/A results
  // --------------------------------------------------------------------------
  saveQABtn.addEventListener('click', () => {
    const answers = Array.from(questionsDiv.querySelectorAll('.question-answer')).map(t => t.value);
    const items = (currentQuestions || []).map((q, i) => {
      const questionText = extractQuestionText(q);
      return { question: questionText, answer: answers[i] || '' };
    });
    const body = {
      items: items, meta: currentMeta,
      summary: extractSummaryFromResult(),
      topics: currentMeta.topics
    };
    resultDiv.textContent = 'Saving...';
    apiCall('/records/questions', body).then(data => {
      resultDiv.textContent = `저장 완료! (ID: ${data.record_id})`;
    }).catch(() => {});
  });

  // --------------------------------------------------------------------------
  // EVENT: Start chat session
  // --------------------------------------------------------------------------
  chatStartBtn.addEventListener('click', () => {
    const summary = extractSummaryFromResult();
    if (!summary) {
      resultDiv.textContent = 'Error: 채팅을 시작할 요약 내용이 없습니다.';
      return;
    }
    const body = {
      text: summary, url: currentMeta.source_url || currentMeta.url,
      title: currentMeta.title, max_questions: 6
    };
    resultDiv.textContent = 'Starting chat session...';
    apiCall('/chat/start', body).then(data => {
      sidSpan.textContent = data.session_id;
      qSpan.textContent = extractQuestionText(data.question) || '(질문 없음)';
      chatDiv.style.display = 'block';
      resultDiv.textContent = 'Chat started.';
    }).catch(() => {});
  });

  // --------------------------------------------------------------------------
  // EVENT: Send chat answer
  // --------------------------------------------------------------------------
  sendBtn.addEventListener('click', () => {
    const answer = answerInput.value.trim();
    if (!answer || sendBtn.disabled) return;
    const body = { session_id: sidSpan.textContent, answer };
    answerInput.disabled = true;
    sendBtn.disabled = true;
    apiCall('/chat/reply', body).then(data => {
      const nextQ = extractQuestionText(data.question);
      qSpan.textContent = nextQ || '(질문 수신 실패)';
      if (data.is_last) {
        qSpan.textContent += "\n(마지막 질문입니다)";
        sendBtn.disabled = true;
      } else {
        answerInput.value = '';
      }
    }).catch(err => { qSpan.textContent = `Error: ${err.message}`; })
    .finally(() => {
      if (!sendBtn.disabled) answerInput.disabled = false;
    });
  });

  // --------------------------------------------------------------------------
  // EVENT: Voice recording start/stop
  // --------------------------------------------------------------------------
  recordBtn.addEventListener('click', async () => {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunks = [];
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
        mediaRecorder.onstop = () => {
          recordBtn.textContent = "🎤 말하기 시작";
          voiceStatusEl.textContent = "처리 중...";
          handleVoiceStop();
        };
        mediaRecorder.start();
        recordBtn.textContent = "🛑 말하기 중지";
        voiceStatusEl.textContent = "듣고 있어요...";
      } catch (err) {
        voiceStatusEl.textContent = "오류: 마이크 접근 권한이 필요합니다.";
      }
    }
  });

  // --------------------------------------------------------------------------
  // VOICE: Handle audio after recording stop
  // --------------------------------------------------------------------------
  async function handleVoiceStop() {
    const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm"); // Server expects "audio"

    try {
      const server = serverInput.value.trim();
      const response = await fetch(`${server}/voice/get-ai-response`, { method: "POST", body: formData });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || `HTTP ${response.status}`);
      }
      const json = await response.json();
      transcriptEl.textContent = "🗣️ 내 질문: " + json.transcript;
      voiceAnswerEl.textContent = "💬 AI 답변: " + json.response_text;

      // Request AI response as speech
      const ttsResponse = await fetch(`${server}/voice/tts?text=${encodeURIComponent(json.response_text)}`);
      if (!ttsResponse.ok) throw new Error("TTS 오디오 생성 실패");
      const audioData = await ttsResponse.blob();
      audioPlayer.src = URL.createObjectURL(audioData);
      audioPlayer.style.display = 'block';
      audioPlayer.play();
      voiceStatusEl.textContent = "완료";
    } catch (err) {
      voiceStatusEl.textContent = `오류: ${err.message}`;
    }
  }

  // --------------------------------------------------------------------------
  // INITIALIZATION: Context-specific setup
  // --------------------------------------------------------------------------
  function initializeForSidebar() {
    resultDiv.textContent = '궁금한 내용을 드래그하거나, 음성으로 질문해보세요!';
    window.addEventListener('message', (event) => {
      if (event.data && event.data.type === 'CHATTERPALS_TEXT_SELECTION') {
        const { text, url, title } = event.data;
        generateQuestions(text, url, title);
      }
    });
  }

  function initializeForPopup() {
    chrome.storage.local.get('contextData', (result) => {
      if (result.contextData) {
        const { text, url, title } = result.contextData;
        chrome.storage.local.remove('contextData');
        generateQuestions(text, url, title);
      } else {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          if (tabs && tabs.length > 0) {
            chrome.scripting.executeScript({
              target: { tabId: tabs[0].id },
              function: () => window.getSelection().toString(),
            }, (injectionResults) => {
              if (!chrome.runtime.lastError && injectionResults && injectionResults[0].result) {
                const selection = injectionResults[0].result;
                if (selection.trim().length > 0) {
                  generateQuestions(selection, tabs[0].url, tabs[0].title);
                }
              }
            });
          }
        });
      }
    });
  }

  // --------------------------------------------------------------------------
  // ENTRY POINT
  // --------------------------------------------------------------------------
  const urlParams = new URLSearchParams(window.location.search);
  const context = urlParams.get('context');
  if (context === 'sidebar') {
    initializeForSidebar();
  } else {
    initializeForPopup();
  }
});
