<!-- 胶囊记录表：展示管理员可见的情绪记录。 -->
<!-- 输入 records/loading，输出只读的 Element Plus 表格。 -->
<script setup>
import {
  ElTable,
  ElTableColumn,
} from 'element-plus/es/components/table/index'
import ElTag from 'element-plus/es/components/tag/index'
import 'element-plus/es/components/table/style/css'
import 'element-plus/es/components/tag/style/css'
import {
  dominantEmotion,
  formatShanghaiShort,
} from '../../utils/stats'

defineProps({
  records: {
    type: Array,
    required: true,
  },
  loading: Boolean,
})

const QUADRANTS = {
  melancholic: { label: '低落', className: 'quadrant-melancholic' },
  anxious: { label: '紧绷', className: 'quadrant-anxious' },
  joyful: { label: '明亮', className: 'quadrant-joyful' },
  calm: { label: '平静', className: 'quadrant-calm' },
}

function truncateInput(value) {
  const text = String(value || '')
  return text.length > 24 ? `${text.slice(0, 24)}…` : text
}

function quadrantLabel(quadrant) {
  return QUADRANTS[quadrant]?.label || '未知'
}

function quadrantClass(quadrant) {
  return QUADRANTS[quadrant]?.className || ''
}
</script>

<template>
  <div class="records-table" :class="{ 'is-loading': loading }">
    <ElTable
      :data="records"
      :row-key="(row) => row.id"
      table-layout="fixed"
      aria-label="情绪胶囊记录"
    >
      <ElTableColumn label="时间" width="128">
        <template #default="{ row }">
          {{ formatShanghaiShort(row.createdAt) }}
        </template>
      </ElTableColumn>

      <ElTableColumn prop="userNickname" label="用户" width="130">
        <template #default="{ row }">
          <span class="user-name" :title="row.userNickname">
            {{ row.userNickname }}
          </span>
        </template>
      </ElTableColumn>

      <ElTableColumn label="输入" min-width="300">
        <template #default="{ row }">
          <span class="input-summary" :title="row.input">
            {{ truncateInput(row.input) }}
          </span>
        </template>
      </ElTableColumn>

      <ElTableColumn label="主导情绪" width="108">
        <template #default="{ row }">
          {{ dominantEmotion(row.emotions) }}
        </template>
      </ElTableColumn>

      <ElTableColumn label="效价" width="86">
        <template #default="{ row }">
          <span
            class="valence"
            :class="row.valence < 0 ? 'is-negative' : 'is-positive'"
          >
            {{ Number(row.valence).toFixed(2) }}
          </span>
        </template>
      </ElTableColumn>

      <ElTableColumn label="象限" width="92">
        <template #default="{ row }">
          <ElTag
            size="small"
            effect="plain"
            class="quadrant-tag"
            :class="quadrantClass(row.quadrant)"
          >
            {{ quadrantLabel(row.quadrant) }}
          </ElTag>
        </template>
      </ElTableColumn>
    </ElTable>

    <div v-if="loading" class="table-loading" aria-label="正在加载">
      <span></span>
    </div>
  </div>
</template>

<style scoped>
.records-table {
  position: relative;
  width: 100%;
  overflow: hidden;
}

.records-table :deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(255, 255, 255, 0.045);
  --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.045);
  --el-table-border-color: rgba(255, 255, 255, 0.07);
  --el-table-text-color: rgba(255, 255, 255, 0.72);
  --el-table-header-text-color: rgba(255, 255, 255, 0.45);
  width: 100%;
  background: transparent;
  font-size: 12px;
}

.records-table :deep(.el-table__inner-wrapper::before) {
  background: rgba(255, 255, 255, 0.06);
}

.records-table :deep(.el-table th.el-table__cell) {
  font-weight: 400;
  letter-spacing: 0.06em;
}

.records-table :deep(.el-table td.el-table__cell),
.records-table :deep(.el-table th.el-table__cell) {
  padding: 12px 0;
}

.user-name,
.input-summary {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.input-summary {
  color: rgba(255, 255, 255, 0.82);
}

.valence {
  font-variant-numeric: tabular-nums;
}

.valence.is-positive {
  color: #ffc078;
}

.valence.is-negative {
  color: #8bb8ff;
}

.quadrant-tag {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.035);
}

.quadrant-melancholic {
  border-color: rgba(173, 139, 255, 0.38);
  color: #bca6ff;
}

.quadrant-anxious {
  border-color: rgba(91, 223, 211, 0.36);
  color: #77ded5;
}

.quadrant-joyful {
  border-color: rgba(255, 176, 112, 0.38);
  color: #ffc078;
}

.quadrant-calm {
  border-color: rgba(123, 182, 255, 0.38);
  color: #9dc8ff;
}

.table-loading {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgba(11, 10, 20, 0.45);
  backdrop-filter: blur(2px);
}

.table-loading span {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.15);
  border-top-color: var(--text-primary);
  border-radius: 50%;
  animation: table-spin 700ms linear infinite;
}

@keyframes table-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1023px) {
  .records-table :deep(.el-scrollbar__wrap) {
    overflow-x: auto;
  }
}
</style>
