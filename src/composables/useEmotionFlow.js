// 情绪流程状态机：管理输入、解析、错误与结果占位，并丢弃过期响应。
import { ref } from 'vue'
import { analyzeMood, extractKeywords } from '../api/emotion'
import { paletteForQuadrant, saveCapsule } from '../api/capsules'
import { useAuthStore } from '../stores/auth'
import { pickMusic } from '../utils/pickMusic'

export function useEmotionFlow() {
  const auth = useAuthStore()
  const stage = ref('input')
  const inputText = ref('')
  const capsule = ref(null)
  const keywords = ref([])
  const errorMessage = ref('')
  let requestId = 0

  async function submit(text) {
    const myId = ++requestId
    inputText.value = text
    keywords.value = extractKeywords(text)
    errorMessage.value = ''
    stage.value = 'analyzing'

    try {
      const data = await analyzeMood(text, auth.session?.access_token)

      if (myId !== requestId) {
        return
      }

      const music = pickMusic(
        data.valence,
        data.arousal,
        text,
      )
      if (!music) {
        throw new Error('曲库配置不可用')
      }
      if (myId !== requestId) {
        return
      }

      const saved = await saveCapsule(
        {
          ...data,
          input: text,
          quadrant: music.quadrant,
          music,
          palette:
            data.palette || paletteForQuadrant(music.quadrant),
        },
        auth.user?.id,
      )
      if (myId !== requestId) {
        return
      }

      capsule.value = saved
      stage.value = 'result'
    } catch (error) {
      if (myId !== requestId) {
        return
      }

      errorMessage.value =
        error instanceof Error ? error.message : '解析失败，请重试'
      stage.value = 'error'
    }
  }

  function reset() {
    requestId += 1
    stage.value = 'input'
    keywords.value = []
    capsule.value = null
    errorMessage.value = ''
  }

  return {
    stage,
    inputText,
    capsule,
    keywords,
    errorMessage,
    submit,
    reset,
  }
}
