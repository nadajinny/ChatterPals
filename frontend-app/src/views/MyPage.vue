<template>
  <main class="mypage">
    <section class="hero" aria-labelledby="mypage-title">
      <h2 id="mypage-title">Home</h2>
      <p>
        👋 환영합니다! <strong>Chatterpals</strong> 마이페이지 화면입니다. 앞으로 여기에서 기능을
        하나씩 추가해 나가요.
      </p>
    </section>
  </main>
</template>

<script setup lang="ts">
// 페이지 로직은 아직 없어요. 이후에 상태/라우팅을 연결해요.
</script>

<style scoped>
.mypage {
  padding: 2rem 1rem;
}

.hero {
  max-width: 900px;
  margin: 0 auto;
  text-align: center;
}

.hero h2 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.hero p {
  color: #4b5563; /* gray-600 */
}

@media (prefers-color-scheme: dark) {
  .hero p {
    color: #9ca3af; /* gray-400 */
  }
}
</style>