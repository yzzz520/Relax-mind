// 仅对 Supabase 同源代理请求处理 401，避免误伤自家 /api 请求。
import { supabase } from './supabase'

const LOGIN_PATH = '/login'

export function supabaseRequestUrl(path) {
  return new URL(path, window.location.origin).toString()
}

export function isUnauthorizedStatus(error) {
  return Number(error?.status) === 401
}

export function isSupabaseRequestUrl(requestUrl) {
  try {
    const target = new URL(requestUrl, window.location.origin)
    return (
      target.origin === window.location.origin &&
      target.pathname.startsWith('/sb/')
    )
  } catch {
    return false
  }
}

export function isSupabaseUnauthorized(error, requestUrl) {
  return isUnauthorizedStatus(error) && isSupabaseRequestUrl(requestUrl)
}

export async function handleSupabaseUnauthorized(error, requestUrl) {
  if (!isSupabaseUnauthorized(error, requestUrl)) {
    return false
  }

  try {
    await supabase.auth.signOut({ scope: 'local' })
  } finally {
    if (window.location.pathname !== LOGIN_PATH) {
      window.location.assign(LOGIN_PATH)
    }
  }
  return true
}
