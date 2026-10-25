// 情绪 Mock：提供关键词提取、五组情绪样本和分析延迟。
import { pickMusic } from '../utils/pickMusic.js'

// 情绪八维，顺序固定。雷达图、颜色映射、音乐匹配都依赖这个顺序。
// 新增维度必须同时修改：本常量 + 所有样本 + docs 中的契约表。
export const EMOTION_DIMENSIONS = [
  '喜悦',
  '期待',
  '平静',
  '温暖',
  '悲伤',
  '焦虑',
  '疲惫',
  '孤独',
]

const KEYWORD_RULES = [
  { terms: ['面试', '工作', 'offer'], keyword: '面试' },
  { terms: ['雨', '湿', '冷'], keyword: '潮湿' },
  { terms: ['累', '疲', '困'], keyword: '疲惫' },
  { terms: ['挂', '失败', '拒'], keyword: '挫败' },
  { terms: ['家', '想', '一个人'], keyword: '想家' },
  { terms: ['紧张', '睡', '焦虑'], keyword: '焦虑' },
  { terms: ['开心', '拿下', '成功'], keyword: '喜悦' },
]

const FALLBACK_KEYWORDS = ['情绪', '此刻', '难以名状']

const SAMPLES = [
  {
    capsuleId: 'cap_20261024_001',
    createdAt: '2026-10-24T22:30:00+08:00',
    input: '今天面试被挂了，外面还在下雨，感觉好累',
    emotions: {
      喜悦: 3,
      期待: 18,
      平静: 20,
      温暖: 10,
      悲伤: 78,
      焦虑: 62,
      疲惫: 80,
      孤独: 55,
    },
    keywords: ['面试', '下雨', '退堂鼓', '潮湿', '撑住'],
    fineLabels: ['挫败', '无力', '被否定', '潮湿', '撑不住'],
    comment:
      '面试挂了，外面还下着雨——这两件事今天一起来了，难怪你觉得累。\n别灰心，这场雨总会停的。听听这首 Lo-fi，就当是我陪着你。',
    palette: ['#7C5CFF', '#FF8FB1'],
  },
  {
    capsuleId: 'cap_20261024_002',
    createdAt: '2026-10-24T22:35:00+08:00',
    input: '我终于拿到 offer 了，想大喊一声',
    emotions: {
      喜悦: 88,
      期待: 85,
      平静: 35,
      温暖: 70,
      悲伤: 5,
      焦虑: 10,
      疲惫: 15,
      孤独: 0,
    },
    keywords: ['offer', '终于', '松一口气'],
    fineLabels: ['狂喜', '被肯定', '释然', '想哭', '值得'],
    comment:
      '拿到 offer 了，想大喊一声也很正常。\n有些开心是需要被放大的，让这首歌陪你一起喊出来。',
    palette: ['#FF9F43', '#FFD166'],
  },
  {
    capsuleId: 'cap_20261024_003',
    createdAt: '2026-10-24T22:40:00+08:00',
    input: '一个人在外地，晚上有点想家',
    emotions: {
      喜悦: 10,
      期待: 30,
      平静: 60,
      温暖: 25,
      悲伤: 58,
      焦虑: 25,
      疲惫: 40,
      孤独: 82,
    },
    keywords: ['异地', '夜晚', '想家', '窗外'],
    fineLabels: ['想家', '空落', '挂念', '安静', '独自'],
    comment:
      '一个人在外地，晚上想起家来是躲不掉的。\n这首民谣不吵，就让它陪着你待一会儿。',
    palette: ['#3D5AFE', '#00B8D4'],
  },
  {
    capsuleId: 'cap_20261024_004',
    createdAt: '2026-10-24T22:45:00+08:00',
    input: '明天要答辩，紧张到睡不着',
    emotions: {
      喜悦: 5,
      期待: 45,
      平静: 10,
      温暖: 15,
      悲伤: 30,
      焦虑: 88,
      疲惫: 70,
      孤独: 35,
    },
    keywords: ['答辩', '失眠', '紧张', '明天'],
    fineLabels: ['紧张', '心跳', '怕搞砸', '硬撑', '失眠'],
    comment:
      '明天要答辩，紧张到睡不着，这说明你很在乎。\n别硬扛，先让节奏慢下来，再慢慢睡。',
    palette: ['#00E5A0', '#7C5CFF'],
  },
  {
    capsuleId: 'cap_20261025_005',
    createdAt: '2026-10-25T10:00:00+08:00',
    input: '今天晒了被子，很舒服',
    emotions: {
      喜悦: 40,
      期待: 30,
      平静: 82,
      温暖: 75,
      悲伤: 0,
      焦虑: 5,
      疲惫: 10,
      孤独: 5,
    },
    keywords: ['阳光', '被子', '安静', '暖'],
    fineLabels: ['松弛', '满足', '安心', '慢下来', '踏实'],
    comment:
      '挺好的，这样安静的一刻值得被记住。让这段旋律陪你把这份松弛多留一会儿。',
    palette: ['#FFC978', '#8FE3CF'],
  },
]

