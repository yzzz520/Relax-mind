// 情绪 API 封装：统一导出关键词提取与 mock 情绪分析。
import {
  analyzeMood as analyzeMockMood,
  extractKeywords as extractMockKeywords,
} from './mock'

export function extractKeywords(text) {
  return extractMockKeywords(text)
}

export async function analyzeMood(text) {
  return analyzeMockMood(text)
}
