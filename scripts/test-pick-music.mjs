// 选曲回归：验证同文本稳定性、同象限分布和四象限判定。
// 用法：node scripts/test-pick-music.mjs
import { pickMusic, quadrantOf } from '../src/utils/pickMusic.js'

const SAME = '今天面试被挂了，外面还在下雨，感觉好累'

// ① 稳定性：同一段文本 100 次
const ids = new Set()
for (let i = 0; i < 100; i += 1) {
  ids.add(pickMusic(-0.76, 0.44, SAME).id)
}
console.log('① 同一文本 100 次 →', [...ids], ids.size === 1 ? 'PASS' : 'FAIL')

// ② 分布：10 段不同文本，同一象限
const texts = [
  '晒了被子很舒服',
  '午后阳光照进来',
  '安静地坐一会儿',
  '慢慢喝完一杯茶',
  '今天过得很松弛',
  '被窝里暖暖的',
  '窗外阳光正好',
  '什么也不做很安心',
  '心里踏实又平静',
  '这是很舒服的一天',
]
const tally = {}
for (const t of texts) {
  const m = pickMusic(0.8, 0.3, t)
  tally[m.id] = (tally[m.id] || 0) + 1
}
console.log('② 10 段文本分布 →', tally)
console.log(
  '   不同 id 数 =',
  Object.keys(tally).length,
  Object.keys(tally).length >= 2 ? 'PASS' : 'FAIL',
)

// ③ 象限判定抽查
for (const [v, a, want] of [
  [-0.7, 0.3, 'melancholic'],
  [-0.7, 0.7, 'anxious'],
  [0.8, 0.7, 'joyful'],
  [0.8, 0.3, 'calm'],
]) {
  const got = quadrantOf(v, a)
  console.log(
    `③ (${v}, ${a}) → ${got}`,
    got === want ? 'PASS' : `FAIL(期望 ${want})`,
  )
}
