<template>
  <div class="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
    <!-- 总收录 -->
    <div class="glass glass-hover p-4">
      <div class="mb-1 flex items-center gap-1.5 text-xs text-slate-400">
        <svg viewBox="0 0 24 24" class="h-4 w-4 text-cyan-400" fill="currentColor">
          <path d="M2 6l9-4 9 4-9 4-9-4Zm0 6 9 4 9-4M2 18l9 4 9-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
          <rect x="11" y="7" width="2" height="14" fill="currentColor" opacity="0.6"/>
        </svg>
        总收录镜像
      </div>
      <p class="stat-value">{{ fmt(stats.total) }}</p>
      <p class="mt-0.5 text-[11px] text-slate-500">SHA256 去重后的独立镜像</p>
    </div>

    <!-- 今日新增（可点击查看列表） -->
    <button
      type="button"
      class="glass glass-hover group p-4 text-left transition hover:border-cyan-400/40"
      title="点击查看今日新增的镜像"
      @click="$emit('today')"
    >
      <div class="mb-1 flex items-center gap-1.5 text-xs text-slate-400 group-hover:text-cyan-300">
        <svg viewBox="0 0 24 24" class="h-4 w-4 text-cyan-400" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 5v14M5 12h14"/>
        </svg>
        今日新增
        <span class="ml-auto text-[10px] opacity-60 transition group-hover:opacity-100">查看 →</span>
      </div>
      <p class="stat-value">{{ fmt(stats.today_new) }}</p>
      <p class="mt-0.5 text-[11px] text-slate-500">首次收录的新镜像</p>
    </button>

    <!-- 今日更新 -->
    <div class="glass glass-hover p-4">
      <div class="mb-1 flex items-center gap-1.5 text-xs text-slate-400">
        <svg viewBox="0 0 24 24" class="h-4 w-4 text-cyan-400" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 12a9 9 0 1 1-2.6-6.4M21 3v6h-6"/>
        </svg>
        今日更新
      </div>
      <p class="stat-value">{{ fmt(stats.today_update) }}</p>
      <p class="mt-0.5 text-[11px] text-slate-500">已收录镜像的内容更新</p>
    </div>

    <!-- 最后同步 -->
    <div class="glass glass-hover p-4 col-span-2 md:col-span-1">
      <div class="mb-1 flex items-center gap-1.5 text-xs text-slate-400">
        <svg viewBox="0 0 24 24" class="h-4 w-4 text-cyan-400" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
          <circle cx="12" cy="12" r="9"/>
          <path d="M12 7v5l3 2"/>
        </svg>
        最后同步
      </div>
      <p class="font-mono text-sm font-semibold text-cyan-200 md:text-base">{{ lastSync }}</p>
      <p class="mt-0.5 text-[11px] text-slate-500">爬虫最近一次抓取完成时间</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { store } from '../store'
import { fmtCount } from '../utils/format'

const stats = computed(() => store.data?.stats || {})
const lastSync = computed(() => (store.data?.stats?.last_sync || '').slice(0, 16))
const fmt = fmtCount
</script>
