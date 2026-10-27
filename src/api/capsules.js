// 胶囊数据 API：Supabase 持久化与 mock 本地历史，统一输出前端 Capsule。
import { throwIfSupabaseError } from '../lib/errors'
import { isMockMode, supabase } from '../lib/supabase'
import {
  handleSupabaseUnauthorized,
  supabaseRequestUrl,
} from '../lib/unauthorized'

const HISTORY_PREFIX = 'capsule_mock_history_'
const PALETTES = {
  melancholic: ['#7C5CFF', '#FF8FB1'],
  anxious: ['#00E5A0', '#7C5CFF'],
  joyful: ['#FF9F43', '#FFD166'],
  calm: ['#FFC978', '#8FE3CF'],
}

export function paletteForQuadrant(quadrant) {
  return PALETTES[quadrant] || PALETTES.melancholic
}

function readMockHistory(userId) {
  try {
    const raw = window.localStorage.getItem(`${HISTORY_PREFIX}${userId}`)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function writeMockHistory(userId, items) {
  window.localStorage.setItem(
    `${HISTORY_PREFIX}${userId}`,
    JSON.stringify(items.slice(0, 50)),
  )
}

function normalizeRow(row) {
  const track = Array.isArray(row.tracks) ? row.tracks[0] : row.tracks
  const music = track
    ? {
        id: track.id,
        title: track.title,
        artist: track.artist,
        file: track.file_url,
        quadrant: track.quadrant,
      }
    : null
  const quadrant = music?.quadrant || 'melancholic'

  return {
    capsuleId: row.id,
    createdAt: row.created_at,
    input: row.input_text,
    emotions: row.emotions,
    valence: row.valence,
    arousal: row.arousal,
    keywords: row.keywords || [],
    fineLabels: row.fine_labels || [],
    quadrant,
    music,
    comment: row.comment,
    palette: PALETTES[quadrant],
  }
}

export async function saveCapsule(capsule, userId) {
  if (!userId) {
    throw new Error('保存记录需要登录状态')
  }
  if (!capsule.capsuleId) {
    throw new Error('胶囊编号缺失')
  }

  if (isMockMode) {
    const item = {
      ...capsule,
      capsuleId:
        capsule.capsuleId ||
        `mock_${Date.now()}_${Math.random().toString(16).slice(2, 6)}`,
      createdAt: capsule.createdAt || new Date().toISOString(),
    }
    const history = readMockHistory(userId).filter(
      (entry) => entry.capsuleId !== item.capsuleId,
    )
    history.unshift(item)
    writeMockHistory(userId, history)
    return item
  }

  const { error } = await supabase
    .from('capsules')
    .upsert({
      id: capsule.capsuleId,
      user_id: userId,
      input_text: capsule.input,
      emotions: capsule.emotions,
      valence: capsule.valence,
      arousal: capsule.arousal,
      keywords: capsule.keywords,
      fine_labels: capsule.fineLabels,
      track_id: capsule.music?.id || null,
      comment: capsule.comment,
    }, {
      onConflict: 'id',
      ignoreDuplicates: true,
    })
  if (error) {
    throw mapSupabaseError(error, '保存情绪胶囊失败')
  }

  return {
    ...capsule,
    capsuleId: capsule.capsuleId,
    createdAt: capsule.createdAt,
  }
}

export async function fetchHistory(limit = 50, userId) {
  if (!userId) {
    throw new Error('登录状态已失效，请重新登录')
  }
  const safeLimit = Math.min(Math.max(Number(limit) || 50, 1), 50)

  if (isMockMode) {
    return readMockHistory(userId).slice(0, safeLimit)
  }

  const { data, error } = await supabase
    .from('capsules')
    .select(
      'id,user_id,input_text,emotions,valence,arousal,keywords,fine_labels,comment,created_at,tracks(id,title,artist,file_url,quadrant)',
    )
    .eq('user_id', userId)
    .order('created_at', { ascending: false })
    .limit(safeLimit)
  if (error) {
    const handled = await handleSupabaseUnauthorized(
      error,
      supabaseRequestUrl('/sb/rest/v1/capsules'),
    )
    if (handled) {
      throw new Error('登录已失效，请重新登录')
    }
  }
  throwIfSupabaseError(error, '读取历史记录失败')
  return (data || []).map(normalizeRow)
}
