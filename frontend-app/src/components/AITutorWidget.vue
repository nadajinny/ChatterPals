<template>
  <div class="ai-tutor-widget">
    <!-- 채팅 메시지가 표시되는 영역 -->
    <div class="chat-history" ref="chatHistoryEl">
      <div v-for="(msg, index) in messages" :key="index" :class="['chat-message', msg.role]">
        <div class="message-content">
          <p>{{ msg.text }}</p>
          <!-- AI 메시지이고 오디오 URL이 있을 경우 플레이어 표시 -->
          <div v-if="msg.role === 'ai' && msg.audioUrl" class="audio-player">
            <button @click="playAudio(msg.audioUrl, index)" class="play-pause-btn" aria-label="재생">
              <svg v-if="currentlyPlayingIndex !== index" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg>
            </button>
          </div>
        </div>
      </div>
      <div v-if="isProcessingAudio || isProcessingText" class="chat-message ai">
          <div class="message-content thinking">...</div>
      </div>
    </div>

    <!-- 입력 영역 -->
    <div class="chat-input-area">
      <textarea
        v-model="inputText"
        @keydown.enter.prevent="handleSendMessage"
        placeholder="메시지를 입력하거나 마이크를 누르세요..."
        rows="1"
        ref="textareaEl"
      ></textarea>
      <button @click="handleSendMessage" :disabled="!inputText.trim() || isProcessingAudio || isProcessingText">전송</button>
      <button @click="toggleRecording" :disabled="isProcessingText" class="mic-btn">
        {{ isRecording ? '🔴' : '🎤' }}
      </button>
    </div>
    
    <!-- 오디오 재생을 위한 숨겨진 태그 -->
    <audio ref="audioPlayer" style="display: none;"></audio>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import * as api from '@/services/api';

interface Message {
  role: 'user' | 'ai';
  text: string;
  audioUrl?: string;
}

// --- 상태 변수 ---
const messages = ref<Message[]>([]);
const inputText = ref('');
const isRecording = ref(false);
const isProcessingAudio = ref(false);
const isProcessingText = ref(false);

const audioPlayer = ref<HTMLAudioElement | null>(null);
const currentlyPlayingIndex = ref<number | null>(null);

const chatHistoryEl = ref<HTMLElement | null>(null);
const textareaEl = ref<HTMLTextAreaElement | null>(null);

let mediaRecorder: MediaRecorder | null = null;
let audioChunks: Blob[] = [];

// --- 메시지 처리 함수 ---

// 텍스트 메시지 전송
async function handleSendMessage() {
  const text = inputText.value.trim();
  if (!text || isProcessingAudio.value || isProcessingText.value) return;

  messages.value.push({ role: 'user', text });
  inputText.value = '';
  isProcessingText.value = true;
  
  try {
    const result = await api.getResponseFromText(text);
    await processAiResponse(result.response_text);
  } catch (error) {
    console.error("텍스트 응답 처리 중 오류:", error);
    messages.value.push({ role: 'ai', text: '오류가 발생했습니다. 다시 시도해주세요.' });
  } finally {
    isProcessingText.value = false;
  }
}

// 음성 녹음 토글
async function toggleRecording() {
  if (isRecording.value) {
    mediaRecorder?.stop();
  } else {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];
      mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);
      mediaRecorder.onstop = handleAudioProcessing;
      mediaRecorder.start();
      isRecording.value = true;
    } catch (error) {
      console.error('마이크 접근 오류:', error);
      alert('마이크를 사용할 수 없습니다.');
    }
  }
}

// 녹음된 오디오 처리
async function handleAudioProcessing() {
  isRecording.value = false;
  isProcessingAudio.value = true;
  const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

  try {
    const result = await api.getResponseFromAudio(audioBlob);
    messages.value.push({ role: 'user', text: `"${result.transcript}"` });
    await processAiResponse(result.response_text);
  } catch (error) {
    console.error("음성 응답 처리 중 오류:", error);
    messages.value.push({ role: 'ai', text: '오류가 발생했습니다. 다시 시도해주세요.' });
  } finally {
    isProcessingAudio.value = false;
  }
}

// 공통 AI 응답 처리 (텍스트 + TTS)
async function processAiResponse(text: string) {
  const ttsAudioBlob = await api.getTtsAudio(text);
  const audioUrl = URL.createObjectURL(ttsAudioBlob);
  
  // AI 메시지를 화면에 추가합니다. (음성 자동 재생은 하지 않습니다)
  messages.value.push({ role: 'ai', text, audioUrl });
}

// --- 오디오 플레이어 제어 ---
function playAudio(url: string, index: number) {
  if (!audioPlayer.value) return;

  if (currentlyPlayingIndex.value === index) {
    audioPlayer.value.pause();
    currentlyPlayingIndex.value = null;
  } else {
    audioPlayer.value.src = url;
    audioPlayer.value.play();
    currentlyPlayingIndex.value = index;
  }
  
  audioPlayer.value.onended = () => {
    currentlyPlayingIndex.value = null;
  };
}


// --- UI/UX 개선 ---

// 채팅창 자동 스크롤
watch(messages, () => {
  nextTick(() => {
    if(chatHistoryEl.value) {
      chatHistoryEl.value.scrollTop = chatHistoryEl.value.scrollHeight;
    }
  });
}, { deep: true });

// 텍스트 입력창 높이 자동 조절
watch(inputText, () => {
    if (!textareaEl.value) return;
    textareaEl.value.style.height = 'auto';
    textareaEl.value.style.height = `${textareaEl.value.scrollHeight}px`;
});
</script>

<style scoped>
.ai-tutor-widget {
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(140, 149, 159, 0.2);
  width: 100%;
  max-width: 600px;
  height: 70vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #d0d7de;
}

.chat-history {
  flex-grow: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-message {
  display: flex;
  max-width: 80%;
}

.chat-message.user {
  align-self: flex-end;
}
.chat-message.ai {
  align-self: flex-start;
}

.message-content {
  padding: 10px 15px;
  border-radius: 18px;
  position: relative;
}
.chat-message.user .message-content {
  background-color: #007aff;
  color: white;
  border-bottom-right-radius: 4px;
}
.chat-message.ai .message-content {
  background-color: #f0f0f0;
  color: #24292f;
  border-bottom-left-radius: 4px;
}
.message-content p {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.5;
}
.message-content.thinking {
  padding: 10px 15px;
  background-color: #f0f0f0;
  color: #57606a;
  border-radius: 18px;
}

.audio-player {
  margin-top: 8px;
}
.play-pause-btn {
  width: 30px; height: 30px; padding: 0;
  border: none; background-color: rgba(255,255,255,0.3);
  border-radius: 50%; cursor: pointer; color: #24292f;
  display: flex; align-items: center; justify-content: center;
}
.play-pause-btn svg { width: 16px; height: 16px; }

.chat-input-area {
  display: flex;
  padding: 10px;
  border-top: 1px solid #d0d7de;
  gap: 8px;
  align-items: flex-end;
}
textarea {
  flex-grow: 1;
  border: 1px solid #d0d7de;
  border-radius: 20px;
  padding: 10px 15px;
  font-size: 15px;
  line-height: 1.4;
  resize: none;
  max-height: 100px;
  overflow-y: auto;
  font-family: inherit;
}
.chat-input-area button {
  border-radius: 50%;
  width: 40px;
  height: 40px;
  padding: 0;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.mic-btn { font-size: 1.2rem; }
</style>

