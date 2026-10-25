// 情绪流程状态机：管理输入、解析、错误与结果占位，并丢弃过期响应。
import { ref } from 'vue'
import { analyzeMood, extractKeywords } from '../api/emotion'

export function useEmotionFlow() {
  const stage = ref('input')
  const inputText = ref('')
  const capsule = ref(null)
  const keywords = ref([])
  let requestId = 0

  async function submit(text) {
    const myId = ++requestId
    inputText.value = text
    keywords.value = extractKeywords(text)
    stage.value = 'analyzing'

    try {
      const data = await analyzeMood(text)

      if (myId !== requestId) {
        return
      }

      capsule.value = data
      stage.value = 'result'
    } catch {
      if (myId !== requestId) {
        return
      }

      stage.value = 'error'
    }
  }

  function reset() {
    requestId += 1
    stage.value = 'input'
    keywords.value = []
    capsule.value = null
  }

  return {
    stage,
    inputText,
    capsule,
    keywords,
    submit,
    reset,
  }
}
