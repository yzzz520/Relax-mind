<!-- 登录页：负责 Supabase 手机号登录、注册与管理员登录。 -->
<!-- 输入手机号与密码，输出 Supabase session 并跳转到对应页面。 -->
<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { adminLogin, login, register } from '../api/auth'
import Lightfall from '../components/fx/Lightfall.vue'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const activeMode = ref(route.query.from === 'admin' ? 'admin' : 'user')
const userAction = ref('login')
const phone = ref('')
const nickname = ref('')
const password = ref('')
const confirmPassword = ref('')
const adminPhone = ref('')
const adminPassword = ref('')
const errorMessage = ref('')
const isSubmitting = ref(false)

const isUserMode = computed(() => activeMode.value === 'user')
const isRegisterMode = computed(
  () => isUserMode.value && userAction.value === 'register',
)
const submitLabel = computed(() => {
  if (isSubmitting.value) {
    return isRegisterMode.value ? '正在注册' : '正在登录'
  }
  if (!isUserMode.value) return '登录管理后台'
  return isRegisterMode.value ? '注册并进入' : '登录'
})

function switchMode(mode) {
  if (isSubmitting.value) return
  activeMode.value = mode
  errorMessage.value = ''
}

function switchUserAction(action) {
  if (isSubmitting.value) return
  userAction.value = action
  password.value = ''
  confirmPassword.value = ''
  errorMessage.value = ''
}

async function handleUserSubmit() {
  errorMessage.value = ''
  if (isRegisterMode.value && password.value !== confirmPassword.value) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  isSubmitting.value = true
  try {
    const session = isRegisterMode.value
      ? await register(phone.value, nickname.value, password.value)
      : await login(phone.value, password.value)
    auth.applySession(session)
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
    const session = await adminLogin(adminPhone.value, adminPassword.value)
    auth.applySession(session)
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
        <p>手机号登录与注册</p>
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
        :aria-label="isRegisterMode ? '用户注册' : '用户登录'"
        @submit.prevent="handleUserSubmit"
      >
        <div class="auth-subtabs" role="tablist" aria-label="用户操作">
          <button
            class="auth-subtab"
            :class="{ active: !isRegisterMode }"
            type="button"
            role="tab"
            :aria-selected="!isRegisterMode"
            :disabled="isSubmitting"
            @click="switchUserAction('login')"
          >
            登录
          </button>
          <button
            class="auth-subtab"
            :class="{ active: isRegisterMode }"
            type="button"
            role="tab"
            :aria-selected="isRegisterMode"
            :disabled="isSubmitting"
            @click="switchUserAction('register')"
          >
            注册
          </button>
        </div>

        <label class="field">
          <span class="field-label">手机号</span>
          <input
            v-model="phone"
            type="tel"
            name="phone"
            inputmode="tel"
            autocomplete="tel"
            maxlength="16"
            placeholder="输入 11 位手机号"
            :disabled="isSubmitting"
            @input="errorMessage = ''"
          />
        </label>

        <label v-if="isRegisterMode" class="field">
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

        <label class="field">
          <span class="field-label">密码</span>
          <input
            v-model="password"
            type="password"
            name="password"
            :autocomplete="isRegisterMode ? 'new-password' : 'current-password'"
            :placeholder="isRegisterMode ? '至少 6 位密码' : '输入密码'"
            :disabled="isSubmitting"
            @input="errorMessage = ''"
          />
        </label>

        <label v-if="isRegisterMode" class="field">
          <span class="field-label">确认密码</span>
          <input
            v-model="confirmPassword"
            type="password"
            name="confirm-password"
            autocomplete="new-password"
            placeholder="再次输入密码"
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
          <span class="field-label">管理员手机号</span>
          <input
            v-model="adminPhone"
            type="tel"
            name="admin-phone"
            inputmode="tel"
            autocomplete="tel"
            maxlength="16"
            placeholder="输入管理员手机号"
            :disabled="isSubmitting"
            @input="errorMessage = ''"
          />
        </label>

        <label class="field">
          <span class="field-label">密码</span>
          <input
            v-model="adminPassword"
            type="password"
            name="admin-password"
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
