<!-- 管理后台：拉取记录、筛选数据并组合统计卡、图表和表格。 -->
<!-- 输入管理员会话，输出只读的全站情绪概览。 -->
<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { fetchRecords } from '../api/admin'
import DailyLine from '../components/admin/DailyLine.vue'
import EmotionBar from '../components/admin/EmotionBar.vue'
import RecordsTable from '../components/admin/RecordsTable.vue'
import StatCards from '../components/admin/StatCards.vue'
import { useAuthStore } from '../stores/auth'
import { computeStats } from '../utils/stats'

const router = useRouter()
const auth = useAuthStore()
const records = ref([])
const loading = ref(true)
const errorMessage = ref('')
const quadrantFilter = ref('')
const rangeFilter = ref('')
let requestId = 0

const quadrantOptions = [
  { value: '', label: '全部' },
  { value: 'melancholic', label: '低落' },
  { value: 'anxious', label: '紧绷' },
  { value: 'joyful', label: '明亮' },
  { value: 'calm', label: '平静' },
]

const rangeOptions = [
  { value: '', label: '全部时间' },
  { value: '7', label: '近 7 天' },
  { value: '30', label: '近 30 天' },
]

const hasFilters = computed(
  () => Boolean(quadrantFilter.value || rangeFilter.value),
)
const stats = computed(() => computeStats(records.value))

async function loadRecords() {
  const currentRequest = ++requestId
  loading.value = true
  errorMessage.value = ''

  try {
    const data = await fetchRecords({
      quadrant: quadrantFilter.value || null,
      days: rangeFilter.value ? Number(rangeFilter.value) : null,
    })
    if (currentRequest === requestId) {
      records.value = data
    }
  } catch (error) {
    if (currentRequest === requestId) {
      records.value = []
      errorMessage.value =
        error instanceof Error ? error.message : '读取管理数据失败'
    }
  } finally {
    if (currentRequest === requestId) {
      loading.value = false
    }
  }
}

function clearFilters() {
  quadrantFilter.value = ''
  rangeFilter.value = ''
}

async function handleLogout() {
  await auth.logout()
  router.replace('/login')
}

watch([quadrantFilter, rangeFilter], loadRecords)
onMounted(loadRecords)
</script>

<template>
  <main class="admin-page">
    <div class="admin-shell">
      <header class="admin-header">
        <span class="brand">AI 情绪胶囊</span>
        <div class="header-actions">
          <span class="role">管理员 · {{ auth.nickname }}</span>
          <button class="logout-button" type="button" @click="handleLogout">
            退出
          </button>
        </div>
      </header>

      <section class="page-intro">
        <p class="eyebrow">OPERATIONS</p>
        <h1>情绪概览</h1>
        <p>观察最近的表达、情绪分布与生成趋势</p>
      </section>

      <div v-if="errorMessage" class="error-banner" role="alert">
        <span>{{ errorMessage }}</span>
        <button type="button" @click="loadRecords">重试</button>
      </div>

      <div v-if="loading && !records.length" class="loading-layout">
        <div class="skeleton-stats">
          <span v-for="index in 4" :key="index"></span>
        </div>
        <div class="skeleton-charts">
          <span></span>
          <span></span>
        </div>
        <div class="skeleton-table"></div>
      </div>

      <template v-else>
        <StatCards :stats="stats" />

        <div v-if="records.length" class="chart-grid">
          <section class="panel chart-panel">
            <header class="panel-heading">
              <h2>八维情绪均值</h2>
              <span>0–100</span>
            </header>
            <EmotionBar :emotion-avg="stats.emotionAvg" />
          </section>
          <section class="panel chart-panel">
            <header class="panel-heading">
              <h2>最近 7 天生成量</h2>
              <span>Asia / Shanghai</span>
            </header>
            <DailyLine :daily="stats.daily" />
          </section>
        </div>

        <section class="records-panel">
          <header class="records-heading">
            <div>
              <h2>情绪记录</h2>
              <span>{{ records.length }} 条记录</span>
            </div>
            <div class="filters">
              <div class="filter-group" aria-label="按象限筛选">
                <button
                  v-for="option in quadrantOptions"
                  :key="option.value"
                  type="button"
                  :class="{ active: quadrantFilter === option.value }"
                  @click="quadrantFilter = option.value"
                >
                  {{ option.label }}
                </button>
              </div>
              <select v-model="rangeFilter" aria-label="按时间范围筛选">
                <option
                  v-for="option in rangeOptions"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>
            </div>
          </header>

          <RecordsTable
            v-if="records.length"
            :records="records"
            :loading="loading"
          />

          <div v-else class="empty-state">
            <span class="empty-mark" aria-hidden="true"></span>
            <h2>{{ hasFilters ? '当前筛选条件下没有记录' : '还没有情绪记录' }}</h2>
            <p>
              {{
                hasFilters
                  ? '换一个情绪象限或时间范围再看看'
                  : '用户生成胶囊后，这里会显示情绪分布与趋势'
              }}
            </p>
            <button
              type="button"
              @click="hasFilters ? clearFilters() : router.push('/')"
            >
              {{ hasFilters ? '清除筛选' : '去生成第一条' }}
            </button>
          </div>
        </section>
      </template>
    </div>
  </main>
</template>

<style scoped src="../assets/styles/admin.css"></style>
