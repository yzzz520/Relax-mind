<!-- Ported from reactbits.dev/backgrounds/radar (MIT) -->
<!-- 改动：React hooks 改为 Vue 生命周期；GLSL 与渲染逻辑保持原样。 -->
<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { createRadarRenderer } from './renderers/radarRenderer'

const props = defineProps({
  color: { type: String, default: '#3ef09a' },
  backgroundColor: { type: String, default: 'transparent' },
  mode: { type: String, default: 'sweep' },
  speed: { type: Number, default: 1 },
  trail: { type: Number, default: 0.35 },
  scale: { type: Number, default: 0.9 },
  ringCount: { type: Number, default: 6 },
  spokeCount: { type: Number, default: 12 },
  ticks: { type: Boolean, default: true },
  targets: { type: Number, default: 6 },
  clutter: { type: Number, default: 0.35 },
  glow: { type: Number, default: 1 },
  brightness: { type: Number, default: 1 },
  gridOpacity: { type: Number, default: 1 },
  lineWidth: { type: Number, default: 1 },
  tilt: { type: Number, default: 0 },
  centerX: { type: Number, default: 0.5 },
  centerY: { type: Number, default: 0.5 },
  mouseInteraction: { type: Boolean, default: true },
  intro: { type: Boolean, default: true },
  grain: { type: Number, default: 0.03 },
  fade: { type: Number, default: 0 },
  opacity: { type: Number, default: 1 },
  lightMode: { type: Boolean, default: false },
  paused: { type: Boolean, default: false },
  dpr: { type: Number, default: undefined },
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
    color: String(props.color),
    backgroundColor: String(props.backgroundColor),
    mode: props.mode === 'pulse' ? 'pulse' : 'sweep',
    speed: props.speed,
    trail: clamp(props.trail, 0.02, 1),
    scale: Math.max(0.05, props.scale),
    ringCount: Math.round(clamp(props.ringCount, 1, 24)),
    spokeCount: Math.round(clamp(props.spokeCount, 0, 72)),
    ticks: props.ticks,
    targets: Math.round(clamp(props.targets, 0, 16)),
    clutter: clamp(props.clutter, 0, 1),
    glow: Math.max(0, props.glow),
    brightness: Math.max(0, props.brightness),
    gridOpacity: clamp(props.gridOpacity, 0, 2),
    lineWidth: clamp(props.lineWidth, 0.25, 4),
    tilt: (clamp(props.tilt, 0, 80) * Math.PI) / 180,
    centerX: props.centerX,
    centerY: props.centerY,
    mouseInteraction: props.mouseInteraction,
    intro: props.intro,
    grain: Math.max(0, props.grain),
    fade: clamp(props.fade, 0, 1),
    opacity: clamp(props.opacity, 0, 1),
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
  cleanupRenderer = createRadarRenderer({
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
  <div ref="container" class="radar-fx">
    <canvas ref="canvas" class="radar-fx-canvas" aria-hidden="true"></canvas>
    <div v-if="unsupported" class="radar-fx-fallback" aria-hidden="true"></div>
  </div>
</template>

<style scoped>
.radar-fx {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 54%, rgba(124, 92, 255, 0.16), transparent 64%),
    transparent;
}

.radar-fx-canvas,
.radar-fx-fallback {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.radar-fx-canvas {
  display: block;
}

.radar-fx-fallback {
  background:
    radial-gradient(circle, transparent 38%, rgba(124, 92, 255, 0.2) 39% 40%, transparent 41%),
    radial-gradient(circle, transparent 56%, rgba(124, 92, 255, 0.16) 57% 58%, transparent 59%),
    radial-gradient(circle, transparent 74%, rgba(124, 92, 255, 0.12) 75% 76%, transparent 77%);
}
</style>
