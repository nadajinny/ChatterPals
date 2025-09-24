<!-- src/views/Settings.vue -->
<template>
  <main class="settings">
    <!-- 상단 히어로 -->
    <header class="page-hero" aria-labelledby="settings-title">
      <h1 id="settings-title">학습 방법 설정하기</h1>
      <p class="subtitle">Hey there, fill out this form</p>
    </header>

    <!-- 옵션 2열 (둘 중 하나만 선택: 라디오) -->
    <section class="options" aria-label="학습 옵션">
      <div class="option">
        <h2 class="label">DEBATE WITH AI</h2>
        <label class="checkbox">
          <input type="radio" name="studyMode" value="debate" v-model="form.mode" />
          <span>선택</span>
        </label>
        <p class="hint">토론 기능이 어떤 식의 대화로 이루어지는지, 예시</p>

        <textarea
          class="textarea"
          rows="8"
          placeholder="Enter your message"
          v-model="form.debateMsg"
        ></textarea>
      </div>

      <div class="option">
        <h2 class="label">EXPRESS IDEA</h2>
        <label class="checkbox">
          <input type="radio" name="studyMode" value="express" v-model="form.mode" />
          <span>선택</span>
        </label>
        <p class="hint">설명 기능이 어떤 식의 대화로 이루어지는지, 예시</p>

        <textarea
          class="textarea"
          rows="8"
          placeholder="Enter your message"
          v-model="form.expressMsg"
        ></textarea>
      </div>
    </section>

    <!-- ✅ 추가: 튜터 캐릭터 설정하기 -->
    <section class="tutor" aria-labelledby="tutor-title">
      <h2 id="tutor-title" class="tutor-title">튜터 캐릭터 설정하기</h2>
      <p class="subtitle">Hey there, fill out this form</p>

      <div class="tutor-grid">
        <!-- 왼쪽: 동물 종류 (라디오: 하나만 선택) -->
        <div class="tutor-block">
          <h3 class="label">캐릭터 동물 종류</h3>
          <div class="radio-group">
            <label class="radio">
              <input type="radio" name="animal" value="cat" v-model="form.animal" />
              <span>Cat</span>
            </label>
            <label class="radio">
              <input type="radio" name="animal" value="dog" v-model="form.animal" />
              <span>Dog</span>
            </label>
            <label class="radio">
              <input type="radio" name="animal" value="fox" v-model="form.animal" />
              <span>Fox</span>
            </label>
            <label class="radio">
              <input type="radio" name="animal" value="rabbit" v-model="form.animal" />
              <span>Rabbit</span>
            </label>
          </div>
        </div>

        <!-- 오른쪽: 성격 요소 (체크박스: 여러 개 선택) -->
        <div class="tutor-block">
          <h3 class="label">캐릭터 성격 요소</h3>
          <div class="traits">
            <label class="checkbox"><input type="checkbox" value="친절함" v-model="form.traits" /> <span>CHECKBOX</span></label>
            <label class="checkbox"><input type="checkbox" value="유머" v-model="form.traits" /> <span>CHECKBOX</span></label>
            <label class="checkbox"><input type="checkbox" value="논리적" v-model="form.traits" /> <span>CHECKBOX</span></label>
            <label class="checkbox"><input type="checkbox" value="차분함" v-model="form.traits" /> <span>CHECKBOX</span></label>
            <label class="checkbox"><input type="checkbox" value="열정적" v-model="form.traits" /> <span>CHECKBOX</span></label>
            <label class="checkbox"><input type="checkbox" value="창의적" v-model="form.traits" /> <span>CHECKBOX</span></label>
            <label class="checkbox"><input type="checkbox" value="꼼꼼함" v-model="form.traits" /> <span>CHECKBOX</span></label>
            <label class="checkbox"><input type="checkbox" value="배려심" v-model="form.traits" /> <span>CHECKBOX</span></label>
          </div>
        </div>
      </div>

      <!-- 대화 예시 -->
      <label class="visually-hidden" for="sample">대화 예시</label>
      <textarea
        id="sample"
        class="textarea big"
        rows="10"
        placeholder="대화 예시"
        v-model="form.sampleDialog"
      ></textarea>
    </section>

    <!-- 하단 버튼 -->
    <div class="actions">
      <button type="button" class="primary" @click="apply">Submit</button>
    </div>
  </main>
</template>

<script setup lang="ts">
import { reactive } from 'vue'

const form = reactive({
  // 학습 방법
  mode: '',           // 'debate' | 'express'
  debateMsg: '',
  expressMsg: '',

  // 튜터 캐릭터
  animal: '',         // 라디오: 한 가지
  traits: [] as string[], // 체크박스: 여러 개
  sampleDialog: '',

  // (기존 필드가 필요하면 아래 유지)
  desc1: '',
  desc2: '',
})

