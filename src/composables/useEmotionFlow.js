// 情绪流程状态机：管理输入、解析、错误与结果占位，并丢弃过期响应。
import { ref } from 'vue'
import { analyzeMood, extractKeywords } from '../api/emotion'
import { paletteForQuadrant, saveCapsule } from '../api/capsules'
import { enqueueCapsule } from '../api/capsuleQueue'
import { useAuthStore } from '../stores/auth'
import { pickMusic } from '../utils/pickMusic'

export function useEmotionFlow() {
  const auth = useAuthStore()
  const stage = ref('input')
  const inputText = ref('')
  const capsule = ref(null)
  const keywords = ref([])
  const errorMessage = ref('')
  const saveState = ref('idle')
  let requestId = 0
  let saveStateTimer

  function clearSaveStateTimer() {
    window.clearTimeout(saveStateTimer)
  }

  async function submit(text) {
    const myId = ++requestId
    inputText.value = text
    keywords.value = extractKeywords(text)
    errorMessage.value = ''
    saveState.value = 'idle'
    clearSaveStateTimer()
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

      const draft = {
        ...data,
        capsuleId: crypto.randomUUID(),
        createdAt: data.createdAt || new Date().toISOString(),
        input: text,
        quadrant: music.quadrant,
        music,
        palette: data.palette || paletteForQuadrant(music.quadrant),
      }
      capsule.value = draft
      stage.value = 'result'
      saveState.value = 'saving'

      const userId = auth.user?.id
      saveCapsule(draft, userId)
        .then((saved) => {
          if (
            myId !== requestId ||
            capsule.value?.capsuleId !== draft.capsuleId
          ) {
            return
          }
          capsule.value = saved
          saveState.value = 'saved'
          clearSaveStateTimer()
          saveStateTimer = window.setTimeout(() => {
            if (
              myId === requestId &&
              saveState.value === 'saved'
            ) {
              saveState.value = 'idle'
            }
          }, 2000)
        })
        .catch(() => {
          enqueueCapsule(draft, userId)
          if (
            myId === requestId &&
            capsule.value?.capsuleId === draft.capsuleId
          ) {
            saveState.value = 'failed'
          }
        })
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
    clearSaveStateTimer()
    stage.value = 'input'
    keywords.value = []
    capsule.value = null
    errorMessage.value = ''
    saveState.value = 'idle'
  }

  return {
    stage,
    inputText,
    capsule,
    keywords,
    errorMessage,
    saveState,
    submit,
    reset,
  }
}
