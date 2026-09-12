<template>
  <div class="mx-auto max-w-7xl px-4 pb-16 md:px-6" v-if="item">
    <div class="pt-6 md:pt-10">
      <!-- 面包屑 -->
      <nav class="mb-4 flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
        <RouterLink to="/" class="transition hover:text-cyan-300">首页</RouterLink>
        <span>/</span>
        <RouterLink :to="`/category/${item.category_key}`" class="transition hover:text-cyan-300">
          {{ categoryName(item.category_key) }}
        </RouterLink>
        <span>/</span>
        <span class="text-slate-400">详情</span>
      </nav>

      <!-- 统一综合信息卡片 -->
      <section class="glass mb-6 overflow-hidden">
        <div class="flex flex-wrap items-start justify-between gap-3 border-b border-white/5 p-5 md:p-6">
          <div class="min-w-0">
            <span class="badge-cyan mb-2">{{ categoryName(item.category_key) }}</span>
            <h1 class="text-xl font-bold leading-snug text-white md:text-2xl">{{ meta.title }}</h1>
            <div class="mt-2 flex flex-wrap items-center gap-1.5">
              <span
                v-if="meta.lifecycle_state === 'ended'"
                class="inline-flex items-center rounded-md border border-rose-400/30 bg-rose-500/10 px-2 py-0.5 text-xs text-rose-300"
              >
                已停止支持
              </span>
              <span
                v-else-if="meta.lifecycle_state === 'supported'"
                class="inline-flex items-center rounded-md border border-emerald-400/30 bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-300"
              >
                支持中
              </span>
              <span v-if="meta.lifecycle" class="text-xs text-slate-400">{{ meta.lifecycle }}</span>
              <span v-if="meta.support_end" class="text-xs text-slate-400">支持至 {{ meta.support_end }}</span>
            </div>
            <p class="mt-1 text-xs text-slate-500">数据以 SHA256 为主键聚合，源自 {{ (item.sources_raw || []).length }} 个数据源</p>
          </div>
          <div class="flex flex-wrap gap-2">
            <RouterLink v-if="meta.sha256" :to="`/tool-hash?h=${meta.sha256}`" class="btn-ghost !text-xs">校验哈希</RouterLink>
          </div>
        </div>

        <!-- 综合字段 -->
        <div class="grid grid-cols-2 gap-px bg-white/5 sm:grid-cols-3">
          <div v-for="f in fields" :key="f.label" class="flex flex-col gap-1 bg-ink-950 p-4">
            <span class="text-xs text-slate-500">{{ f.label }}</span>
            <span
              class="break-all text-sm"
              :class="[
                f.mono ? 'font-mono' : '',
                f.hl ? 'font-semibold text-cyan-200' : 'text-slate-200',
              ]"
              >{{ f.value || '-' }}</span
            >
          </div>
        </div>

        <div class="flex flex-wrap gap-x-5 gap-y-1.5 border-t border-white/5 p-4 text-xs text-slate-400">
          <span v-if="meta.editions">内置版本：{{ Array.isArray(meta.editions) ? meta.editions.join('、') : (typeof meta.editions === 'object' ? JSON.stringify(meta.editions) : meta.editions) }}</span>
          <span v-if="meta.kb">最新补丁：<b class="text-cyan-300">{{ meta.kb }}</b></span>
          <span v-if="meta.support_end">支持截至：{{ meta.support_end }}</span>
          <span v-if="meta.updated_at">更新时间：{{ meta.updated_at }}</span>
        </div>
      </section>

      <!-- 独立三站原始数据卡片 -->
      <div class="mb-3 flex items-center justify-between gap-2">
        <h2 class="flex items-center gap-2 text-base font-semibold text-slate-100">
          <span class="h-4 w-1 rounded bg-cyan-400"></span>
          三站原始数据对照
        </h2>
        <span class="text-xs text-slate-500">各站独立保存 · 一站一条快照</span>
      </div>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        <SourceCard v-for="s in item.sources_raw" :key="s.source" :src="s" />
      </div>

      <div v-if="!item.sources_raw || !item.sources_raw.length" class="glass mt-4 flex flex-col items-center gap-3 py-14 text-center">
        <p class="text-sm text-slate-400">暂未采集到原始数据</p>
      </div>
    </div>
  </div>

  <!-- 未找到 -->
  <div v-else class="glass mx-auto mt-10 max-w-7xl px-4 py-24 text-center">
    <p class="text-sm text-slate-400">未找到该镜像</p>
    <p class="mt-1 text-xs text-slate-600">({{ route.params.isoKey }})</p>
    <RouterLink to="/" class="btn-ghost mt-4 inline-flex">返回首页</RouterLink>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { store, findItem, categoryName } from '../store'
import { setPageMeta } from '../utils/format'
import { SITE_CONFIG } from '../config'
import SourceCard from '../components/SourceCard.vue'

const route = useRoute()
const item = computed(() => findItem(route.params.isoKey))
const meta = computed(() => item.value?.meta_unified || {})

// 深链直载 / 数据就绪后写真实标题（避免被 afterEach 的通用标题覆盖）
watch(
  [() => store.loaded, () => route.params.isoKey],
  () => {
    const it = findItem(route.params.isoKey)
    const base = SITE_CONFIG.name
    if (it) {
      const m = it.meta_unified || {}
      setPageMeta(
        `${m.title || 'Windows 镜像'} 下载 - ${base}`,
        m.desc || `${m.title} 官方原版镜像信息与多源下载链接，${base}。`
      )
    } else {
      setPageMeta(`镜像详情 - ${base}`, `Windows 原版镜像详情，${base}。`)
    }
  },
  { immediate: true }
)

const fields = computed(() => {
  const m = meta.value
  return [
    { label: '系统版本', value: m.version, mono: false, hl: true },
    { label: '内部 Build', value: m.build, mono: true, hl: true },
    { label: '架构', value: m.arch, mono: false },
    { label: '零售 / 批量', value: m.type === 'consumer' ? '消费者版（零售）' : m.type === 'business' ? '商业版（批量）' : '', mono: false },
    { label: '文件大小', value: m.size, mono: false },
    { label: 'SHA-256', value: m.sha256, mono: true, hl: true },
    { label: '生命周期', value: m.lifecycle, mono: false },
    { label: '发布日期', value: m.date, mono: false },
  ]
})
</script>
