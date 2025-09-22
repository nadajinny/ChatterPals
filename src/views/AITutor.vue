<template>
  <main class="aitutor">
    <section class="hero" aria-labelledby="aitutor-title">
      <h2 id="aitutor-title">Level Test</h2>
      <p>
        👋 환영합니다! <strong>Chatterpals</strong> aitutor 시작해보세요.
      </p>

      <!-- 시작 버튼 -->
      <RouterLink to="/aitutor/start" class="start-btn">
        aitutor 시작하기
      </RouterLink>
    </section>
  </main>
</template>

<script setup lang="ts">
// 추후 로직/상태/라우팅 연결 예정
</script>

<style scoped>
.leveltest {
  /* 넓게 시원하게 + 반응형 여백 */
  padding: 2rem clamp(16px, 4vw, 48px);
}

.hero {
  /* 폭 제한 제거 */
  max-width: none;
  margin: 0 auto;
  text-align: center;
}

.hero h2 {
  font-size: clamp(2rem, 1.6rem + 1.2vw, 3rem);
  margin-bottom: 0.5rem;
}

.hero p {
  color: #4b5563; /* gray-600 */
  font-size: clamp(1rem, 0.95rem + 0.5vw, 1.25rem);
  margin-bottom: 1.25rem;
}

/* 간단한 버튼 스타일 */
.start-btn {
  display: inline-block;
  padding: 0.85rem 1.25rem;
  border-radius: 10px;
  text-decoration: none;
  background: #6366f1;
  color: white;
  font-weight: 700;
  transition: transform .08s ease, opacity .2s ease;
}
.start-btn:hover { opacity: .95; }
.start-btn:active { transform: translateY(1px); }

@media (prefers-color-scheme: dark) {
  .hero p { color: #9ca3af; /* gray-400 */ }
}
</style>
