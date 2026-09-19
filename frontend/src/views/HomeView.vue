<template>
  <div class="mx-auto max-w-7xl px-4 pb-16 md:px-6">
    <!-- Hero -->
    <section class="relative py-10 md:py-16">
      <div class="bg-grid pointer-events-none absolute inset-0"></div>
      <div class="relative">
        <span class="mb-3 inline-flex items-center gap-1.5 rounded-full border border-cyan-400/30 bg-cyan-500/10 px-3 py-1 text-xs text-cyan-300">
          <span class="h-1.5 w-1.5 animate-pulse rounded-full bg-cyan-400"></span>
          SPA 静态聚合 · 每日自动同步三站
        </span>
        <h1 class="text-3xl font-extrabold tracking-tight md:text-5xl">
          <span class="glow-text">{{ site.name }}</span>
          <span class="mt-2 block text-xl font-semibold text-slate-300 md:text-2xl">
            微软原版系统镜像站
          </span>
        </h1>
        <p class="mt-4 max-w-2xl text-sm leading-relaxed text-slate-400 md:text-base">
          以 <span class="font-mono text-cyan-300">SHA256</span> 为主键聚合三站镜像元数据，保留原始信息，
          支持检索筛选与校验，纯净无捆绑，提供 Windows / Office 原版镜像及 SHA 校验码。
        </p>
      </div>
    </section>

    <!-- 数据抓取 / 服务运行状态 -->
    <DataStatus class="mb-4" />

    <!-- 统计双看板 -->
    <StatBoard class="mb-6" @today="onToday" />

    <!-- 搜索 -->
    <div class="mb-4">
      <SearchBox v-model="query" />
    </div>

    <!-- 高级筛选 -->
    <div class="mb-6">
      <FilterBar v-model="filters" />
    </div>

    <!-- 结果统计 -->
    <div id="mirror-list" class="mb-3 flex flex-wrap items-center justify-between gap-2 scroll-mt-20">
      <h2 class="flex items-center gap-2 text-base font-semibold text-slate-100">
        <span class="h-4 w-1 rounded bg-cyan-400"></span>
        镜像列表
      </h2>
      <div class="flex items-center gap-2">
        <button
          v-if="todayOnly"
          type="button"
          class="inline-flex items-center gap-1 rounded-md border border-cyan-400/40 bg-cyan-500/10 px-2 py-0.5 text-xs text-cyan-300 transition hover:bg-cyan-500/20"
          title="清除“今日新增”筛选"
          @click="todayOnly = false"
        >
          今日新增 ✕
        </button>
        <span class="text-xs text-slate-500">共 {{ listed.length }} 条</span>
      </div>
    </div>

    <!-- 列表（默认精简展示，可“加载更多”） -->
    <div v-if="listed.length" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <IsoCard v-for="it in shown" :key="it.iso_key" :item="it" />
    </div>

    <!-- 加载更多 -->
    <div v-if="listed.length && shown.length < listed.length" class="mt-6 flex items-center justify-center gap-4">
      <button class="btn-ghost" @click="loadMore">
        加载更多
        <span class="text-xs text-slate-500">（当前 {{ shown.length }} / {{ listed.length }}，每次再载 24 条）</span>
      </button>
    </div>

    <!-- 空状态 -->
    <div v-else class="glass flex flex-col items-center justify-center gap-3 py-16 text-center">
      <svg viewBox="0 0 24 24" class="h-10 w-10 text-slate-600" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
        <circle cx="11" cy="11" r="7" />
        <path d="m21 21-4.3-4.3" />
      </svg>
      <p class="text-sm text-slate-400">未找到匹配的镜像，试试调整搜索词或重置筛选条件</p>
      <button class="btn-ghost !text-xs" @click="resetAll">重置筛选</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { store, categoryName } from '../store'
import { fuzzyFilter, applyFilters } from '../utils/search'
import StatBoard from '../components/StatBoard.vue'
import DataStatus from '../components/DataStatus.vue'
import SearchBox from '../components/SearchBox.vue'
import FilterBar from '../components/FilterBar.vue'
import IsoCard from '../components/IsoCard.vue'

// 今日新增视图：由 StatBoard“今日新增”卡片点击触发，过滤 first_seen=今天 的镜像
const todayOnly = ref(false)
const today = computed(() => (store.data?.stats?.last_sync || '').slice(0, 10))
function onToday() {
  todayOnly.value = true
  // 滚动到镜像列表
  requestAnimationFrame(() => {
    document.getElementById('mirror-list')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

const site = computed(() => store.data?.site || { name: '海云镜像' })
const query = ref('')
const filters = ref({ category: 'all', arch: 'all', type: 'all', lifecycle: 'all' })

function resetAll() {
  query.value = ''
  filters.value = { category: 'all', arch: 'all', type: 'all', lifecycle: 'all' }
  visible.value = PAGE_INIT
}

// —— 首页精简展示：默认只显示少量，点击“加载更多”逐步追加 ——
const PAGE_INIT = 12
const PAGE_STEP = 24
const visible = ref(PAGE_INIT)
const listed = computed(() => {
  let all = store.data?.items || []
  if (todayOnly.value) {
    all = all.filter((it) => it.first_seen === today.value)
  }
  const filtered = applyFilters(all, filters.value)
  return fuzzyFilter(filtered, query.value, categoryName)
})
const shown = computed(() => listed.value.slice(0, visible.value))
function loadMore() {
  visible.value += PAGE_STEP
}
</script>