const VALENCE_POSITIVE = { 喜悦: 1.0, 期待: 0.6, 平静: 0.3, 温暖: 0.7 }
const VALENCE_NEGATIVE = { 悲伤: 1.0, 焦虑: 0.7, 疲惫: 0.5, 孤独: 0.6 }
const AROUSAL_ACTIVE = { 焦虑: 1.0, 喜悦: 0.8, 期待: 0.6 }
const AROUSAL_CALM = {
  平静: 0.8,
  疲惫: 0.4,
  孤独: 0.4,
  悲伤: 0.3,
  温暖: 0.3,
}

function weighted(emotions, weights) {
  return Object.entries(weights).reduce(
    (sum, [dim, weight]) => sum + (emotions[dim] ?? 0) * weight,
    0,
  )
}

/**
 * 对称归一化，数学上保证 valence ∈ [-1,1]、arousal ∈ [0,1]，无需 clamp。
 * 不要改回 /100 的写法：八维总合约 300，直接除会溢出并被截断，抹掉强度信息。
 */
export function computeVAD(emotions) {
  const pos = weighted(emotions, VALENCE_POSITIVE)
  const neg = weighted(emotions, VALENCE_NEGATIVE)
  const act = weighted(emotions, AROUSAL_ACTIVE)
  const calm = weighted(emotions, AROUSAL_CALM)

  const tv = pos + neg
  const ta = act + calm

  return {
    valence: tv === 0 ? 0 : Number(((pos - neg) / tv).toFixed(2)),
    arousal: ta === 0 ? 0.5 : Number((((act - calm) / ta + 1) / 2).toFixed(2)),
  }
}

function sleep(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

function random(min, max) {
  return Math.round(Math.random() * (max - min) + min)
}

function selectSample(text) {
  const normalizedText = text.toLowerCase()

  if (/阳光|晒|舒服|安静|慢慢/.test(normalizedText)) {
    return SAMPLES[4]
  }

  if (/offer|拿下|成功|开心/.test(normalizedText)) {
    return SAMPLES[1]
  }

  if (/紧张|睡|答辩|焦虑/.test(normalizedText)) {
    return SAMPLES[3]
  }

  if (/家|一个人|想/.test(normalizedText)) {
    return SAMPLES[2]
  }

  return SAMPLES[0]
}

export function extractKeywords(text) {
  const normalizedText = text.toLowerCase()
  const matchedKeywords = KEYWORD_RULES.filter((rule) =>
    rule.terms.some((term) => normalizedText.includes(term)),
  )
    .map((rule) => rule.keyword)
    .slice(0, 3)

  if (matchedKeywords.length === 0) {
    return [...FALLBACK_KEYWORDS]
  }

  for (const keyword of FALLBACK_KEYWORDS) {
    if (matchedKeywords.length >= 2) {
      break
    }

    if (!matchedKeywords.includes(keyword)) {
      matchedKeywords.push(keyword)
    }
  }

  return matchedKeywords
}

export async function analyzeMood(text) {
  if (new URLSearchParams(window.location.search).get('fail') === '1') {
    throw new Error('解析失败')
  }

  await sleep(random(1800, 3200))
  const sample = selectSample(text)
  const vad = computeVAD(sample.emotions)
  const capsuleId = `cap_${Date.now()}_${Math.random().toString(16).slice(2, 6)}`
  const capsule = {
    ...sample,
    capsuleId,
    ...vad,
    music: pickMusic(vad.valence, vad.arousal, text),
  }
  return structuredClone(capsule)
}
