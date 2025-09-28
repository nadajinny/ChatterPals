import { computed, reactive, watchEffect } from 'vue'
import { fetchMe, login as loginRequest, signup as signupRequest } from '@/services/auth'

type User = {
  id: string
  username: string
  nickname: string
  created_at: string
}

const state = reactive({
  user: null as User | null,
  token: (typeof window !== 'undefined' && window.localStorage.getItem('chatter_token')) || null,
  loading: false,
})

let initialized = false

async function ensureLoaded() {
  if (initialized) return
  initialized = true
  if (state.token) {
    try {
      state.user = await fetchMe(state.token)
    } catch (error) {
      console.warn('Failed to load user', error)
      clearAuth()
    }
  }
}

function setToken(token: string) {
  state.token = token
  if (typeof window !== 'undefined') {
    window.localStorage.setItem('chatter_token', token)
  }
}

function clearAuth() {
  state.user = null
  state.token = null
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem('chatter_token')
  }
}

export function useAuth() {
  watchEffect(() => {
    if (!initialized) {
      ensureLoaded()
    }
  })

  async function login(username: string, password: string) {
    state.loading = true
    try {
      const data = await loginRequest(username, password)
      setToken(data.access_token)
      state.user = data.user
      return data.user
    } finally {
      state.loading = false
    }
  }

  async function signup(username: string, nickname: string, password: string) {
    state.loading = true
    try {
      const data = await signupRequest({ username, nickname, password })
      setToken(data.access_token)
      state.user = data.user
      return data.user
    } finally {
      state.loading = false
    }
  }

  function logout() {
    clearAuth()
  }

  return {
    user: computed(() => state.user),
    token: computed(() => state.token),
    isAuthenticated: computed(() => Boolean(state.user && state.token)),
    loading: computed(() => state.loading),
    login,
    signup,
    logout,
    ensureLoaded,
  }
}
