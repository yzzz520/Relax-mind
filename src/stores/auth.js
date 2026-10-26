// 认证仓库：同步 Supabase session，mock 模式提供等价的本地登录态。
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import {
  MOCK_SESSION_KEY,
  logout as logoutApi,
  readMockSession,
} from '../api/auth'
import { mapSupabaseError } from '../lib/errors'
import { isMockMode, supabase } from '../lib/supabase'

export const useAuthStore = defineStore('auth', () => {
  const session = ref(null)
  const user = ref(null)
  const ready = ref(false)
  const authError = ref('')
  let authSubscription = null
  let initialization = null

  const isAuthenticated = computed(() => Boolean(user.value))
  const isAdmin = computed(
    () => user.value?.app_metadata?.role === 'admin',
  )
  const role = computed(() => {
    if (!user.value) return null
    return isAdmin.value ? 'admin' : 'user'
  })
  const nickname = computed(() => {
    return (
      user.value?.user_metadata?.nickname ||
      user.value?.email?.split('@')[0] ||
      ''
    )
  })

  function applySession(nextSession) {
    session.value = nextSession || null
    user.value = nextSession?.user || null
    authError.value = ''
    if (isMockMode) {
      if (nextSession) {
        window.localStorage.setItem(
          MOCK_SESSION_KEY,
          JSON.stringify(nextSession),
        )
      } else {
        window.localStorage.removeItem(MOCK_SESSION_KEY)
      }
    }
  }

  async function initialize() {
    if (initialization) return initialization

    initialization = (async () => {
      if (isMockMode) {
        applySession(readMockSession())
        ready.value = true
        return
      }

      const { data, error } = await supabase.auth.getSession()
      if (error) {
        authError.value = mapSupabaseError(
          error,
          '读取登录状态失败',
        ).message
      } else {
        applySession(data.session)
      }

      if (!authSubscription) {
        const result = supabase.auth.onAuthStateChange(
          (_event, nextSession) => {
            applySession(nextSession)
          },
        )
        authSubscription = result.data.subscription
      }
      ready.value = true
    })()

    return initialization
  }

  async function logout() {
    try {
      await logoutApi()
    } finally {
      applySession(null)
    }
  }

  return {
    session,
    user,
    ready,
    authError,
    role,
    nickname,
    isAuthenticated,
    isAdmin,
    initialize,
    applySession,
    logout,
  }
})
