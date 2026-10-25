<!-- Ported from reactbits.dev/backgrounds/lightfall (MIT) -->
<!-- 改动：React hooks 改为 Vue 生命周期；GLSL 与渲染逻辑保持原样。 -->
<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { createLightfallRenderer } from './renderers/lightfallRenderer'

const props = defineProps({
  colors: {
    type: Array,
    default: () => ['#ffffff'],
  },
  backgroundColor: {
    type: String,
    default: '#94a3b8',
  },
  speed: {
    type: Number,
    default: 0.3,
  },
  streakCount: {
    type: Number,
    default: 2,
  },
  streakWidth: {
    type: Number,
    default: 0.8,
  },
  streakLength: {
    type: Number,
    default: 1,
  },
  glow: {
    type: Number,
    default: 1,
  },
  density: {
    type: Number,
    default: 0.6,
  },
  twinkle: {
    type: Number,
    default: 0.3,
  },
  zoom: {
    type: Number,
    default: 3,
  },
  backgroundGlow: {
    type: Number,
    default: 0.1,
  },
  headGlow: {
    type: Number,
    default: 0.6,
  },
  depth: {
    type: Number,
    default: 0.5,
  },
  bloom: {
    type: Number,
    default: 0.35,
  },
  opacity: {
    type: Number,
    default: 1,
  },
  mouseInteraction: {
    type: Boolean,
    default: true,
  },
  mouseStrength: {
    type: Number,
    default: 0.4,
  },
  mouseRadius: {
    type: Number,
    default: 0.45,
  },
  mouseDampening: {
    type: Number,
    default: 0.15,
  },
  lens: {
    type: Number,
    default: 0.5,
  },
  holdToWarp: {
    type: Boolean,
    default: true,
  },
  intro: {
    type: Boolean,
    default: true,
  },
  fade: {
    type: Number,
    default: 0,
  },
  lightMode: {
    type: Boolean,
    default: false,
  },
  paused: {
    type: Boolean,
    default: false,
  },
  dpr: {
    type: Number,
    default: undefined,
  },
})

const emit = defineEmits(['unsupported'])
const container = ref(null)
const canvas = ref(null)
const unsupported = ref(false)
const settingsRef = { current: null }
const wakeRef = { current: null }
let cleanupRenderer = null

const clamp = (value, min, max) => Math.min(max, Math.max(min, value))

function buildSettings() {
  return {
    colors: (
      Array.isArray(props.colors) && props.colors.length
        ? props.colors
        : ['#ffffff']
    )
      .slice(0, 8)
      .map(String),
    backgroundColor: String(props.backgroundColor),
    speed: props.speed,
    streakCount: Math.round(clamp(props.streakCount, 1, 16)),
    streakWidth: Math.max(0.05, props.streakWidth),
    streakLength: Math.max(0.05, props.streakLength),
    glow: Math.max(0, props.glow),
    density: props.density,
    twinkle: clamp(props.twinkle, 0, 1),
    zoom: Math.max(0.1, props.zoom),
    backgroundGlow: Math.max(0, props.backgroundGlow),
    headGlow: clamp(props.headGlow, 0, 1),
    depth: Math.max(0, props.depth),
    bloom: Math.max(0, props.bloom),
    opacity: clamp(props.opacity, 0, 1),
    mouseInteraction: props.mouseInteraction,
    mouseStrength: Math.max(0, props.mouseStrength),
    mouseRadius: Math.max(0.01, props.mouseRadius),
    mouseDampening: Math.max(0, props.mouseDampening),
    lens: clamp(props.lens, 0, 1),
    holdToWarp: props.holdToWarp,
    intro: props.intro,
    fade: clamp(props.fade, 0, 1),
    lightMode: props.lightMode,
    paused: props.paused,
    dpr: props.dpr,
  }
}

settingsRef.current = buildSettings()

function mountRenderer() {
  cleanupRenderer?.()
  cleanupRenderer = null
  if (!container.value || !canvas.value) return

  unsupported.value = false
  cleanupRenderer = createLightfallRenderer({
    container: container.value,
    canvas: canvas.value,
    settingsRef,
    wakeRef,
    onUnsupported: () => {
      unsupported.value = true
      emit('unsupported')
    },
    onRestart: () => {
      queueMicrotask(mountRenderer)
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
  <div ref="container" class="lightfall-container">
    <canvas ref="canvas" class="lightfall-canvas" aria-hidden="true"></canvas>
    <div v-if="unsupported" class="lightfall-fallback" aria-hidden="true"></div>
  </div>
</template>

<style scoped>
.lightfall-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 42%, rgba(124, 92, 255, 0.24), transparent 48%),
    var(--bg-base);
}

.lightfall-canvas,
.lightfall-fallback {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.lightfall-canvas {
  display: block;
}

.lightfall-fallback {
  background:
    radial-gradient(ellipse at 48% 36%, rgba(124, 92, 255, 0.34), transparent 44%),
    radial-gradient(ellipse at 62% 72%, rgba(255, 143, 177, 0.12), transparent 48%),
    var(--bg-base);
}
</style>
