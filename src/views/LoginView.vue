<!-- 登录页：负责用户与管理员身份切换及登录提交。 -->
<!-- 输入昵称或管理员凭据，输出登录态并跳转到对应页面。 -->
<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { adminLogin, login } from '../api/auth'
import Lightfall from '../components/fx/Lightfall.vue'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activeMode = ref(route.query.from === 'admin' ? 'admin' : 'user')
const nickname = ref('')
const username = ref('')
const password = ref('')
const errorMessage = ref('')
const isSubmitting = ref(false)

const isUserMode = computed(() => activeMode.value === 'user')
const submitLabel = computed(() => {
  if (isSubmitting.value) {
    return isUserMode.value ? '正在进入' : '正在登录'
  }

  return isUserMode.value ? '进入' : '登录'
})

function switchMode(mode) {
  if (isSubmitting.value) {
    return
  }

  activeMode.value = mode
  errorMessage.value = ''
}

async function handleUserSubmit() {
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    const result = await login(nickname.value)
    auth.setAuth(result)
    await router.push({ name: 'capsule' })
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '登录失败，请重试'
  } finally {
    isSubmitting.value = false
  }
}

async function handleAdminSubmit() {
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    const result = await adminLogin(username.value, password.value)
    auth.setAuth(result)
    await router.push({ name: 'admin' })
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '登录失败，请重试'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <Lightfall
      class="login-lightfall"
      :colors="['#7c5cff']"
      background-color="#0b0a14"
      :speed="0.6"
    />
    <div class="login-scrim" aria-hidden="true"></div>

    <header class="brand">
      <span class="brand-mark" aria-hidden="true"></span>
      <span>AI 情绪胶囊</span>
    </header>

    <section class="login-panel" aria-labelledby="login-title">
      <div class="panel-heading">
        <span class="panel-rule" aria-hidden="true"></span>
        <h1 id="login-title">进入你的情绪空间</h1>
        <p>选择身份后继续</p>
      </div>

      <div class="mode-tabs" role="tablist" aria-label="登录身份">
        <button
          class="mode-tab"
          :class="{ active: isUserMode }"
          type="button"
          role="tab"
          :aria-selected="isUserMode"
          :disabled="isSubmitting"
          @click="switchMode('user')"
        >
          我是用户
        </button>
        <button
          class="mode-tab"
          :class="{ active: !isUserMode }"
          type="button"
          role="tab"
          :aria-selected="!isUserMode"
          :disabled="isSubmitting"
          @click="switchMode('admin')"
        >
          我是管理员
        </button>
      </div>

      <form
        v-if="isUserMode"
        class="login-form"
        aria-label="用户登录"
        @submit.prevent="handleUserSubmit"
      >
        <label class="field">
          <span class="field-label">昵称</span>
          <input
            v-model="nickname"
            type="text"
            name="nickname"
            autocomplete="nickname"
            placeholder="输入至少 2 个字的昵称"
            :disabled="isSubmitting"
            @input="errorMessage = ''"
          />
        </label>

        <p v-if="errorMessage" class="error-message" role="alert">
          {{ errorMessage }}
        </p>

        <button class="submit-button" type="submit" :disabled="isSubmitting">
          <span>{{ submitLabel }}</span>
          <span class="button-arrow" aria-hidden="true">→</span>
        </button>
      </form>

      <form
        v-else
        class="login-form"
        aria-label="管理员登录"
        @submit.prevent="handleAdminSubmit"
      >
        <label class="field">
          <span class="field-label">用户名</span>
          <input
            v-model="username"
            type="text"
            name="username"
            autocomplete="username"
            placeholder="输入管理员用户名"
            :disabled="isSubmitting"
            @input="errorMessage = ''"
          />
        </label>

        <label class="field">
          <span class="field-label">密码</span>
          <input
            v-model="password"
            type="password"
            name="password"
            autocomplete="current-password"
            placeholder="输入管理员密码"
            :disabled="isSubmitting"
            @input="errorMessage = ''"
          />
        </label>

        <p v-if="errorMessage" class="error-message" role="alert">
          {{ errorMessage }}
        </p>

        <button class="submit-button" type="submit" :disabled="isSubmitting">
          <span>{{ submitLabel }}</span>
          <span class="button-arrow" aria-hidden="true">→</span>
        </button>
      </form>
    </section>
  </main>
</template>

<style scoped src="../assets/styles/login.css"></style>
