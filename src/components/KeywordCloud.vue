<!-- 标签云：按 fineLabels 顺序渲染尺寸递减、逐个淡入的情绪标签。 -->
<!-- 输入 5-8 个标签，输出整齐的玻璃标签组。 -->
<script setup>
defineProps({
  labels: {
    type: Array,
    required: true,
  },
})

function tagStyle(index) {
  return {
    fontSize: `${Math.max(13, 18 - index * 1.2)}px`,
    '--rotate': `${((index % 3) - 1) * 1.2}deg`,
    animationDelay: `${index * 60}ms`,
  }
}
</script>

<template>
  <div class="tag-cloud">
    <span
      v-for="(label, index) in labels"
      :key="label"
      class="tag"
      :style="tagStyle(index)"
    >
      {{ label }}
    </span>
  </div>
</template>

<style scoped>
.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-content: flex-start;
}

.tag {
  padding: 6px 14px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.88);
  transform: rotate(var(--rotate));
  opacity: 0;
  animation: tag-in 400ms var(--ease-soft) forwards;
  cursor: default;
  transition:
    transform var(--dur-fast) var(--ease-soft),
    background var(--dur-fast) var(--ease-soft);
}

.tag:hover {
  background: rgba(255, 255, 255, 0.12);
  transform: rotate(var(--rotate)) translateY(-2px) scale(1.04);
}

@keyframes tag-in {
  from {
    opacity: 0;
    translate: 0 5px;
  }

  to {
    opacity: 1;
    translate: 0 0;
  }
}
</style>
