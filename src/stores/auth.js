// 登录态仓库：管理当前角色与昵称，并同步到 localStorage。
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

const AUTH_STORAGE_KEY = 'capsule_auth'

function readStoredAuth() {
  try {
    const value = window.localStorage.getItem(AUTH_STORAGE_KEY)

    if (!value) {
      return null
    }

    const auth = JSON.parse(value)

    if (
      !['user', 'admin'].includes(auth?.role) ||
      typeof auth?.nickname !== 'string'
    ) {
      window.localStorage.removeItem(AUTH_STORAGE_KEY)
      return null
    }

    return auth
  } catch {
    window.localStorage.removeItem(AUTH_STORAGE_KEY)
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const storedAuth = readStoredAuth()
  const role = ref(storedAuth?.role ?? null)
  const nickname = ref(storedAuth?.nickname ?? '')

  const isAuthenticated = computed(() => role.value !== null)
  const isAdmin = computed(() => role.value === 'admin')

  function setAuth(auth) {
    role.value = auth.role
    nickname.value = auth.nickname
    window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(auth))
  }

  function logout() {
    role.value = null
    nickname.value = ''
    window.localStorage.removeItem(AUTH_STORAGE_KEY)
  }

  return {
    role,
    nickname,
    isAuthenticated,
    isAdmin,
    setAuth,
    logout,
  }
})
