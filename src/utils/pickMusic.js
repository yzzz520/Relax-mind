// 选曲工具：把 VAD 坐标映射到四象限，并用稳定哈希选择曲目。
import { MUSIC_LIBRARY } from '../data/musicLibrary.js'

export function quadrantOf(valence, arousal) {
  if (valence < 0 && arousal < 0.5) return 'melancholic'
  if (valence < 0) return 'anxious'
  if (arousal < 0.5) return 'calm'
  return 'joyful'
}

function hashString(s) {
  let h = 0
  for (let i = 0; i < s.length; i += 1) {
    h = (h * 31 + s.charCodeAt(i)) >>> 0
  }
  return h
}

export function pickMusic(valence, arousal, seed = '') {
  const quadrant = quadrantOf(valence, arousal)
  const list = MUSIC_LIBRARY[quadrant]

  if (!list || list.length === 0) {
    return null
  }

  const index = hashString(String(seed)) % list.length
  return { ...list[index], quadrant }
}
