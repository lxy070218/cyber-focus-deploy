<template>
  <div class="dashboard">
    <div class="cards">
      <div class="card" v-for="card in cards" :key="card.label">
        <div class="card-main">
          <span class="card-value">{{ card.value }}</span>
          <span class="card-unit">{{ card.unit }}</span>
        </div>
        <div class="card-label">{{ card.label }}</div>
      </div>
    </div>

    <div class="charts">
      <div class="chart-box">
        <div class="chart-title">近7日专注时长</div>
        <div class="chart" ref="lineRef"></div>
        <div v-if="!hasLineData" class="empty">暂无数据</div>
      </div>
      <div class="chart-box">
        <div class="chart-title">24小时分心分布</div>
        <div class="chart" ref="barRef"></div>
        <div v-if="!hasBarData" class="empty">暂无数据</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import echarts from '../utils/echarts'

const props = defineProps({
  summary: {
    type: Object,
    default: () => ({
      focusDuration: 0,
      focusCount: 0,
      distractCount: 0,
      avgDuration: 0
    })
  },
  weeklyFocus: {
    type: Array,
    default: () => []
  },
  hourlyDistract: {
    type: Array,
    default: () => []
  }
})

const lineRef = ref(null)
const barRef = ref(null)
let lineChart = null
let barChart = null

function formatDuration(min) {
  const m = Number(min) || 0
  if (m < 60) return { value: m, unit: '分钟' }
  return { value: (m / 60).toFixed(1), unit: '小时' }
}

const cards = computed(() => {
  const s = props.summary || {}
  const focus = formatDuration(s.focusDuration)
  const avg = formatDuration(s.avgDuration)
  return [
    { label: '今日专注时长', value: focus.value, unit: focus.unit },
    { label: '专注次数', value: s.focusCount || 0, unit: '次' },
    { label: '分心次数', value: s.distractCount || 0, unit: '次' },
    { label: '平均时长', value: avg.value, unit: avg.unit }
  ]
})

const hasLineData = computed(() => {
  const arr = props.weeklyFocus || []
  return arr.length > 0 && arr.some(d => Number(d.duration) > 0)
})

const hasBarData = computed(() => {
  const arr = props.hourlyDistract || []
  return arr.length > 0 && arr.some(v => Number(v) > 0)
})

function buildLineOption() {
  const arr = props.weeklyFocus || []
  const dates = arr.map(d => d.date)
  const durations = arr.map(d => Number(d.duration) || 0)
  return {
    backgroundColor: 'transparent',
    grid: { left: 50, right: 24, top: 24, bottom: 36 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 20, 40, 0.85)',
      borderColor: 'rgba(0, 212, 255, 0.4)',
      textStyle: { color: '#fff' },
      formatter: p => `${p[0].name}<br/>专注 ${p[0].value} 分钟`
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.25)' } },
      axisTick: { show: false },
      axisLabel: { color: 'rgba(255,255,255,0.65)' }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: 'rgba(255,255,255,0.65)' }
    },
    series: [{
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      data: durations,
      lineStyle: {
        width: 3,
        color: {
          type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [
            { offset: 0, color: '#00d4ff' },
            { offset: 0.5, color: '#3a8bff' },
            { offset: 1, color: '#7b61ff' }
          ]
        },
        shadowColor: 'rgba(0, 212, 255, 0.7)',
        shadowBlur: 15
      },
      itemStyle: {
        color: '#00d4ff',
        borderColor: '#fff',
        borderWidth: 1,
        shadowColor: 'rgba(0, 212, 255, 0.9)',
        shadowBlur: 10
      },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(0, 212, 255, 0.45)' },
            { offset: 1, color: 'rgba(0, 212, 255, 0)' }
          ]
        }
      }
    }]
  }
}

function buildBarOption() {
  const arr = props.hourlyDistract || []
  const hours = arr.map((_, i) => i + '时')
  const values = arr.map(v => Number(v) || 0)
  const maxVal = values.length ? Math.max(...values) : 0
  const data = values.map(val => {
    const isMax = maxVal > 0 && val === maxVal
    return {
      value: val,
      itemStyle: isMax
        ? {
            color: '#ff4d4f',
            shadowColor: 'rgba(255, 77, 79, 0.9)',
            shadowBlur: 18
          }
        : {
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: '#00d4ff' },
                { offset: 1, color: '#1e6fff' }
              ]
            },
            shadowColor: 'rgba(0, 140, 255, 0.5)',
            shadowBlur: 8
          }
    }
  })
  return {
    backgroundColor: 'transparent',
    grid: { left: 50, right: 24, top: 24, bottom: 36 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(0, 20, 40, 0.85)',
      borderColor: 'rgba(0, 212, 255, 0.4)',
      textStyle: { color: '#fff' },
      formatter: p => `${p[0].name}<br/>分心 ${p[0].value} 次`
    },
    xAxis: {
      type: 'category',
      data: hours,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.25)' } },
      axisTick: { show: false },
      axisLabel: { color: 'rgba(255,255,255,0.65)', interval: 1 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: 'rgba(255,255,255,0.65)' }
    },
    series: [{
      type: 'bar',
      data,
      barWidth: '55%'
    }]
  }
}

function renderLine() {
  if (!lineChart || !hasLineData.value) return
  lineChart.setOption(buildLineOption(), true)
}

function renderBar() {
  if (!barChart || !hasBarData.value) return
  barChart.setOption(buildBarOption(), true)
}

function handleResize() {
  lineChart && lineChart.resize()
  barChart && barChart.resize()
}

onMounted(() => {
  lineChart = echarts.init(lineRef.value)
  barChart = echarts.init(barRef.value)
  renderLine()
  renderBar()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  lineChart && lineChart.dispose()
  barChart && barChart.dispose()
  lineChart = null
  barChart = null
})

watch(() => props.weeklyFocus, renderLine, { deep: true })
watch(() => props.hourlyDistract, renderBar, { deep: true })
</script>

<style scoped>
.dashboard {
  width: 100%;
  box-sizing: border-box;
  padding: 20px;
  color: #fff;
  background: transparent;
}

.cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.card {
  position: relative;
  padding: 22px 24px;
  border: 1px solid rgba(0, 212, 255, 0.25);
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.08), rgba(123, 97, 255, 0.08));
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.12) inset;
  overflow: hidden;
}

.card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #00d4ff, #7b61ff);
  box-shadow: 0 0 10px #00d4ff;
}

.card-main {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.card-value {
  font-size: 34px;
  font-weight: 700;
  line-height: 1.1;
  color: #00d4ff;
  text-shadow: 0 0 12px rgba(0, 212, 255, 0.6);
}

.card-unit {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.card-label {
  margin-top: 10px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
}

.charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.chart-box {
  position: relative;
  min-height: 380px;
  padding: 12px 14px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  background: transparent;
}

.chart-title {
  margin-bottom: 8px;
  padding-left: 10px;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.9);
  border-left: 3px solid #00d4ff;
}

.chart {
  width: 100%;
  height: 320px;
}

.empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 16px;
  color: rgba(255, 255, 255, 0.4);
}
</style>
