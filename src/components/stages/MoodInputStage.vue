<!-- 输入态组件：收集情绪文本、校验长度并触发分析。 -->
<!-- 输入双向绑定的文本，输出 submit / retry 事件。 -->
<script setup>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
} from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  isError: Boolean,
})

const emit = defineEmits(['update:modelValue', 'submit', 'retry'])
const textarea = ref(null)
const isShaking = ref(false)
const isSubmitting = ref(false)
const validationMessage = ref('')
let shakeTimer

const count = computed(() => props.modelValue.length)
const canSubmit = computed(() => props.modelValue.trim().length >= 4)
const isEmpty = computed(() => props.modelValue.trim().length === 0)

function handleInput(event) {
  const value = event.target.value.slice(0, 200)
  event.target.value = value
  emit('update:modelValue', value)
  validationMessage.value = ''
}

function triggerShake() {
  validationMessage.value = '再多说一点'
  isShaking.value = false
  window.requestAnimationFrame(() => {
    isShaking.value = true
  })
  window.clearTimeout(shakeTimer)
  shakeTimer = window.setTimeout(() => {
    isShaking.value = false
  }, 300)
}

function handleSubmit() {
  if (isSubmitting.value || isEmpty.value) {
    return
  }

  if (!canSubmit.value) {
    triggerShake()
    return
  }

  isSubmitting.value = true
  nextTick(() => {
    emit('submit', props.modelValue)
  })
}

function handleShortcut(event) {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault()
    handleSubmit()
  }
}

function handleRetry() {
  validationMessage.value = ''
  emit('retry')
}

onMounted(() => {
  nextTick(() => textarea.value?.focus())
})

onBeforeUnmount(() => {
  window.clearTimeout(shakeTimer)
})
</script>

<template>
  <section class="mood-stage">
    <div class="mood-content">
      <header class="intro">
        <h1>写出今天的故事，唱片为你转动</h1>
        <p>write today's story, let the record spin for you</p>
      </header>

      <form
        class="mood-form"
        :class="{ 'is-shaking': isShaking }"
        novalidate
        @submit.prevent="handleSubmit"
      >
        <textarea
          ref="textarea"
          :value="modelValue"
          maxlength="200"
          rows="4"
          placeholder="写下此刻的心情..."
          aria-label="情绪输入"
          @input="handleInput"
          @keydown="handleShortcut"
        ></textarea>

        <div class="form-footer">
          <span class="count" :class="{ warning: count > 180 }">
            {{ count }}/200
          </span>
          <button
            class="generate-button"
            :class="{ dimmed: !canSubmit }"
            type="submit"
            :disabled="isSubmitting || isEmpty"
            :aria-disabled="isSubmitting || !canSubmit"
          >
            {{ isSubmitting ? '正在解析情绪波长...' : '生成情绪胶囊 →' }}
          </button>
        </div>
      </form>

      <p v-if="validationMessage" class="validation-message" role="alert">
        {{ validationMessage }}
      </p>

      <button v-if="isError" class="retry-button" type="button" @click="handleRetry">
        解析失败，点击重试
      </button>
    </div>
  </section>
</template>

<style scoped>
.mood-stage {
  position: relative; z-index: 1; display: grid; min-height: 100dvh;
  place-items: center; padding: 96px 24px 48px;
}
.mood-content { width: min(92vw, var(--maxw-input)); }
.intro { margin-bottom: 28px; text-align: center; }
.intro h1 {
  margin: 0; color: var(--text-primary); font-size: clamp(24px, 4vw, 40px);
  font-weight: 300; letter-spacing: 0.1em;
  text-shadow: 0 0 24px rgba(124, 92, 255, 0.6), 0 0 60px rgba(124, 92, 255, 0.3);
}
.intro p {
  margin: 12px 0 0; color: var(--text-secondary); font-size: 12px;
  letter-spacing: 0.08em; opacity: 0.55;
}
.mood-form {
  padding: 18px; border: 1px solid var(--glass-border);
  border-radius: var(--radius-card); background: var(--glass-bg);
  box-shadow: 0 28px 90px rgba(0, 0, 0, 0.28), inset 0 1px rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(var(--glass-blur));
}
.mood-form.is-shaking { animation: shake 300ms ease-in-out; }
.mood-form textarea {
  width: 100%; height: 120px; max-height: 120px; padding: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px;
  outline: none; background: rgba(0, 0, 0, 0.14); color: var(--text-primary);
  font-size: 15px; line-height: 1.7; resize: none;
  transition: border-color var(--dur-fast) var(--ease-soft),
    box-shadow var(--dur-fast) var(--ease-soft);
}
.mood-form textarea:focus {
  border-color: rgba(124, 92, 255, 0.62);
  box-shadow: 0 0 0 3px rgba(124, 92, 255, 0.1);
}
.mood-form textarea::placeholder { color: rgba(255, 255, 255, 0.28); }
.form-footer {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; margin-top: 14px;
}
.count {
  color: var(--text-secondary); font-size: 12px;
  font-variant-numeric: tabular-nums;
}
.count.warning { color: #ffd166; }
.generate-button {
  min-height: 42px; padding: 0 17px; border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px; background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary); font-size: 13px;
  transition: opacity var(--dur-fast) var(--ease-soft),
    background var(--dur-fast) var(--ease-soft);
}
.generate-button:hover:not(:disabled) { background: rgba(255, 255, 255, 0.16); }
.generate-button.dimmed { opacity: 0.4; }
.generate-button:disabled { cursor: not-allowed; }
.validation-message,
.retry-button {
  margin: 12px 0 0; color: #ff9fbd; font-size: 12px; text-align: center;
}
.retry-button {
  display: block; width: 100%; padding: 0; border: 0; background: transparent;
}
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-8px); }
  40% { transform: translateX(8px); }
  60% { transform: translateX(-6px); }
  80% { transform: translateX(6px); }
}
@media (max-width: 560px) {
  .mood-stage { padding: 88px 4vw 32px; }
  .intro h1 { font-size: 24px; }
  .form-footer { align-items: stretch; flex-direction: column-reverse; }
  .generate-button { width: 100%; }
  .count { text-align: right; }
}
</style>
