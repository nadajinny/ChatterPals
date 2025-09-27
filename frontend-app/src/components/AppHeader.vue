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
        <RouterLink to="/mypage">My Page</RouterLink>
      </nav>
      <div class="auth-actions" aria-live="polite">
        <template v-if="isAuthenticated">
          <span class="welcome">안녕하세요, {{ user?.nickname }}님</span>
          <button class="link-button" type="button" @click="goMyPage">마이페이지</button>
          <button class="primary" type="button" @click="logoutUser">로그아웃</button>
        </template>
        <template v-else>
          <button class="link-button" type="button" @click="openLogin">로그인</button>
          <button class="primary" type="button" @click="openSignup">회원가입</button>
        </template>
      </div>
    </div>

    <!-- 로그인 모달 -->
    <div
      v-if="showLogin"
      class="modal-backdrop"
      role="dialog"
      aria-modal="true"
      @click.self="closeDialogs"
    >
      <section class="modal">
        <header class="modal-header">
          <h2>로그인</h2>
          <button class="icon-button" type="button" @click="closeDialogs" aria-label="닫기">×</button>
        </header>
        <form class="modal-body" @submit.prevent="handleLogin">
          <label>
            아이디(ID)
            <input v-model.trim="loginForm.username" type="text" autocomplete="username" required />
          </label>
          <label>
            비밀번호
            <input v-model.trim="loginForm.password" type="password" autocomplete="current-password" required />
          </label>
          <p v-if="authError" class="error">{{ authError }}</p>
          <button class="primary full" type="submit" :disabled="loading">{{ loading ? '로그인 중...' : '로그인' }}</button>
          <p class="switch-message">계정이 없나요? <button type="button" class="link-button" @click="switchToSignup">회원가입</button></p>
        </form>
      </section>
    </div>

    <!-- 회원가입 모달 -->
    <div
      v-if="showSignup"
      class="modal-backdrop"
      role="dialog"
      aria-modal="true"
      @click.self="closeDialogs"
    >
      <section class="modal">
        <header class="modal-header">
          <h2>회원가입</h2>
          <button class="icon-button" type="button" @click="closeDialogs" aria-label="닫기">×</button>
        </header>
        <form class="modal-body" @submit.prevent="handleSignup">
          <label>
            아이디(ID)
            <input v-model.trim="signupForm.username" type="text" autocomplete="username" required minlength="3" />
          </label>
          <label>
            닉네임
            <input v-model.trim="signupForm.nickname" type="text" required minlength="1" />
          </label>
          <label>
            비밀번호
            <input v-model.trim="signupForm.password" type="password" autocomplete="new-password" required minlength="6" />
          </label>
          <p v-if="authError" class="error">{{ authError }}</p>
          <p v-if="authSuccess" class="success">{{ authSuccess }}</p>
          <button class="primary full" type="submit" :disabled="loading">{{ loading ? '가입 중...' : '회원가입' }}</button>
          <p class="switch-message">이미 계정이 있나요? <button type="button" class="link-button" @click="switchToLogin">로그인</button></p>
        </form>
      </section>
    </div>
  </header>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { user, isAuthenticated, login, signup, logout, loading } = useAuth()

const showLogin = ref(false)
const showSignup = ref(false)
const loginForm = reactive({ username: '', password: '' })
const signupForm = reactive({ username: '', nickname: '', password: '' })
const authError = ref('')
const authSuccess = ref('')

function resetForms() {
  authError.value = ''
  authSuccess.value = ''
}

function openLogin() {
  resetForms()
  showSignup.value = false
  showLogin.value = true
}

function openSignup() {
  resetForms()
  showLogin.value = false
  showSignup.value = true
}

function switchToSignup() {
  openSignup()
}

function switchToLogin() {
  openLogin()
}

function closeDialogs() {
  showLogin.value = false
  showSignup.value = false
}

async function handleLogin() {
  authError.value = ''
  try {
    await login(loginForm.username, loginForm.password)
    closeDialogs()
    loginForm.username = ''
    loginForm.password = ''
    router.push('/mypage')
  } catch (error) {
    authError.value = error instanceof Error ? error.message : '로그인에 실패했습니다.'
  }
}

async function handleSignup() {
  authError.value = ''
  authSuccess.value = ''
  try {
    await signup(signupForm.username, signupForm.nickname, signupForm.password)
    authSuccess.value = '회원가입이 완료되었습니다. 자동으로 로그인되었습니다.'
    signupForm.username = ''
    signupForm.nickname = ''
    signupForm.password = ''
    setTimeout(() => {
      closeDialogs()
      router.push('/mypage')
    }, 600)
  } catch (error) {
    authError.value = error instanceof Error ? error.message : '회원가입에 실패했습니다.'
  }
}

function logoutUser() {
  logout()
  router.push('/')
}

function goMyPage() {
  router.push('/mypage')
}
</script>

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

.auth-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-left: clamp(12px, 3vw, 36px);
}

.welcome {
  font-weight: 600;
  color: #2563eb;
}

.link-button {
  background: none;
  border: none;
  padding: 0;
  font: inherit;
  color: #2563eb;
  cursor: pointer;
}

.link-button:hover,
.link-button:focus {
  text-decoration: underline;
}

.primary {
  border: none;
  border-radius: 9999px;
  background: linear-gradient(120deg, #6366f1, #14b8a6);
  color: #fff;
  font-weight: 600;
  padding: 0.4rem 1.1rem;
  cursor: pointer;
  transition: transform 120ms ease;
}

.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.primary:hover:not(:disabled),
.primary:focus-visible:not(:disabled) {
  transform: translateY(-1px);
}

.primary.full {
  width: 100%;
  margin-top: 1rem;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: clamp(16px, 4vw, 48px);
  z-index: 2000;
}

.modal {
  width: min(100%, 360px);
  background: #ffffff;
  border-radius: 18px;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.25);
  padding: 1.8rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.45rem;
}

.icon-button {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 9999px;
  background: #f3f4f6;
  font-size: 1.25rem;
  cursor: pointer;
}

.icon-button:hover {
  background: #e5e7eb;
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.modal-body label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-weight: 600;
  color: #1f2937;
}

.modal-body input {
  border: 1px solid #d1d5db;
  border-radius: 10px;
  padding: 0.55rem 0.75rem;
  font-size: 0.95rem;
}

.error {
  color: #dc2626;
  font-size: 0.9rem;
  margin: 0;
}

.success {
  color: #059669;
  font-size: 0.9rem;
  margin: 0;
}

.switch-message {
  display: flex;
  gap: 0.4rem;
  font-size: 0.9rem;
  align-items: center;
  justify-content: center;
}

@media (prefers-color-scheme: dark) {
  .app-header {
    background: rgba(0, 0, 0, 0.55);
    border-bottom-color: #2a2a2a;
  }
  .nav :is(a, .router-link-active) {
    color: #e5e7eb; /* gray-200 */
  }
  .modal {
    background: #111827;
    color: #e5e7eb;
    box-shadow: 0 24px 60px rgba(15, 23, 42, 0.6);
  }
  .modal-body label {
    color: #f3f4f6;
  }
  .modal-body input {
    border-color: #374151;
    background: #1f2937;
    color: #f9fafb;
  }
}
</style>
