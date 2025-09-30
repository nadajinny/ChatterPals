import { computed, reactive, watchEffect } from 'vue'
import { fetchMe, login as loginRequest, signup as signupRequest } from '@/services/auth'

type User = {
  id: string
  username: string
  nickname: string
  created_at: string
}

const AUTH_MESSAGE_TYPE = 'AUTH_UPDATE'
const WEB_SOURCE = 'chatter-web'
const EXTENSION_SOURCE = 'chatter-extension'

const initialToken =
  (typeof window !== 'undefined' && window.localStorage.getItem('chatter_token')) || null

const state = reactive({
  user: null as User | null,
  token: initialToken,
  loading: false,
})

let initialized = false

type ApplyOptions = { broadcast?: boolean }

function postAuthUpdate(token: string | null, user: User | null) {
  if (typeof window === 'undefined') return
  window.postMessage(
    {
      source: WEB_SOURCE,
      type: AUTH_MESSAGE_TYPE,
      token,
      user,
    },
    '*',
  )
}

function applyAuth(token: string | null, user: User | null, options: ApplyOptions = {}) {
  const broadcast = options.broadcast ?? true
  state.user = user
  state.token = token
  if (typeof window !== 'undefined') {
    if (token) {
      window.localStorage.setItem('chatter_token', token)
    } else {
      window.localStorage.removeItem('chatter_token')
    }
  }
  if (broadcast) {
    postAuthUpdate(token, user)
  }
}

function isAuthMessage(payload: unknown): payload is {
  source: string
  type: string
  token?: string | null
  user?: User | null
} {
  if (!payload || typeof payload !== 'object') return false
  const record = payload as Record<string, unknown>
  return record.source === EXTENSION_SOURCE && record.type === AUTH_MESSAGE_TYPE
}

if (typeof window !== 'undefined') {
  window.addEventListener('message', (event: MessageEvent) => {
    if (!isAuthMessage(event.data)) return
    console.debug('[useAuth] Received auth broadcast from extension', event.data)
    const token = typeof event.data.token === 'string' ? event.data.token : null
    const user = (event.data.user ?? null) as User | null
    applyAuth(token, user, { broadcast: false })
  })
}

async function ensureLoaded() {
  if (initialized) return
  initialized = true
  if (state.token) {
    try {
      const user = await fetchMe(state.token)
      applyAuth(state.token, user)
    } catch (error) {
      console.warn('Failed to load user', error)
      applyAuth(null, null)
    }
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
      applyAuth(data.access_token, data.user)
      return data.user
    } finally {
      state.loading = false
    }
  }

  async function signup(username: string, nickname: string, password: string) {
    state.loading = true
    try {
      const data = await signupRequest({ username, nickname, password })
      applyAuth(data.access_token, data.user)
      return data.user
    } finally {
      state.loading = false
    }
  }

  function logout() {
    applyAuth(null, null)
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
