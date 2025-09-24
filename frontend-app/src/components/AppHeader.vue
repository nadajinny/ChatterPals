<template>
  <header class="app-header" role="banner">
    <div class="container">
      <RouterLink
        to="/"
        class="logo"
        aria-label="Chatterpals Home"
      >
        <img src="../../public/logo.png" alt="Chatterpals 로고" class="logo-img" />
        <span class="logo-text">Chatterpals</span>
      </RouterLink>
      <nav class="nav">
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/level-test">Level Test</RouterLink>
        <RouterLink to="/aitutor">AI 튜터</RouterLink>
        <RouterLink to="/studylog">Study Log</RouterLink>
        <RouterLink to="/settings">Settings</RouterLink>
      </nav>
    </div>
  </header>
</template>

<script setup></script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-bottom: 1px solid #eaeaea;
}

.container {
  box-sizing: border-box; /* ✅ 폭 계산에 padding 포함 */
  width: 100%;
  padding: 0.75rem clamp(16px, 4vw, 48px);
  display: flex;
  align-items: center;
  gap: 1rem;
}


/* 로고 (이미지 + 텍스트) */
.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-right: auto;
  text-decoration: none;
}

.logo-img {
  width: 50px;
  height: 50px;
  object-fit: contain;
}

.logo-text {
  font-weight: 800;
  font-size: clamp(1.25rem, 1rem + 0.9vw, 1.9rem);
  background: linear-gradient(90deg, #0ea5e9, #63f1cd, #f7a655);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
/* 오른쪽에 메뉴 */
.nav {
  margin-left: auto;
  display: flex;
  gap: clamp(12px, 1.8vw, 24px);
}
.nav :is(a, .router-link-active) {
  text-decoration: none;
  color: #111827; /* gray-900 */
  font-weight: 600;
}
.nav .router-link-active {
  text-decoration: underline;
}

@media (prefers-color-scheme: dark) {
  .app-header {
    background: rgba(0, 0, 0, 0.55);
    border-bottom-color: #2a2a2a;
  }
  .nav :is(a, .router-link-active) {
    color: #e5e7eb; /* gray-200 */
  }
}
</style>
