// 胶囊保存队列：持久化失败记录，并在应用下次启动时重试一次。
import { saveCapsule } from './capsules'

export const CAPSULE_QUEUE_KEY = 'capsule_save_queue_v1'
const MAX_QUEUE_SIZE = 20

function readQueue() {
  try {
    const raw = window.localStorage.getItem(CAPSULE_QUEUE_KEY)
    const queue = raw ? JSON.parse(raw) : []
    return Array.isArray(queue) ? queue : []
  } catch {
    window.localStorage.removeItem(CAPSULE_QUEUE_KEY)
    return []
  }
}

function writeQueue(queue) {
  try {
    window.localStorage.setItem(
      CAPSULE_QUEUE_KEY,
      JSON.stringify(queue.slice(-MAX_QUEUE_SIZE)),
    )
  } catch {
    // Storage can be unavailable in private browsing; save failure remains visible.
  }
}

export function enqueueCapsule(capsule, userId) {
  if (!userId || !capsule?.capsuleId) return
  const queue = readQueue().filter(
    (entry) => entry.capsule?.capsuleId !== capsule.capsuleId,
  )
  queue.push({
    userId,
    capsule,
    queuedAt: new Date().toISOString(),
  })
  writeQueue(queue)
}

export async function retryPendingCapsules(userId) {
  if (!userId) return { attempted: 0, saved: 0 }

  const queue = readQueue()
  const remaining = []
  let attempted = 0
  let saved = 0

  for (const entry of queue) {
    if (entry.userId !== userId) {
      remaining.push(entry)
      continue
    }

    attempted += 1
    try {
      await saveCapsule(entry.capsule, userId)
      saved += 1
    } catch {
      remaining.push(entry)
    }
  }

  writeQueue(remaining)
  return { attempted, saved }
}
