// 管理后台统计：所有日期按 Asia/Shanghai 计算，不依赖浏览器时区。
import { EMOTION_DIMENSIONS } from '../api/mock'

const SHANGHAI_OFFSET_MS = 8 * 60 * 60 * 1000
const DAY_MS = 24 * 60 * 60 * 1000

function shiftedDate(value) {
  return new Date(new Date(value).getTime() + SHANGHAI_OFFSET_MS)
}

export function shanghaiDayKey(value) {
  const date = shiftedDate(value)
  const year = date.getUTCFullYear()
  const month = String(date.getUTCMonth() + 1).padStart(2, '0')
  const day = String(date.getUTCDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function startOfShanghaiDay(value = new Date()) {
  const date = shiftedDate(value)
  return new Date(
    Date.UTC(
      date.getUTCFullYear(),
      date.getUTCMonth(),
      date.getUTCDate(),
    ) - SHANGHAI_OFFSET_MS,
  )
}

export function formatShanghaiShort(value) {
  const date = shiftedDate(value)
  const month = String(date.getUTCMonth() + 1).padStart(2, '0')
  const day = String(date.getUTCDate()).padStart(2, '0')
  const hour = String(date.getUTCHours()).padStart(2, '0')
  const minute = String(date.getUTCMinutes()).padStart(2, '0')
  return `${month}-${day} ${hour}:${minute}`
}

export function dominantEmotion(emotions = {}) {
  let result = '—'
  let highest = -1
  for (const dimension of EMOTION_DIMENSIONS) {
    const value = Number(emotions[dimension] ?? 0)
    if (value > highest) {
      highest = value
      result = dimension
    }
  }
  return result
}

export function computeStats(records, now = new Date()) {
  const total = records.length
  const todayStart = startOfShanghaiDay(now).getTime()
  const tomorrowStart = todayStart + DAY_MS
  const today = records.filter(
    (record) => {
      const createdAt = new Date(record.createdAt).getTime()
      return createdAt >= todayStart && createdAt < tomorrowStart
    },
  ).length

  const avgValence = total
    ? Number(
        (
          records.reduce(
            (sum, record) => sum + Number(record.valence || 0),
            0,
          ) / total
        ).toFixed(2),
      )
    : 0

  const emotionAvg = Object.fromEntries(
    EMOTION_DIMENSIONS.map((dimension) => {
      const average = total
        ? records.reduce(
            (sum, record) =>
              sum + Number(record.emotions?.[dimension] ?? 0),
            0,
          ) / total
        : 0
      return [dimension, Number(average.toFixed(1))]
    }),
  )

  const topEmotion = total
    ? EMOTION_DIMENSIONS.reduce((top, dimension) =>
        emotionAvg[dimension] > emotionAvg[top] ? dimension : top,
      )
    : '—'

  const counts = new Map()
  for (const record of records) {
    const key = shanghaiDayKey(record.createdAt)
    counts.set(key, (counts.get(key) || 0) + 1)
  }
  const daily = Array.from({ length: 7 }, (_, index) => {
    const date = new Date(now.getTime() - (6 - index) * DAY_MS)
    const key = shanghaiDayKey(date)
    return {
      date: key.slice(5),
      count: counts.get(key) || 0,
    }
  })

  return {
    total,
    today,
    avgValence,
    topEmotion,
    emotionAvg,
    daily,
  }
}