function apply() {
  if (!form.mode) {
    alert('학습 방법(Debate/Express) 중 하나를 선택해주세요.')
    return
  }
  if (!form.animal) {
    alert('튜터 캐릭터의 동물 종류를 선택해주세요.')
    return
  }
  console.log('settings payload', JSON.parse(JSON.stringify(form)))
  alert('설정이 적용되었습니다!')
}
</script>

<style scoped>
/* 페이지 레이아웃 */
.settings {
  padding: clamp(32px, 5vw, 56px) clamp(16px, 4vw, 48px);
  max-width: 1200px;
  margin: 0 auto;
}

/* 큰 제목 + 서브타이틀 */
.page-hero {
  text-align: center;
  margin-bottom: clamp(24px, 4vw, 40px);
}
.page-hero h1 {
  font-weight: 800;
  font-size: clamp(2rem, 1.2rem + 3vw, 4rem);
  line-height: 1.15;
  letter-spacing: -0.02em;
  margin: 0 0 6px 0;
  color: #111827;
}
.subtitle {
  color: #9ca3af;
  font-size: clamp(1rem, 0.9rem + 0.4vw, 1.25rem);
  margin: 0;
}

/* 옵션 2열 그리드 */
.options {
  display: grid;
  grid-template-columns: 1fr;
  gap: clamp(20px, 2.5vw, 28px);
  margin-top: clamp(12px, 2vw, 20px);
}
@media (min-width: 960px) {
  .options { grid-template-columns: 1fr 1fr; }
}

/* 공통 라벨/체크박스 */
.label {
  font-size: 0.85rem;
  letter-spacing: 0.12em;
  color: #6b7280;
  margin: 0 0 8px 0;
}
.checkbox, .radio {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: #6b7280;
  user-select: none;
}
.checkbox input, .radio input { width: 18px; height: 18px; }

/* 도움문구 */
.hint { margin: 8px 0 10px; color: #6b7280; font-size: 0.95rem; }

/* 텍스트영역 */
.textarea {
  width: 100%;
  min-height: 220px;
  padding: 14px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  font-size: 1rem;
  color: #111827;
  outline: none;
  resize: vertical;
}
.textarea.big { min-height: 260px; }
.textarea:focus {
  border-color: #9ca3af;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12);
}

/* ✅ 튜터 섹션 */
.tutor { margin-top: clamp(28px, 5vw, 56px); }
.tutor-title {
  text-align: center;
  font-weight: 800;
  font-size: clamp(2rem, 1.2rem + 2.4vw, 3.25rem);
  letter-spacing: -0.02em;
  margin: 0 0 8px;
  color: #111827;
}
.tutor .subtitle {
  text-align: center;
  margin-bottom: clamp(18px, 2.4vw, 28px);
}

.tutor-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: clamp(18px, 2.4vw, 24px);
  margin-bottom: clamp(18px, 2.4vw, 24px);
}
@media (min-width: 960px) {
  .tutor-grid { grid-template-columns: 1fr 1fr; }
}

.radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 18px;
}

.traits {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
}
@media (min-width: 560px) {
  .traits { grid-template-columns: 1fr 1fr; }
}

/* 하단 버튼 */
.actions {
  display: flex;
  justify-content: center;
  margin-top: clamp(20px, 3vw, 32px);
}
.primary {
  appearance: none;
  border: none;
  padding: 0.9rem 1.4rem;
  border-radius: 12px;
  background: #2f8deb; /* 산뜻한 파란색 */
  color: #fff;
  font-weight: 800;
  letter-spacing: 0.02em;
  cursor: pointer;
  transition: transform .06s ease, opacity .2s ease, box-shadow .2s ease;
  box-shadow: 0 6px 18px rgba(47, 141, 235, 0.35);
}
.primary:hover { opacity: .95; box-shadow: 0 8px 24px rgba(47, 141, 235, 0.45); }
.primary:active { transform: translateY(1px); }

/* 접근성 */
.visually-hidden {
  position: absolute !important;
  clip: rect(1px, 1px, 1px, 1px);
  padding: 0 !important; border: 0 !important;
  height: 1px !important; width: 1px !important; overflow: hidden;
}

/* 다크 모드 */
@media (prefers-color-scheme: dark) {
  .page-hero h1, .tutor-title { color: #e5e7eb; }
  .subtitle { color: #a3a3a3; }
  .hint, .label { color: #b0b0b0; }
  .textarea { background: #0b0b0c; color: #e5e7eb; border-color: #2a2a2a; }
  .textarea:focus { border-color: #4b5563; box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25); }
}
</style>
