// 情绪 API：mock 模式本地分析，api 模式调用受 Supabase JWT 保护的后端。
import {
  analyzeMood as analyzeMockMood,
  extractKeywords as extractMockKeywords,
} from './mock'
import { isMockMode } from '../lib/supabase'

export function extractKeywords(text) {
  return extractMockKeywords(text)
}

export async function analyzeMood(text, accessToken) {
  if (isMockMode) {
    return analyzeMockMood(text)
  }
  if (!accessToken) {
    throw new Error('登录状态已失效，请重新登录')
  }

  let response
  try {
    response = await fetch('/api/analyze', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    })
  } catch {
    throw new Error('网络异常，请稍后重试')
  }

  let payload = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('登录已失效，请重新登录')
    }
    throw new Error(
      typeof payload?.detail === 'string'
        ? payload.detail
        : '分析服务暂不可用，请稍后重试',
    )
  }

  if (
    !payload ||
    typeof payload !== 'object' ||
    !payload.emotions ||
    typeof payload.valence !== 'number' ||
    typeof payload.arousal !== 'number'
  ) {
    throw new Error('分析结果格式异常')
  }
  return payload
}
