<!-- 极光背景：绘制两组模糊光斑与 60-100 个缓慢漂移的 canvas 粒子。 -->
<!-- 输入 0-1 的 intensity，输出随解析状态平滑加速的视觉背景。 -->
<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  intensity: {
    type: Number,
    default: 0.3,
  },
  colors: {
    type: Array,
    default: () => ['#7C5CFF', '#FF8FB1'],
  },
})

const canvas = ref(null)
const FRAME_INTERVAL = 1000 / 60

let context
let particles = []
let frameId = 0
let lastFrame = 0
let width = 0
let height = 0
let running = false
let resizeObserver
let motionQuery

function clampIntensity(value) {
  return Math.min(1, Math.max(0, value))
}

let targetIntensity = clampIntensity(props.intensity)
let currentIntensity = targetIntensity

function createParticles() {
  const count = Math.min(
    100,
    Math.max(60, Math.round((width * height) / 16000)),
  )

  particles = Array.from({ length: count }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    size: 1 + Math.random(),
    vx: (Math.random() - 0.5) * 0.18,
    vy: (Math.random() - 0.5) * 0.18,
    alpha: 0.28 + Math.random() * 0.36,
    color: Math.random() > 0.5 ? '255, 143, 177' : '159, 139, 255',
  }))
}

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
  createParticles()
  drawFrame(false)
}

function drawFrame(shouldMove) {
  if (!context || !width || !height) {
    return
  }

  currentIntensity += (targetIntensity - currentIntensity) * 0.045
  const speed = 0.5 + currentIntensity
  const brightness = 0.55 + currentIntensity * 0.45
  context.clearRect(0, 0, width, height)

  for (const particle of particles) {
    if (shouldMove) {
      particle.x += particle.vx * speed
      particle.y += particle.vy * speed

      if (particle.x < 0) particle.x = width
      if (particle.x > width) particle.x = 0
      if (particle.y < 0) particle.y = height
      if (particle.y > height) particle.y = 0
    }

    context.fillStyle = `rgba(${particle.color}, ${particle.alpha * brightness})`
    context.fillRect(particle.x, particle.y, particle.size, particle.size)
  }
}

function animate(timestamp) {
  if (!running) {
    return
  }

  frameId = window.requestAnimationFrame(animate)

  if (timestamp - lastFrame < FRAME_INTERVAL) {
    return
  }

  lastFrame = timestamp
  drawFrame(true)
}

function stopAnimation() {
  running = false
  window.cancelAnimationFrame(frameId)
}

function startAnimation() {
  if (running || document.hidden || motionQuery.matches) {
    drawFrame(false)
    return
  }

  running = true
  lastFrame = 0
  frameId = window.requestAnimationFrame(animate)
}

function syncAnimation() {
  stopAnimation()
  startAnimation()
}

watch(
  () => props.intensity,
  (value) => {
    targetIntensity = clampIntensity(value)
  },
)

onMounted(() => {
  motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  resizeObserver = new ResizeObserver(resizeCanvas)
  resizeObserver.observe(canvas.value)
  document.addEventListener('visibilitychange', syncAnimation)
  motionQuery.addEventListener('change', syncAnimation)
  resizeCanvas()
  startAnimation()
})

onBeforeUnmount(() => {
  stopAnimation()
  resizeObserver?.disconnect()
  document.removeEventListener('visibilitychange', syncAnimation)
  motionQuery?.removeEventListener('change', syncAnimation)
})
</script>

<template>
  <div class="aurora" aria-hidden="true">
    <div class="glow glow-one" :style="{ color: colors[0] }"></div>
    <div class="glow glow-two" :style="{ color: colors[1] }"></div>
    <canvas ref="canvas" class="particles"></canvas>
  </div>
</template>

<style scoped>
.aurora {
  position: fixed;
  z-index: 0;
  inset: 0;
  overflow: hidden;
  background: var(--bg-base);
  pointer-events: none;
}

.glow {
  position: absolute;
  width: 46vw;
  min-width: 340px;
  aspect-ratio: 1;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.2;
  background: radial-gradient(circle, currentColor, transparent 68%);
  transition: color var(--dur-slow) var(--ease-soft);
  will-change: transform;
}

.glow-one {
  top: 8%;
  left: -12%;
  animation: drift-one 40s var(--ease-soft) infinite alternate;
}

.glow-two {
  right: -14%;
  bottom: -8%;
  animation: drift-two 40s var(--ease-soft) infinite alternate;
}

.particles {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

@keyframes drift-one {
  from {
    transform: translate3d(-4%, -3%, 0) scale(0.9);
  }

  to {
    transform: translate3d(22vw, 17vh, 0) scale(1.12);
  }
}

@keyframes drift-two {
  from {
    transform: translate3d(3%, 5%, 0) scale(1);
  }

  to {
    transform: translate3d(-20vw, -15vh, 0) scale(0.88);
  }
}
</style>
