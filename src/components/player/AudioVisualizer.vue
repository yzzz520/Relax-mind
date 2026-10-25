<!-- 音频频谱：绘制中心呼吸圆与 48 根放射频谱条。 -->
<!-- 输入 analyser、播放状态与配色，输出实时 canvas 动画。 -->
<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  analyser: {
    type: Object,
    default: null,
  },
  isPlaying: Boolean,
  isFallback: Boolean,
  palette: {
    type: Array,
    default: () => ['#7C5CFF', '#FF8FB1'],
  },
})

const BAR_COUNT = 48
const canvas = ref(null)
const levels = new Array(BAR_COUNT).fill(0)

let context
let frameId = 0
let resizeObserver
let frequencyData = null
let width = 0
let height = 0
let running = false
let lastTimestamp = 0

function resizeCanvas() {
  if (!canvas.value) {
    return
  }

  width = canvas.value.clientWidth
  height = canvas.value.clientHeight
  const dpr = window.devicePixelRatio || 1
  canvas.value.width = Math.round(width * dpr)
  canvas.value.height = Math.round(height * dpr)
  context = canvas.value.getContext('2d')
  context.setTransform(dpr, 0, 0, dpr, 0, 0)
}

function hexToRgba(hex, alpha) {
  const value = hex.replace('#', '')
  const normalized =
    value.length === 3
      ? value
          .split('')
          .map((char) => char + char)
          .join('')
      : value
  const number = Number.parseInt(normalized, 16)
  return `rgba(${(number >> 16) & 255}, ${(number >> 8) & 255}, ${number & 255}, ${alpha})`
}

function draw(timestamp) {
  if (!running || !context) {
    return
  }

  frameId = window.requestAnimationFrame(draw)
  context.clearRect(0, 0, width, height)
  const elapsed = lastTimestamp
    ? Math.min(1000, timestamp - lastTimestamp)
    : 16
  lastTimestamp = timestamp

  const centerX = width / 2
  const centerY = height / 2
  const scale = Math.min(width, height) / 260
  const breathing = 0.5 + 0.5 * Math.sin(timestamp / 900)
  let lowEnergy = 0

  if (props.analyser && props.isPlaying) {
    props.analyser.getByteFrequencyData(frequencyData)
    lowEnergy =
      frequencyData.slice(0, 12).reduce((sum, value) => sum + value, 0) /
      (12 * 255)
  } else {
    lowEnergy = props.isFallback ? 0.35 + breathing * 0.25 : breathing * 0.16
  }

  for (let index = 0; index < BAR_COUNT; index += 1) {
    let target = 0

    if (props.analyser && props.isPlaying) {
      const bin = Math.min(
        frequencyData.length - 1,
        Math.floor((index / BAR_COUNT) * frequencyData.length),
      )
      target = frequencyData[bin] / 255
    } else if (props.isFallback) {
      target = 0.25 + 0.2 * (0.5 + 0.5 * Math.sin(timestamp / 650 + index))
    }

    if (props.isPlaying || props.isFallback) {
      levels[index] += (target - levels[index]) * (props.isPlaying ? 0.24 : 0.12)
    } else {
      const decay = 1 - Math.exp(-elapsed / 180)
      levels[index] += (0 - levels[index]) * decay
    }
  }

  const centerRadius = (36 + lowEnergy * 22) * scale
  const gradient = context.createRadialGradient(
    centerX,
    centerY,
    0,
    centerX,
    centerY,
    centerRadius,
  )
  gradient.addColorStop(0, props.palette[1])
  gradient.addColorStop(1, props.palette[0])

  context.save()
  context.beginPath()
  context.arc(centerX, centerY, centerRadius, 0, Math.PI * 2)
  context.fillStyle = gradient
  context.shadowColor = hexToRgba(props.palette[0], 0.7)
  context.shadowBlur = 22 * scale
  context.fill()
  context.restore()

  const barStart = 62 * scale
  const barWidth = Math.max(1.5, 3.5 * scale)
  const idleAlpha = props.isPlaying || props.isFallback ? 0.82 : 0.3
  context.lineCap = 'round'

  for (let index = 0; index < BAR_COUNT; index += 1) {
    const angle = -Math.PI / 2 + (index / BAR_COUNT) * Math.PI * 2
    const length = (4 + levels[index] * 40) * scale
    const x1 = centerX + Math.cos(angle) * barStart
    const y1 = centerY + Math.sin(angle) * barStart
    const x2 = centerX + Math.cos(angle) * (barStart + length)
    const y2 = centerY + Math.sin(angle) * (barStart + length)

    context.beginPath()
    context.moveTo(x1, y1)
    context.lineTo(x2, y2)
    context.lineWidth = barWidth
    context.strokeStyle = hexToRgba(
      props.palette[0],
      idleAlpha * (0.35 + levels[index] * 0.65),
    )
    context.stroke()
  }
}

function startAnimation() {
  if (running) {
    return
  }

  running = true
  frameId = window.requestAnimationFrame(draw)
}

function stopAnimation() {
  running = false
  window.cancelAnimationFrame(frameId)
}

function syncAnimation() {
  if (document.hidden) {
    stopAnimation()
  } else {
    startAnimation()
  }
}

watch(
  () => props.analyser,
  (analyser) => {
    frequencyData = analyser
      ? new Uint8Array(analyser.frequencyBinCount)
      : null
  },
  { immediate: true },
)

onMounted(() => {
  resizeObserver = new ResizeObserver(resizeCanvas)
  resizeObserver.observe(canvas.value)
  resizeCanvas()
  document.addEventListener('visibilitychange', syncAnimation)
  startAnimation()
})

onBeforeUnmount(() => {
  stopAnimation()
  resizeObserver?.disconnect()
  document.removeEventListener('visibilitychange', syncAnimation)
})

defineExpose({
  getLevels: () => [...levels],
})
</script>

<template>
  <canvas
    ref="canvas"
    class="audio-visualizer"
    role="img"
    aria-label="实时音频频谱"
  ></canvas>
</template>

<style scoped>
.audio-visualizer {
  width: 260px;
  height: 260px;
}

@media (max-width: 1023px) {
  .audio-visualizer {
    width: 160px;
    height: 160px;
  }
}
</style>
