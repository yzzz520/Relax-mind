<!-- 管理后台页：S1 阶段仅作为管理员登录后的路由占位容器。 -->
<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

async function handleLogout() {
  await auth.logout()
  router.replace('/login')
}
</script>

<template>
  <main class="shell">
    <header class="shell-header">
      <span class="shell-brand">AI 情绪胶囊</span>
      <div class="shell-actions">
        <span class="shell-role">管理员 · {{ auth.nickname }}</span>
        <button class="logout-button" type="button" @click="handleLogout">
          退出
        </button>
      </div>
    </header>

    <section class="placeholder">
      <span class="placeholder-mark" aria-hidden="true"></span>
      <p class="placeholder-kicker">ADMIN</p>
      <h1>管理后台</h1>
      <p class="placeholder-copy">记录列表与统计图表将在后续批次接入</p>
    </section>
  </main>
</template>

<style scoped>
.shell {
  display: flex;
  min-height: 100dvh;
  flex-direction: column;
  padding: 28px 36px 36px;
  background:
    linear-gradient(215deg, rgba(255, 143, 177, 0.055), transparent 38%),
    var(--bg-base);
}

.shell-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--text-secondary);
  font-size: 12px;
  letter-spacing: 0.08em;
}

.shell-brand {
  color: var(--text-primary);
}

.shell-actions {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 18px;
}

.shell-role {
  max-width: 45%;
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

.placeholder {
  display: grid;
  width: min(100%, 560px);
  margin: auto;
  justify-items: center;
  padding: 44px;
  text-align: center;
}

.placeholder-mark {
  width: 9px;
  height: 9px;
  margin-bottom: 26px;
  border-radius: 50%;
  background: var(--bg-aurora-1);
  box-shadow: 0 0 24px rgba(124, 92, 255, 0.8);
}

.placeholder-kicker {
  margin: 0 0 12px;
  color: var(--text-secondary);
  font-size: 11px;
  letter-spacing: 0.18em;
}

.placeholder h1 {
  margin: 0;
  color: var(--text-primary);
  font-size: clamp(26px, 4vw, 38px);
  font-weight: 300;
  letter-spacing: 0.06em;
  text-shadow:
    0 0 24px rgba(124, 92, 255, 0.45),
    0 0 60px rgba(124, 92, 255, 0.2);
}

.placeholder-copy {
  margin: 16px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

@media (max-width: 560px) {
  .shell {
    padding: 22px 20px 28px;
  }

  .placeholder {
    padding: 32px 8px;
  }
}
</style>
