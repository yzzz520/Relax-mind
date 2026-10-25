// 音频分析器：延迟创建全局 AudioContext，并缓存每个 audio 元素的节点图。
let context = null
const audioGraphs = new WeakMap()

export function getContext() {
  if (!context || context.state === 'closed') {
    const AudioContextClass =
      window.AudioContext || window.webkitAudioContext
    context = new AudioContextClass()
  }

  return context
}

export function createAnalyser(audioElement) {
  const cachedGraph = audioGraphs.get(audioElement)

  if (cachedGraph) {
    return cachedGraph
  }

  const audioContext = getContext()
  const source = audioContext.createMediaElementSource(audioElement)
  const analyser = audioContext.createAnalyser()
  analyser.fftSize = 128
  source.connect(analyser)
  analyser.connect(audioContext.destination)

  const graph = { source, analyser, context: audioContext }
  audioGraphs.set(audioElement, graph)
  return graph
}

export async function closeAudioContext() {
  if (context && context.state !== 'closed') {
    await context.close()
  }

  context = null
}
