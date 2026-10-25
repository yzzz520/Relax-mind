<!-- 黑胶粒子环：Canvas 2D 绘制香槟金星尘、外圈光斑与缓慢环绕。 -->
<!-- 输入播放状态与主题色，输出不含交互的装饰性环形粒子层。 -->
<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  isPlaying: Boolean,
})

const canvas = ref(null)
let context
let frameId = 0
let resizeObserver
let particles = []
let width = 1
let height = 1
let dpr = 1
let lastTime = 0
let previousFrame = 0
let visible = true
let reducedMotion = false

const GOLD = [
  [244, 225, 184],
  [218, 184, 122],
  [172, 132, 75],
  [255, 241, 207],
]

function seeded(seed) {
  let value = seed >>> 0
  return () => {
    value = (value + 0x6d2b79f5) >>> 0
    let next = value
    next = Math.imul(next ^ (next >>> 15), next | 1)
    next ^= next + Math.imul(next ^ (next >>> 7), next | 61)
    return ((next ^ (next >>> 14)) >>> 0) / 4294967296
  }
}

function buildParticles() {
  const count = width < 400 ? 680 : 1180
  const random = seeded(20261025)
  particles = Array.from({ length: count }, (_, index) => {
    const outerBand = random() > 0.78
    const outward = outerBand
      ? 0.24 + Math.pow(random(), 1.6) * 0.42
      : Math.pow(random(), 2.8) * 0.24
    const bokeh = outerBand && random() > 0.7
    const color = GOLD[index % GOLD.length]
    return {
      angle: random() * Math.PI * 2,
      radius: 0.93 + outward,
      size:
        (0.34 + outward * 1.15 + (bokeh ? 1.2 + random() * 2.4 : 0)) *
        (0.82 + random() * 0.38),
      alpha: (bokeh ? 0.2 : 0.28) + random() * (bokeh ? 0.34 : 0.48),
      color,
      bokeh,
      speed: (0.002 + random() * 0.006) * (random() > 0.18 ? 1 : -0.62),
      phase: random() * Math.PI * 2,
      twinkle: 0.00045 + random() * 0.00115,
      drift: 0.5 + random() * 2.4,
      driftSpeed: 0.00015 + random() * 0.00035,
      depth: 0.55 + random() * 0.55,
    }
  })
}

function resize() {
  if (!canvas.value) return
  width = Math.max(1, canvas.value.clientWidth)
  height = Math.max(1, canvas.value.clientHeight)
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  canvas.value.width = Math.round(width * dpr)
  canvas.value.height = Math.round(height * dpr)
  context = canvas.value.getContext('2d')
  context.setTransform(dpr, 0, 0, dpr, 0, 0)
  buildParticles()
  draw(performance.now(), 0)
}

function paintParticle(x, y, size, alpha, color, bokeh) {
  const [red, green, blue] = color
  context.beginPath()
  context.arc(x, y, size, 0, Math.PI * 2)

  if (bokeh) {
    const gradient = context.createRadialGradient(x, y, 0, x, y, size * 1.8)
    gradient.addColorStop(0, `rgba(${red}, ${green}, ${blue}, ${alpha})`)
    gradient.addColorStop(0.48, `rgba(${red}, ${green}, ${blue}, ${alpha * 0.5})`)
    gradient.addColorStop(1, `rgba(${red}, ${green}, ${blue}, 0)`)
    context.fillStyle = gradient
    context.arc(x, y, size * 1.8, 0, Math.PI * 2)
  } else {
    context.fillStyle = `rgba(${red}, ${green}, ${blue}, ${alpha})`
  }

  context.fill()
}

function draw(now, elapsed) {
  if (!context) return
  context.clearRect(0, 0, width, height)
  const centerX = width / 2
  const centerY = height / 2
  const baseRadius = Math.min(width, height) * 0.425
  const direction = props.isPlaying ? 1 : 0.34

  context.save()
  context.translate(centerX, centerY)
  context.scale(1.27, 0.72)
  const halo = context.createRadialGradient(
    0,
    0,
    baseRadius * 0.86,
    0,
    0,
    baseRadius * 1.38,
  )
  halo.addColorStop(0, 'rgba(218, 184, 122, 0)')
  halo.addColorStop(0.34, 'rgba(218, 184, 122, 0.1)')
  halo.addColorStop(0.58, 'rgba(239, 218, 166, 0.14)')
  halo.addColorStop(1, 'rgba(218, 184, 122, 0)')
  context.fillStyle = halo
  context.beginPath()
  context.arc(0, 0, baseRadius * 1.38, 0, Math.PI * 2)
  context.fill()
  context.restore()
  context.save()
  context.globalCompositeOperation = 'lighter'

  for (const particle of particles) {
    particle.angle += particle.speed * elapsed * 0.001 * direction
    const radial =
      baseRadius *
      (particle.radius +
        Math.sin(now * particle.driftSpeed + particle.phase) *
          (particle.drift / baseRadius))
    const x = centerX + Math.cos(particle.angle) * radial * 1.27
    const y =
      centerY +
      Math.sin(particle.angle) * radial * 0.72 +
      Math.sin(now * particle.driftSpeed * 0.7 + particle.phase) * 3
    const twinkle = 0.58 + 0.42 * Math.sin(now * particle.twinkle + particle.phase)
    const alpha =
      particle.alpha *
      twinkle *
      (0.62 + particle.depth * 0.38) *
      Math.max(0.18, 1 - Math.abs(x - centerX) / (width * 0.62))
    const size = particle.size * (0.72 + particle.depth * 0.5)
    paintParticle(x, y, size, alpha, particle.color, particle.bokeh)
  }
  context.restore()
}

function animate(now) {
  if (!visible || document.hidden) {
    frameId = 0
    return
  }

  const elapsed = lastTime ? Math.min(50, now - lastTime) : 16
  lastTime = now
  if (now - previousFrame >= 30) {
    draw(now, elapsed)
    previousFrame = now
  }
  frameId = window.requestAnimationFrame(animate)
}

function start() {
  window.cancelAnimationFrame(frameId)
  frameId = 0
  lastTime = 0
  if (reducedMotion) {
    draw(performance.now(), 0)
    return
  }
  frameId = window.requestAnimationFrame(animate)
}

function handleVisibility() {
  if (!document.hidden) start()
}

watch(
  () => props.isPlaying,
  () => {
    if (reducedMotion) draw(performance.now(), 0)
  },
)

onMounted(() => {
  reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(canvas.value)
  document.addEventListener('visibilitychange', handleVisibility)
  resize()
  start()
})

onBeforeUnmount(() => {
  window.cancelAnimationFrame(frameId)
  resizeObserver?.disconnect()
  document.removeEventListener('visibilitychange', handleVisibility)
  particles = []
  context = null
})
</script>

<template>
  <div class="vinyl-halo">
    <canvas ref="canvas" aria-hidden="true"></canvas>
  </div>
</template>

<style scoped>
.vinyl-halo,
.vinyl-halo canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.vinyl-halo {
  overflow: hidden;
  pointer-events: none;
}

.vinyl-halo canvas {
  display: block;
}
</style>
