<!-- Ported from reactbits.dev/backgrounds/particles (MIT) -->
<!-- 改动：React hooks 改为 Vue 生命周期；GLSL 与渲染逻辑保持原样。 -->
<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { createParticlesRenderer } from './renderers/particlesRenderer'
const props = defineProps({
  particleCount: {
    type: Number,
    default: 200,
  },
  particleSpread: {
    type: Number,
    default: 10,
  },
  speed: {
    type: Number,
    default: 0.1,
  },
  particleColors: {
    type: Array,
    default: () => ['#ffffff'],
  },
  moveParticlesOnHover: {
    type: Boolean,
    default: true,
  },
  particleHoverFactor: {
    type: Number,
    default: 1,
  },
  alphaParticles: {
    type: Boolean,
    default: false,
  },
  particleBaseSize: {
    type: Number,
    default: 100,
  },
  sizeRandomness: {
    type: Number,
    default: 1,
  },
  cameraDistance: {
    type: Number,
    default: 20,
  },
  disableRotation: {
    type: Boolean,
    default: false,
  },
  pixelRatio: {
    type: Number,
    default: undefined,
  },
  shape: {
    type: String,
    default: 'circle',
  },
  glow: {
    type: Number,
    default: 0.5,
  },
  twinkle: {
    type: Number,
    default: 0.3,
  },
  depthOfField: {
    type: Number,
    default: 0,
  },
  connections: {
    type: Boolean,
    default: false,
  },
  connectionDistance: {
    type: Number,
    default: 110,
  },
  hoverEffect: {
    type: String,
    default: 'parallax',
  },
  hoverRadius: {
    type: Number,
    default: 140,
  },
  clickBurst: {
    type: Boolean,
    default: true,
  },
  drift: {
    type: String,
    default: 'none',
  },
  driftSpeed: {
    type: Number,
    default: 1,
  },
  variation: {
    type: Number,
    default: 0,
  },
  intro: {
    type: Boolean,
    default: true,
  },
  opacity: {
    type: Number,
    default: 1,
  },
  lightMode: {
    type: Boolean,
    default: false,
  },
  paused: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['unsupported'])
const container = ref(null)
const canvas = ref(null)
const unsupported = ref(false)
const settingsRef = { current: null }
const wakeRef = { current: null }
let cleanupRenderer = null

const SHAPES = { circle: 0, square: 1, ring: 2, sparkle: 3 }
const EFFECTS = { parallax: 0, repel: 1, attract: 2 }
const DRIFTS = { none: 0, up: 1, down: 2, forward: 3 }
const clamp = (value, min, max) => Math.min(max, Math.max(min, value))

function buildSettings() {
  const colors = (
    Array.isArray(props.particleColors)
      ? props.particleColors
      : [props.particleColors]
  )
    .filter(Boolean)
    .map(String)

  return {
    count: clamp(Math.round(props.particleCount), 1, 20000),
    spread: Math.max(0.1, props.particleSpread),
    speed: props.speed,
    colors: colors.length ? colors : ['#ffffff'],
    mouse: props.moveParticlesOnHover,
    hoverFactor: Math.max(0, props.particleHoverFactor),
    soft: props.alphaParticles,
    size: Math.max(0, props.particleBaseSize),
    randomness: Math.max(0, props.sizeRandomness),
    camera: Math.max(1, props.cameraDistance),
    rotate: !props.disableRotation,
    dpr: props.pixelRatio,
    shape: SHAPES[props.shape] ?? 0,
    glow: Math.max(0, props.glow),
    twinkle: clamp(props.twinkle, 0, 1),
    depthOfField: Math.max(0, props.depthOfField),
    connections: props.connections,
    connectionDistance: Math.max(10, props.connectionDistance),
    hoverEffect: EFFECTS[props.hoverEffect] ?? 0,
    hoverRadius: Math.max(20, props.hoverRadius),
    clickBurst: props.clickBurst,
    drift: DRIFTS[props.drift] ?? 0,
    driftSpeed: props.driftSpeed,
    variation: Math.max(0, Math.round(props.variation)),
    intro: props.intro,
    opacity: clamp(props.opacity, 0, 1),
    lightMode: props.lightMode,
    paused: props.paused,
  }
}

settingsRef.current = buildSettings()

function mountRenderer() {
  cleanupRenderer?.()
  cleanupRenderer = null
  if (!container.value || !canvas.value) return

  unsupported.value = false
  cleanupRenderer = createParticlesRenderer({
    container: container.value,
    canvas: canvas.value,
    settingsRef,
    wakeRef,
    onUnsupported: () => {
      unsupported.value = true
      emit('unsupported')
    },
  })
}

watch(
  () => ({ ...props }),
  () => {
    settingsRef.current = buildSettings()
    wakeRef.current?.()
  },
  { deep: true },
)

onMounted(mountRenderer)

onBeforeUnmount(() => {
  cleanupRenderer?.()
  cleanupRenderer = null
  wakeRef.current = null
})
</script>

<template>
  <div ref="container" class="particles-container">
    <canvas ref="canvas" class="particles-canvas" aria-hidden="true"></canvas>
    <div v-if="unsupported" class="particles-fallback" aria-hidden="true"></div>
  </div>
</template>

<style scoped>
.particles-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 50%, rgba(124, 92, 255, 0.28), transparent 70%),
    var(--bg-base);
}

.particles-canvas,
.particles-fallback {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.particles-canvas {
  display: block;
}

.particles-fallback {
  background:
    radial-gradient(circle at 42% 38%, rgba(255, 255, 255, 0.5), transparent 8%),
    radial-gradient(circle at 66% 58%, rgba(255, 143, 177, 0.42), transparent 11%),
    radial-gradient(circle at 52% 66%, rgba(124, 92, 255, 0.58), transparent 48%),
    var(--bg-base);
}
</style>
