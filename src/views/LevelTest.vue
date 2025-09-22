<template>
  <section class="level-hero" aria-labelledby="level-title">
    <div class="level-inner">
      <h1 id="level-title">레벨테스트 시작하기 버튼</h1>

      <p class="subtitle">
        밑에는 레벨테스트가 진행되는 과정과 테스트를 평가하는 방법, 테스트 진행 결과와 테스트 결과에 따라 취득한
        배지에 대해서 각 섹션별로 설명함.
      </p>

      <!-- 탭 메뉴 -->
      <nav class="tabs" aria-label="카테고리">
        <button class="tab active" type="button">ALL PRODUCTS</button>
        <button class="tab" type="button">CATEGORY 1</button>
        <button class="tab" type="button">CATEGORY 2</button>
        <button class="tab" type="button">CATEGORY 3</button>
        <button class="tab" type="button">CATEGORY 4</button>
      </nav>

      <!-- 시작 버튼 -->
      <RouterLink to="/level-test/start" class="start-btn">레벨테스트 시작하기</RouterLink>
    </div>
  </section>
</template>

<script setup lang="ts">
// 추후 실제 탭/시작 로직 연결 예정
</script>

<style scoped>
/* 시원한 상단 히어로 영역 (풀-와이드) */
.level-hero {

  min-height: 100vh; /* ✅ 브라우저 전체 높이 */
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, #f7b980 0%, #f7cda6 40%, #fbe5cf 100%);

}

/* 내부 컨텐츠 래퍼: 너무 넓지 않게 중앙에 모으되, 꽉 막지 않음 */
.level-inner {
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
}

/* 타이틀: 크게, 굵게 */
.level-inner h1 {
  font-weight: 800;
  line-height: 1.15;
  /* 큰 화면에서 자연스럽게 커지는 반응형 폰트 */
  font-size: clamp(2rem, 1.2rem + 3vw, 4rem);
  color: #1f2937; /* gray-800 */
  margin: 0 0 0.9rem;
}

/* 서브타이틀: 가독성 좋은 중간 톤 */
.subtitle {
  color: #374151; /* gray-700 */
  font-size: clamp(1rem, 0.9rem + 0.6vw, 1.25rem);
  max-width: 1000px;
  margin: 0 auto clamp(18px, 2.2vw, 28px);
}

/* 탭 메뉴 */
.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: clamp(8px, 1.2vw, 18px);
  justify-content: center;
  align-items: center;
  margin: 0 auto clamp(22px, 2.5vw, 36px);
}

.tab {
  appearance: none;
  background: transparent;
  border: none;
  letter-spacing: 0.06em;
  font-weight: 800;
  font-size: clamp(0.85rem, 0.7rem + 0.4vw, 1rem);
  color: #6b7280; /* gray-500 */
  padding: 6px 2px;
  cursor: pointer;
}
.tab.active {
  color: #374151; /* gray-700 */
  position: relative;
}
.tab.active::after {
  content: "";
  display: block;
  height: 2px;
  border-radius: 2px;
  background: #374151;
  margin: 6px auto 0;
  width: 100%;
}

/* 시작 버튼 */
.start-btn {
  display: inline-block;
  margin-top: clamp(8px, 1.2vw, 16px);
  padding: clamp(12px, 1.2vw, 14px) clamp(18px, 2.2vw, 24px);
  border-radius: 12px;
  text-decoration: none;
  background: #111827; /* gray-900 */
  color: #fff;
  font-weight: 800;
  letter-spacing: 0.02em;
  transition: transform 0.06s ease, opacity 0.2s ease, box-shadow 0.2s ease;
  box-shadow: 0 6px 18px rgba(17, 24, 39, 0.15);
}
.start-btn:hover {
  opacity: 0.95;
  box-shadow: 0 8px 24px rgba(17, 24, 39, 0.18);
}
.start-btn:active {
  transform: translateY(1px);
}

/* 다크 모드 대비 */
@media (prefers-color-scheme: dark) {
  .level-inner h1 { color: #e5e7eb; }       /* gray-200 */
  .subtitle { color: #d1d5db; }             /* gray-300 */
  .tab { color: #a1a1aa; }                  /* zinc-400 */
  .tab.active { color: #e5e7eb; }
  .tab.active::after { background: #e5e7eb; }
  .start-btn { background: #e5e7eb; color: #111827; }
}
</style>
