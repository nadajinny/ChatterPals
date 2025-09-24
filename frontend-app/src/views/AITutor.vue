<template>
  <main class="aitutor">
    <AITutorWidget v-if="hasStarted" />

    <section v-else class="hero" aria-labelledby="aitutor-title">
      <h2 id="aitutor-title">AI 튜터와 대화 시작하기</h2>
      <p>
        대화하기 버튼을 누르면 해당 페이지 안에서 자연스럽게 전환되는 느낌으로 진행돼요.
      </p>
      <button @click="hasStarted = true" class="start-btn">aitutor 시작하기</button>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import AITutorWidget from '@/components/AITutorWidget.vue';

// '학습 시작하기' 버튼 클릭 여부를 관리하는 상태입니다.
// 이 값이 true가 되면 화면이 AI 튜터 위젯으로 전환됩니다.
const hasStarted = ref(false);
</script>

<style scoped>
/* ================================
   Animated gradient background
   ================================ */

/* 커스텀 속성 애니메이션을 위한 선언 (지원 브라우저에서 부드럽게) */
@property --grad-angle {
  syntax: "<angle>";
  inherits: false;
  initial-value: 45deg;
}

.aitutor {
  /* 화면 가득 */
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: clamp(32px, 6vw, 72px);

  /* 초기 각도 변수 */
  --grad-angle: 45deg;

  /* 스샷 느낌의 파스텔 그라데이션 (오렌지 → 민트 → 시안) */
  background: linear-gradient(
    var(--grad-angle),
    #f6b77d 0%,
    #cfe6b0 48%,
    #98e6f2 100%
  );

  /* 각도 회전 애니메이션 */
  animation: rotate-gradient 24s linear infinite;
}

/* 각도를 360도 회전 (45→405deg) */
@keyframes rotate-gradient {
  to {
    --grad-angle: 405deg;
  }
}

/* 모션 최소화 설정을 존중 */
@media (prefers-reduced-motion: reduce) {
  .aitutor {
    animation: none;
  }
}

/* ================================
   콘텐츠 스타일
   ================================ */
.hero {
  text-align: center;
  max-width: 980px;
}

.hero h2 {
  color: rgba(17, 24, 39, 0.9);
  font-weight: 800;
  line-height: 1.15;
  font-size: clamp(2rem, 1.2rem + 2.8vw, 3.25rem);
  margin-bottom: 0.6rem;
}

.hero p {
  color: rgba(17, 24, 39, 0.75);
  font-size: clamp(1rem, 0.95rem + 0.4vw, 1.2rem);
  margin: 0 0 1.2rem;
}

/* 버튼 */
.start-btn {
  display: inline-block;
  padding: 0.9rem 1.35rem;
  border-radius: 12px;
  text-decoration: none;
  background: #111827;
  color: #fff;
  font-weight: 800;
  letter-spacing: 0.02em;
  transition: transform .06s ease, opacity .2s ease, box-shadow .2s ease;
  box-shadow: 0 6px 18px rgba(17,24,39,.18);
  border: none; /* button 태그의 기본 테두리 제거 */
  cursor: pointer; /* button 태그에 커서 추가 */
}
.start-btn:hover { opacity: .95; box-shadow: 0 8px 24px rgba(17,24,39,.24); }
.start-btn:active { transform: translateY(1px); }
</style>