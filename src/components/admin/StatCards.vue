<!-- 管理统计卡：展示总量、今日、平均效价和最高情绪。 -->
<!-- 输入 computeStats 的结果，输出四个只读指标。 -->
<script setup>
import { computed } from 'vue'

const props = defineProps({
  stats: {
    type: Object,
    required: true,
  },
})

const cards = computed(() => [
  { label: '总胶囊数', value: props.stats.total, suffix: '条' },
  { label: '今日生成', value: props.stats.today, suffix: '条' },
  {
    label: '平均效价',
    value: Number(props.stats.avgValence).toFixed(2),
    suffix: '',
  },
  { label: '最常见情绪', value: props.stats.topEmotion, suffix: '' },
])
</script>

<template>
  <section class="stat-grid" aria-label="管理统计">
    <article v-for="card in cards" :key="card.label" class="stat-card">
      <span class="stat-label">{{ card.label }}</span>
      <strong class="stat-value">
        {{ card.value }}
        <small v-if="card.suffix">{{ card.suffix }}</small>
      </strong>
    </article>
  </section>
</template>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.stat-card {
  min-width: 0;
  padding: 20px;
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.035);
  box-shadow: inset 0 1px rgba(255, 255, 255, 0.035);
}

.stat-label {
  display: block;
  margin-bottom: 14px;
  color: var(--text-secondary);
  font-size: 11px;
  letter-spacing: 0.1em;
}

.stat-value {
  color: var(--text-primary);
  font-size: clamp(22px, 2.2vw, 30px);
  font-weight: 300;
  letter-spacing: 0.03em;
}

.stat-value small {
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 400;
}

@media (max-width: 760px) {
  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
