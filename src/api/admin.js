// 管理数据 API：拉取最近 300 条胶囊并在前端完成筛选与聚合。
import { mapSupabaseError } from '../lib/errors'
import { supabase } from '../lib/supabase'
import {
  handleSupabaseUnauthorized,
  supabaseRequestUrl,
} from '../lib/unauthorized'
import { quadrantOf } from '../utils/pickMusic'

const PAGE_LIMIT = 300

function nicknameOf(profiles) {
  const profile = Array.isArray(profiles) ? profiles[0] : profiles
  return profile?.nickname || '未知用户'
}

function normalizeRecord(record) {
  const quadrant =
    record.quadrant ||
    quadrantOf(Number(record.valence), Number(record.arousal))
  return {
    id: record.id,
    createdAt: record.created_at,
    input: record.input_text,
    emotions: record.emotions || {},
    valence: Number(record.valence),
    arousal: Number(record.arousal),
    quadrant,
    userNickname: nicknameOf(record.profiles),
  }
}

export async function fetchRecords({ quadrant = null, days = null } = {}) {
  let query = supabase
    .from('capsules')
    .select(
      'id,created_at,input_text,emotions,valence,arousal,profiles(nickname)',
    )
    .order('created_at', { ascending: false })
    .limit(PAGE_LIMIT)

  if (days) {
    const since = new Date(Date.now() - days * 864e5).toISOString()
    query = query.gte('created_at', since)
  }

  const { data, error } = await query
  if (error) {
    const handled = await handleSupabaseUnauthorized(
      error,
      supabaseRequestUrl('/sb/rest/v1/capsules'),
    )
    if (!handled) {
      throw mapSupabaseError(error, '读取管理数据失败')
    }
    throw new Error('登录已失效，请重新登录')
  }

  const records = (data || []).map(normalizeRecord)
  return quadrant
    ? records.filter((record) => record.quadrant === quadrant)
    : records
}
