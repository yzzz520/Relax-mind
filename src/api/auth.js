// 认证 API：Supabase 手机号合成邮箱登录，mock 模式使用本地会话。
import { isMockMode, supabase } from '../lib/supabase'
import { mapSupabaseError, throwIfSupabaseError } from '../lib/errors'
import {
  handleSupabaseUnauthorized,
  supabaseRequestUrl,
} from '../lib/unauthorized'

const MOCK_PROFILE_PREFIX = 'capsule_mock_profile_'
export const MOCK_SESSION_KEY = 'capsule_mock_session'

export function normalizePhone(value) {
  let phone = String(value ?? '').replace(/[\s-]/g, '')
  phone = phone.replace(/^\+86/, '')
  phone = phone.replace(/^86(?=1[3-9]\d{9}$)/, '')

  if (!/^1[3-9]\d{9}$/.test(phone)) {
    throw new Error('请输入正确的 11 位手机号')
  }
  return phone
}

function syntheticEmail(phone) {
  return `${phone}@phone.local`
}

function validatePassword(password) {
  if (String(password ?? '').length < 6) {
    throw new Error('密码至少 6 位')
  }
}

function validateLoginPassword(password) {
  if (!String(password ?? '')) {
    throw new Error('请输入密码')
  }
}

async function raiseSupabaseAuthError(error, path, fallback) {
  const handled = await handleSupabaseUnauthorized(
    error,
    supabaseRequestUrl(path),
  )
  if (handled) {
    throw new Error('登录已失效，请重新登录')
  }
  throw mapSupabaseError(error, fallback)
}

function mockSession(phone, nickname, role = 'user') {
  return {
    access_token: `mock-token-${phone}`,
    token_type: 'bearer',
    user: {
      id: `mock-${phone}`,
      email: syntheticEmail(phone),
      user_metadata: { nickname, phone },
      app_metadata: { role },
    },
  }
}

export function readMockSession() {
  try {
    const value = window.localStorage.getItem(MOCK_SESSION_KEY)
    return value ? JSON.parse(value) : null
  } catch {
    window.localStorage.removeItem(MOCK_SESSION_KEY)
    return null
  }
}

export async function register(phone, nickname, password) {
  const normalizedPhone = normalizePhone(phone)
  const normalizedNickname = String(nickname ?? '').trim()
  validatePassword(password)
  if (normalizedNickname.length < 2) {
    throw new Error('昵称至少需要 2 个字')
  }

  if (isMockMode) {
    const key = `${MOCK_PROFILE_PREFIX}${normalizedPhone}`
    if (window.localStorage.getItem(key)) {
      throw new Error('这个手机号已经注册过了')
    }
    window.localStorage.setItem(
      key,
      JSON.stringify({ nickname: normalizedNickname }),
    )
    return mockSession(normalizedPhone, normalizedNickname)
  }

  const { data, error } = await supabase.auth.signUp({
    email: syntheticEmail(normalizedPhone),
    password,
    options: {
      data: {
        nickname: normalizedNickname,
        phone: normalizedPhone,
      },
    },
  })
  if (error) {
    await raiseSupabaseAuthError(
      error,
      '/sb/auth/v1/signup',
      '注册失败，请稍后重试',
    )
  }
  throwIfSupabaseError(error, '注册失败，请稍后重试')

  if (data.user?.identities?.length === 0) {
    throw new Error('这个手机号已经注册过了')
  }

  if (data.session) {
    return data.session
  }

  const loginResult = await supabase.auth.signInWithPassword({
    email: syntheticEmail(normalizedPhone),
    password,
  })
  if (loginResult.error) {
    await raiseSupabaseAuthError(
      loginResult.error,
      '/sb/auth/v1/token',
      '注册成功，但自动登录失败',
    )
  }
  throwIfSupabaseError(loginResult.error, '注册成功，但自动登录失败')
  return loginResult.data.session
}

export async function login(phone, password) {
  const normalizedPhone = normalizePhone(phone)
  validateLoginPassword(password)

  if (isMockMode) {
    const profile = window.localStorage.getItem(
      `${MOCK_PROFILE_PREFIX}${normalizedPhone}`,
    )
    let nickname = `用户${normalizedPhone.slice(-4)}`
    try {
      nickname = profile ? JSON.parse(profile).nickname : nickname
    } catch {
      window.localStorage.removeItem(
        `${MOCK_PROFILE_PREFIX}${normalizedPhone}`,
      )
    }
    return mockSession(normalizedPhone, nickname)
  }

  const { data, error } = await supabase.auth.signInWithPassword({
    email: syntheticEmail(normalizedPhone),
    password,
  })
  if (error) {
    await raiseSupabaseAuthError(
      error,
      '/sb/auth/v1/token',
      '登录失败，请稍后重试',
    )
  }
  return data.session
}

export async function adminLogin(phone, password) {
  if (isMockMode) {
    const normalizedPhone = normalizePhone(phone)
    validateLoginPassword(password)
    return mockSession(normalizedPhone, '管理员', 'admin')
  }

  const session = await login(phone, password)
  const role = session?.user?.app_metadata?.role
  if (role !== 'admin') {
    const { error } = await supabase.auth.signOut()
    if (error) {
      await raiseSupabaseAuthError(
        error,
        '/sb/auth/v1/logout',
        '退出非管理员账号失败',
      )
    }
    throw new Error('该账号没有管理员权限')
  }
  return session
}

export async function logout() {
  if (isMockMode) {
    window.localStorage.removeItem(MOCK_SESSION_KEY)
    return
  }
  const { error } = await supabase.auth.signOut()
  if (error) {
    const handled = await handleSupabaseUnauthorized(
      error,
      supabaseRequestUrl('/sb/auth/v1/logout'),
    )
    if (!handled) {
      throw mapSupabaseError(error, '退出登录失败')
    }
  }
}
