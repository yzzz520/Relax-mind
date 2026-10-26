function messageOf(error) {
  return `${error?.code || ''} ${error?.message || error || ''}`
    .trim()
    .toLowerCase()
}

export function mapSupabaseError(error, fallback = '操作失败，请稍后重试') {
  const message = messageOf(error)

  if (
    message.includes('invalid login credentials') ||
    message.includes('invalid_credentials')
  ) {
    return new Error('手机号或密码错误')
  }
  if (
    message.includes('user already registered') ||
    message.includes('user_already_exists') ||
    message.includes('already registered') ||
    message.includes('already been registered')
  ) {
    return new Error('这个手机号已经注册过了')
  }
  if (
    message.includes('password should be at least 6 characters') ||
    message.includes('weak_password')
  ) {
    return new Error('密码至少 6 位')
  }
  if (message.includes('email not confirmed')) {
    return new Error('登录失败：请先关闭 Supabase 邮箱确认')
  }
  if (
    message.includes('failed to fetch') ||
    message.includes('networkerror') ||
    message.includes('network request failed') ||
    message.includes('fetch_error') ||
    message.includes('request_timeout')
  ) {
    return new Error('网络异常，请稍后重试')
  }
  if (
    message.includes('row-level security') ||
    message.includes('permission denied') ||
    message.includes('jwt')
  ) {
    return new Error('没有权限访问该数据，请重新登录')
  }

  return new Error(fallback)
}

export function throwIfSupabaseError(error, fallback) {
  if (error) {
    throw mapSupabaseError(error, fallback)
  }
}
