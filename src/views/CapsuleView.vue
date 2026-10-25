<!-- 情绪胶囊页：承载输入、解析、错误与结果页的状态机容器。 -->
<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AnalyzingStage from '../components/stages/AnalyzingStage.vue'
import MoodInputStage from '../components/stages/MoodInputStage.vue'
import ResultStage from '../components/stages/ResultStage.vue'
import AuroraBackground from '../components/AuroraBackground.vue'
import { useEmotionFlow } from '../composables/useEmotionFlow'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const { stage, inputText, capsule, keywords, submit, reset } = useEmotionFlow()

const bgIntensity = computed(() => {
  if (stage.value === 'analyzing') return 1
  if (stage.value === 'result') return 0.6
  return 0.3
})

function handleLogout() {
  auth.logout()
  router.replace('/login')
}

function handleRestart() {
  reset()
  inputText.value = ''
}
</script>

<template>
  <div class="capsule-root">
    <AuroraBackground
      :intensity="bgIntensity"
      :colors="capsule?.palette ?? undefined"
    />

    <header class="capsule-header">
      <span class="brand">AI 情绪胶囊</span>
      <div class="header-actions">
        <span class="user">{{ auth.nickname }}</span>
        <button class="logout-button" type="button" @click="handleLogout">
          退出
        </button>
      </div>
    </header>

    <Transition name="stage" mode="out-in">
      <MoodInputStage
        v-if="stage === 'input' || stage === 'error'"
        key="input"
        v-model="inputText"
        :is-error="stage === 'error'"
        @submit="submit"
        @retry="reset"
      />
      <AnalyzingStage
        v-else-if="stage === 'analyzing'"
        key="analyzing"
        :keywords="keywords"
      />
      <ResultStage
        v-else-if="capsule"
        key="result"
        :capsule="capsule"
        @restart="handleRestart"
      />
      <div v-else key="result-fallback" class="result-placeholder">
        正在整理情绪结果
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.capsule-root {
  position: relative;
  min-height: 100dvh;
  overflow-x: hidden;
  background: var(--bg-base);
}

.capsule-header {
  position: absolute;
  z-index: 3;
  top: 0;
  right: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28px 36px;
  color: var(--text-secondary);
  font-size: 12px;
  letter-spacing: 0.08em;
}

.brand {
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 18px;
}

.user {
  max-width: 40%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logout-button {
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  letter-spacing: inherit;
  opacity: 0.55;
  transition: opacity var(--dur-fast) var(--ease-soft);
}

.logout-button:hover {
  opacity: 1;
}

.stage-enter-active {
  transition:
    opacity var(--dur-base) var(--ease-soft),
    transform var(--dur-base) var(--ease-soft);
}

.stage-leave-active {
  transition: none;
}

.stage-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.stage-leave-to {
  opacity: 0;
}

.result-placeholder {
  position: relative;
  z-index: 1;
  display: grid;
  min-height: 100dvh;
  place-items: center;
  color: var(--text-secondary);
  font-size: 14px;
  letter-spacing: 0.08em;
}

@media (max-width: 560px) {
  .capsule-header {
    padding: 22px 20px;
  }
}
</style>
