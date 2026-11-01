<template>
  <div class="screen">
    <Dashboard
      :summary="summary"
      :weekly-focus="weeklyFocus"
      :hourly-distract="hourlyDistract"
    />
  </div>
</template>

<script setup>
import Dashboard from './components/Dashboard.vue'

const summary = {
  focusDuration: 312,
  focusCount: 8,
  distractCount: 14,
  avgDuration: 39
}

const weeklyFocus = [
  { date: '10-25', duration: 180 },
  { date: '10-26', duration: 240 },
  { date: '10-27', duration: 90 },
  { date: '10-28', duration: 300 },
  { date: '10-29', duration: 260 },
  { date: '10-30', duration: 320 },
  { date: '10-31', duration: 312 }
]

const hourlyDistract = [0, 0, 0, 0, 0, 0, 1, 2, 3, 1, 0, 2, 4, 1, 0, 1, 3, 5, 2, 1, 2, 1, 0, 0]
</script>

<style>
.screen {
  min-height: 100vh;
  background: radial-gradient(ellipse at top, #0a2a4a, #061226 60%, #03060f);
  color: #fff;
}
</style>
