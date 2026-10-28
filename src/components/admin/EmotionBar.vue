<!-- 八维情绪均值：使用 ECharts 横向条形图展示。 -->
<!-- 输入 emotionAvg，输出响应容器尺寸的只读图表。 -->
<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { init, use } from 'echarts/core'
import { SVGRenderer } from 'echarts/renderers'
import { EMOTION_DIMENSIONS } from '../../api/mock'

use([BarChart, GridComponent, TooltipComponent, SVGRenderer])

const props = defineProps({
  emotionAvg: {
    type: Object,
    required: true,
  },
})

const chartElement = ref(null)
let chart
let resizeObserver

function buildOption() {
  const dimensions = [...EMOTION_DIMENSIONS]
  return {
    animationDuration: 500,
    grid: { left: 58, right: 24, top: 18, bottom: 24 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      valueFormatter: (value) => `${Number(value).toFixed(1)}`,
    },
    xAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { color: 'rgba(255,255,255,0.38)', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
    },
    yAxis: {
      type: 'category',
      data: dimensions,
      inverse: true,
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: { color: 'rgba(255,255,255,0.58)', fontSize: 11 },
    },
    series: [
      {
        type: 'bar',
        data: dimensions.map((dimension) => props.emotionAvg[dimension] ?? 0),
        barWidth: 8,
        itemStyle: {
          borderRadius: [0, 4, 4, 0],
          color: '#7c5cff',
        },
      },
    ],
  }
}

function render() {
  chart?.setOption(buildOption(), true)
}

watch(() => props.emotionAvg, render, { deep: true })

onMounted(async () => {
  await nextTick()
  chart = init(chartElement.value, null, { renderer: 'svg' })
  render()
  resizeObserver = new ResizeObserver(() => chart?.resize())
  resizeObserver.observe(chartElement.value)
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div
    ref="chartElement"
    class="emotion-bar"
    role="img"
    aria-label="八维情绪均值条形图"
  ></div>
</template>

<style scoped>
.emotion-bar {
  width: 100%;
  height: 320px;
}
</style>
