<!-- 解析态组件：按 0-600、600-1200、1200-1800ms 依次展示三条文案。 -->
<!-- 输入实时关键词，输出全屏解析遮罩与第三条呼吸态。 -->
<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  keywords: {
    type: Array,
    default: () => [],
  },
})

const activeIndex = ref(0)
const isVisible = ref(false)
const isBreathing = ref(false)
const timers = []
let frameId

const messages = computed(() => [
  `正在提取关键词：[${props.keywords.join(', ')}]...`,
  '情感向量计算中...',
  '正在为你寻找专属旋律...',
])

function schedule(callback, delay) {
  timers.push(window.setTimeout(callback, delay))
}

onMounted(() => {
  frameId = window.requestAnimationFrame(() => {
    isVisible.value = true
  })

  schedule(() => {
    isVisible.value = false
  }, 400)
  schedule(() => {
    activeIndex.value = 1
    isVisible.value = true
  }, 600)
  schedule(() => {
    isVisible.value = false
  }, 1000)
  schedule(() => {
    activeIndex.value = 2
    isVisible.value = true
  }, 1200)
  schedule(() => {
    isBreathing.value = true
  }, 1600)
})

onBeforeUnmount(() => {
  window.cancelAnimationFrame(frameId)
  timers.forEach((timer) => window.clearTimeout(timer))
})
</script>

<template>
  <div class="analyzing-stage" aria-live="polite">
    <p
      class="analysis-text"
      :class="{ visible: isVisible, breathing: isBreathing }"
    >
      {{ messages[activeIndex] }}
    </p>
  </div>
</template>

<style scoped>
.analyzing-stage {
  position: fixed;
  z-index: 10;
  display: grid;
  inset: 0;
  place-items: center;
  padding: 24px;
  background: rgba(11, 10, 20, 0.78);
  backdrop-filter: blur(10px);
}

.analysis-text {
  max-width: 860px;
  margin: 0;
  color: var(--text-primary);
  font-size: clamp(20px, 2.2vw, 24px);
  font-weight: 300;
  letter-spacing: 0.04em;
  line-height: 1.7;
  text-align: center;
  opacity: 0;
  transform: translateY(4px);
  transition:
    opacity var(--dur-fast) var(--ease-soft),
    transform var(--dur-fast) var(--ease-soft);
}

.analysis-text.visible {
  opacity: 1;
  transform: translateY(0);
}

.analysis-text.breathing {
  animation: breathe 1200ms ease-in-out infinite;
}

@keyframes breathe {
  0%,
  100% {
    opacity: 0.5;
  }

  50% {
    opacity: 1;
  }
}

@media (max-width: 560px) {
  .analysis-text {
    max-width: 92vw;
    font-size: 18px;
  }
}
</style>
