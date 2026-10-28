<!-- 最近七天生成量：使用 ECharts 折线图展示。 -->
<!-- 输入 daily，输出响应容器尺寸的只读图表。 -->
<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { init, use } from 'echarts/core'
import { SVGRenderer } from 'echarts/renderers'

use([LineChart, GridComponent, TooltipComponent, SVGRenderer])

const props = defineProps({
  daily: {
    type: Array,
    required: true,
  },
})

const chartElement = ref(null)
let chart
let resizeObserver

function buildOption() {
  return {
    animationDuration: 500,
    grid: { left: 38, right: 18, top: 24, bottom: 30 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: props.daily.map((item) => item.date),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      axisLabel: { color: 'rgba(255,255,255,0.42)', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: 'rgba(255,255,255,0.36)', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
    },
    series: [
      {
        type: 'line',
        data: props.daily.map((item) => item.count),
        smooth: true,
        symbolSize: 6,
        lineStyle: { width: 2, color: '#ff8fb1' },
        itemStyle: { color: '#ff8fb1' },
        areaStyle: { color: 'rgba(255,143,177,0.12)' },
      },
    ],
  }
}

function render() {
  chart?.setOption(buildOption(), true)
}

watch(() => props.daily, render, { deep: true })

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
    class="daily-line"
    role="img"
    aria-label="最近七天情绪胶囊生成量"
  ></div>
</template>

<style scoped>
.daily-line {
  width: 100%;
  height: 320px;
}
</style>
