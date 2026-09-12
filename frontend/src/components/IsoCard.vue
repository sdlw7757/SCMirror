<template>
  <RouterLink
    :to="`/detail/${item.iso_key}`"
    class="glass glass-hover group block p-4 focus:outline-none"
  >
    <!-- 顶部：分类 + 架构 + 生命周期 -->
    <div class="mb-2 flex flex-wrap items-center gap-1.5">
      <span class="badge-cyan">{{ catName }}</span>
      <span v-if="m.arch" class="chip">{{ archLabel(m.arch) }}</span>
      <span v-if="m.type" class="chip">{{ typeShort(m.type) }}</span>
      <span
        v-if="m.lifecycle_state === 'ended'"
        class="inline-flex items-center rounded-md border border-rose-400/30 bg-rose-500/10 px-2 py-0.5 text-xs text-rose-300"
      >
        已停止支持
      </span>
      <span
        v-else-if="m.lifecycle_state === 'supported'"
        class="inline-flex items-center rounded-md border border-emerald-400/30 bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-300"
      >
        支持中
      </span>
    </div>

    <!-- 标题 -->
    <h3 class="text-sm font-semibold leading-snug text-white transition group-hover:text-cyan-200 md:text-base">
      {{ m.title }}
    </h3>

    <!-- 数据来源站点（三站用不同颜色区分） -->
    <div v-if="sourceTags.length" class="mt-1.5 flex flex-wrap items-center gap-1 text-[10px]">
      <span class="text-slate-500/70">来源</span>
      <span
        v-for="(t, i) in sourceTags"
        :key="i"
        class="rounded border px-1.5 py-0.5"
        :class="tagColor(t.key)"
      >{{ t.name }}</span>
    </div>

    <!-- 元信息（重点项提亮） -->
    <div class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-xs">
      <span v-if="m.version" class="font-medium text-cyan-200">版本 {{ m.version }}</span>
      <span v-if="m.build" class="inline-flex items-center rounded-md border border-cyan-400/30 bg-cyan-500/10 px-2 py-0.5 font-mono text-cyan-300">
        Build {{ m.build }}
      </span>
      <span v-if="m.size" class="text-slate-300">{{ m.size }}</span>
      <span v-if="m.kb" class="badge-cyan">
        <span class="opacity-70">KB</span>&nbsp;{{ m.kb }}
      </span>
    </div>

    <!-- 底部分隔 + SHA256 片段 + 数据源 -->
    <div class="mt-3 flex items-center justify-between gap-2 border-t border-white/5 pt-3">
      <span class="min-w-0 flex-1">
        <span class="text-[10px] text-slate-500">SHA256&nbsp;</span>
        <code class="truncate font-mono text-[11px] text-cyan-300/90">
          {{ m.sha256 ? hashText(m.sha256) : (hashesFallback) }}
        </code>
      </span>
      <span class="shrink-0 rounded-md border border-white/10 bg-white/5 px-1.5 py-0.5 text-[11px] text-slate-400">
        {{ (item.sources_raw || []).length }} 源
      </span>
    </div>
  </RouterLink>
</template>

<script setup>
import { computed } from 'vue'
import { categoryName } from '../store'
import { archLabel, typeShort, hashText, sourceColor } from '../utils/format'

const props = defineProps({ item: { type: Object, required: true } })

const m = computed(() => props.item.meta_unified || {})
const catName = computed(() => categoryName(props.item.category_key))
const sourceTags = computed(() =>
  (props.item.sources_raw || [])
    .map((s) => ({ key: s.source, name: s.source_name || s.source || '' }))
    .filter((t) => t.name)
)
// 三站配色统一取自 format.sourceColor（山己几子木=青 / 系统库=绿 / HelloWindows=紫）
function tagColor(key) {
  return sourceColor(key).badge
}
const hashesFallback = computed(() => {
  const src = (props.item.sources_raw || [])[0]
  const h = src?.hash || {}
  return h.sha256 || h.sha1 || ''
})
</script>
