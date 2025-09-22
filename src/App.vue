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

<style scoped></style>
