<!-- 疗愈语：逐字展示带主题色竖线并由关键词自然引出的 AI 寄语。 -->
<!-- 输入 comment、palette，输出打字机文本与完成态。 -->
<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  comment: {
    type: String,
    default: '',
  },
  palette: {
    type: Array,
    default: () => ['#7C5CFF', '#FF8FB1'],
  },
})

const paragraphs = ref([''])
const isTyping = ref(true)
let typeTimer
let motionQuery

const fullParagraphs = computed(() =>
  props.comment.split(/\r?\n/).map((paragraph) => paragraph.trim()),
)

function finishTyping() {
  window.clearTimeout(typeTimer)
  paragraphs.value = [...fullParagraphs.value]
  isTyping.value = false
}

function typeNextCharacter(index = 0) {
  if (!isTyping.value) {
    return
  }

  if (motionQuery?.matches || index >= props.comment.length) {
    finishTyping()
    return
  }

  const character = props.comment[index]
  const lastIndex = paragraphs.value.length - 1

  if (character === '\n') {
    paragraphs.value.push('')
  } else {
    paragraphs.value[lastIndex] += character
  }

  const punctuationPause = /[，。！？；：,.!?;]/.test(character)
    ? 120
    : 0
  typeTimer = window.setTimeout(
    () => typeNextCharacter(index + 1),
    28 + punctuationPause,
  )
}

function startTyping() {
  window.clearTimeout(typeTimer)
  paragraphs.value = ['']
  isTyping.value = true

  if (motionQuery?.matches) {
    finishTyping()
    return
  }

  typeNextCharacter()
}

watch(() => props.comment, startTyping)

onMounted(() => {
  motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  startTyping()
})

onBeforeUnmount(() => {
  window.clearTimeout(typeTimer)
})
</script>

<template>
  <section
    class="healing"
    :style="{ '--accent': palette[0] }"
    aria-label="AI 疗愈语"
  >
    <blockquote class="comment">
      <p v-for="(paragraph, index) in paragraphs" :key="index">
        {{ paragraph }}<span
          v-if="isTyping && index === paragraphs.length - 1"
          class="typing-cursor"
          aria-hidden="true"
        >▌</span>
      </p>
    </blockquote>
  </section>
</template>

<style scoped>
.healing {
  padding: 8px 4px;
  opacity: 0;
  animation: comment-in 600ms var(--ease-soft) 300ms forwards;
}

.comment {
  margin: 0;
  padding: 2px 0 2px 16px;
  border-left: 2px solid var(--accent);
  color: var(--text-primary);
  font-size: 17px;
  font-weight: 300;
  line-height: 1.9;
}

.comment p {
  margin: 0;
}

.comment p + p {
  margin-top: 0.35em;
}

.typing-cursor {
  display: inline-block;
  margin-left: 2px;
  animation: cursor-blink 1s step-end infinite;
}

@keyframes comment-in {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes cursor-blink {
  50% {
    opacity: 0;
  }
}

@media (max-width: 560px) {
  .healing {
    padding: 0 4px;
  }

  .comment {
    font-size: 14px;
    font-weight: 400;
    line-height: 1.75;
  }
}
</style>
