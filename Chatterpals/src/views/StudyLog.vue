<!-- src/views/StudyLog.vue -->
<template>
  <main class="studylog">
    <section class="hero" aria-labelledby="studylog-title">
      <h1 id="studylog-title" class="title">학습통계</h1>

      <ul class="stats" aria-label="학습 통계">
        <li>학습한 글 수: <strong>10000자</strong></li>
        <li>학습 시간 : <strong>12시간</strong></li>
      </ul>

      <RouterLink to="/studylog/start" class="start-btn">전체기록 보기</RouterLink>
    </section>

    <hr class="divider" />
  </main>
</template>

<script setup lang="ts">
// 추후 로직/상태/라우팅 연결 예정
</script>

<style scoped>
/* 페이지 패딩: 큰 화면에서도 왼쪽 정렬 느낌 유지 */
.studylog {
  padding: clamp(24px, 4vw, 48px) clamp(16px, 4vw, 48px);
}

/* 왼쪽에 모은 넓은 레이아웃 */
.hero {
  max-width: 760px;   /* 왼쪽에 정보만 담고, 오른쪽은 여백 */
}

/* 큰 제목 */
.title {
  font-weight: 800;
  font-size: clamp(2.25rem, 1.5rem + 2.8vw, 4.25rem);
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: #111827; /* gray-900 */
  margin: 0 0 clamp(18px, 2.2vw, 26px);
}

/* 회색 통계 텍스트 */
.stats {
  list-style: none;
  padding: 0;
  margin: 0 0 clamp(16px, 2vw, 24px);
  color: #9ca3af; /* gray-400 */
  font-size: clamp(1rem, 0.95rem + 0.4vw, 1.25rem);
}
.stats li + li { margin-top: 6px; }
.stats strong { color: #6b7280; font-weight: 700; } /* 한 톤 짙게 */

.start-btn {
  display: inline-block;
  margin-top: clamp(10px, 1.4vw, 16px);
  padding: 0.95rem 1.4rem;
  border-radius: 10px;
  text-decoration: none;
  background: #2f8deb; /* 파란 버튼 */
  color: #fff;
  font-weight: 800;
  letter-spacing: 0.02em;
  transition: transform .06s ease, opacity .2s ease, box-shadow .2s ease;
  box-shadow: 0 6px 18px rgba(47,141,235,.3);
}
.start-btn:hover { opacity: .95; box-shadow: 0 8px 24px rgba(47,141,235,.4); }
.start-btn:active { transform: translateY(1px); }

/* 하단 구분선 */
.divider {
  margin-top: clamp(18px, 2.4vw, 28px);
  border: 0;
  border-bottom: 1px solid #e5e7eb; /* gray-200 */
}

/* 다크 모드 */
@media (prefers-color-scheme: dark) {
  .title { color: #e5e7eb; }
  .stats { color: #a3a3a3; }
  .stats strong { color: #d1d5db; }
  .divider { border-bottom-color: #2a2a2a; }
}
</style>
