// 曲库：按情绪象限分组。文件名只表分组与序号，标题作者写在这里。
// quadrant 取值：calm / melancholic / anxious / joyful。
// 当前四首为占位素材，授权状态未确认，不要声明为公共领域。
export const MUSIC_LIBRARY = {
  melancholic: [
    {
      id: 'melancholic-1',
      title: 'melancholic-1',
      artist: '待确认',
      file: '/audio/melancholic-1.mp3',
      license: 'PLACEHOLDER',
      source: null,
    },
  ],
  anxious: [
    {
      id: 'anxious-1',
      title: 'anxious-1',
      artist: '待确认',
      file: '/audio/anxious-1.mp3',
      license: 'PLACEHOLDER',
      source: null,
    },
  ],
  joyful: [
    {
      id: 'joyful-1',
      title: 'joyful-1',
      artist: '待确认',
      file: '/audio/joyful-1.mp3',
      license: 'PLACEHOLDER',
      source: null,
    },
  ],
  calm: [
    {
      id: 'calm-1',
      title: 'calm-1',
      artist: '待确认',
      file: '/audio/calm-1.mp3',
      license: 'PLACEHOLDER',
      source: null,
    },
  ],
}

export const QUADRANT_LABELS = {
  melancholic: '低落 · 陪伴',
  anxious: '紧绷 · 舒缓',
  joyful: '明亮 · 延续',
  calm: '平静 · 停留',
}
