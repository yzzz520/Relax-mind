<!-- 八维雷达图：按固定情绪维度展示 0-100 强度与主题色。 -->
<!-- 输入 emotions、palette，输出可响应容器尺寸变化的 ECharts SVG。 -->
<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RadarChart } from 'echarts/charts'
import { init, use } from 'echarts/core'
import { SVGRenderer } from 'echarts/renderers'
import { EMOTION_DIMENSIONS } from '../api/mock'

use([RadarChart, SVGRenderer])

const props = defineProps({
  emotions: {
    type: Object,
    required: true,
  },
  palette: {
    type: Array,
    default: () => ['#7C5CFF', '#FF8FB1'],
  },
})

const chartElement = ref(null)
let chart
let resizeObserver

function hexToRgba(hex, alpha) {
  const value = hex.replace('#', '')
  const normalized =
    value.length === 3
      ? value
          .split('')
          .map((char) => char + char)
          .join('')
      : value
  const number = Number.parseInt(normalized, 16)
  return `rgba(${(number >> 16) & 255}, ${(number >> 8) & 255}, ${number & 255}, ${alpha})`
}

function buildOption() {
  const accent = props.palette[0] ?? '#7C5CFF'

  return {
    radar: {
      // indicator 顺序决定视觉方位：当前使正面情绪在左半、负面在右半，
      // 便于一眼判断情绪倾向。改动顺序前请评估视觉效果。
      indicator: EMOTION_DIMENSIONS.map((name) => ({ name, max: 100 })),
      center: ['50%', '54%'],
      radius: '72%',
      splitNumber: 5,
      axisName: {
        color: 'rgba(255,255,255,0.6)',
        fontSize: 12,
        padding: [3, 5],
      },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.12)' } },
      splitArea: {
        areaStyle: {
          color: [
            'rgba(255,255,255,0.03)',
            'rgba(255,255,255,0.06)',
          ],
        },
      },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.10)' } },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: EMOTION_DIMENSIONS.map(
              (dimension) => props.emotions[dimension] ?? 0,
            ),
            symbol: 'circle',
            symbolSize: 5,
            lineStyle: { width: 2, color: accent },
            itemStyle: { color: accent },
            areaStyle: {
              color: {
                type: 'radial',
                x: 0.5,
                y: 0.5,
                r: 0.75,
                colorStops: [
                  { offset: 0, color: hexToRgba(accent, 0.1) },
                  { offset: 1, color: hexToRgba(accent, 0.45) },
                ],
              },
            },
          },
        ],
      },
    ],
    animationDuration: 900,
    animationEasing: 'cubicOut',
  }
}

function renderChart() {
  chart?.setOption(buildOption(), true)
}

watch(
  [() => props.emotions, () => props.palette],
  renderChart,
  { deep: true },
)

onMounted(async () => {
  await nextTick()
  chart = init(chartElement.value, null, { renderer: 'svg' })
  renderChart()
  resizeObserver = new ResizeObserver(() => chart?.resize())
  resizeObserver.observe(chartElement.value)
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chart?.dispose()
  chart = null
})

defineExpose({
  getOption: () => chart?.getOption(),
})
</script>

<template>
  <div
    ref="chartElement"
    class="radar-chart"
    role="img"
    aria-label="八维情绪雷达图"
  ></div>
</template>

<style scoped>
.radar-chart {
  width: 100%;
  height: var(--radar-height);
  padding: 8px 0;
}

@media (max-width: 1023px) {
  .radar-chart {
    height: 260px;
  }
}
</style>
