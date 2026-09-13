<template>
  <div class="glass flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-2.5 text-xs">
    <span
      class="inline-flex items-center gap-1.5 font-medium"
      :class="status.cls"
    >
      <span class="h-2 w-2 rounded-full" :class="status.dot"></span>
      {{ status.text }}
    </span>
    <span v-if="lastSync" class="text-slate-500">
      最近抓取 <b class="font-mono text-cyan-300">{{ lastSync }}</b>
    </span>
    <span class="text-slate-500">
      今日新增 <b class="text-cyan-300">{{ fmt(stats.today_new) }}</b>
    </span>
    <span class="text-slate-500">
      今日更新 <b class="text-cyan-300">{{ fmt(stats.today_update) }}</b>
    </span>
    <span class="ml-auto text-slate-600">GitHub Actions 每日自动抓取三站并同步</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { store } from '../store'
import { fmtCount } from '../utils/format'

const stats = computed(() => store.data?.stats || {})
const lastSync = computed(() => (stats.value.last_sync || '').slice(0, 16))

// last_sync 为北京时间(UTC+8)字符串，转成真实时刻再与当前时间比较新鲜度
function parseBjt(s) {
  const m = String(s || '').match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/)
  if (!m) return null
  return Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4] - 8, +m[5])
}

const status = computed(() => {
  const t = parseBjt(stats.value.last_sync || '')
  if (!t) {
    return { text: '数据同步状态未知', dot: 'bg-slate-400', cls: 'text-slate-300' }
  }
  const ageH = (Date.now() - t) / 36e5
  if (ageH <= 30) {
    return { text: '数据抓取服务运行正常', dot: 'bg-emerald-400 animate-pulse', cls: 'text-emerald-300' }
  }
  if (ageH <= 72) {
    return { text: '数据同步延迟（上次抓取超过 1 天）', dot: 'bg-amber-400', cls: 'text-amber-300' }
  }
  return { text: '数据同步异常（多日未更新）', dot: 'bg-rose-500', cls: 'text-rose-300' }
})

const fmt = fmtCount
</script>