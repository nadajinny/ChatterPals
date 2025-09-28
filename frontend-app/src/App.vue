<script setup lang="ts">
import AppHeader from '@/components/AppHeader.vue'
</script>

<template>
  <div id="app">
  <AppHeader />
  <!-- 현재 URL에 맞는 페이지 컴포넌트가 여기 표시됨 -->
  <RouterView />
  </div>
</template>

<style>
@font-face {
  font-family: "BMDOHYEON";
  src: url("../assets/fonts/BMDOHYEON_otf.otf") format("opentype");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}

/* 전역 폰트 설정 */
html, body {
  font-family: "BMDOHYEON", "Noto Sans KR", sans-serif;
  line-height: 1.6;
  color: #111827;
}
</style>


