<template>
  <div class="mx-auto max-w-7xl px-4 pb-16 md:px-6">
    <div v-if="category" class="pt-8 md:pt-12">
      <!-- 面包屑 / 标题 -->
      <nav class="mb-3 flex items-center gap-1.5 text-xs text-slate-500">
        <RouterLink to="/" class="transition hover:text-cyan-300">首页</RouterLink>
        <span>/</span>
        <span class="text-slate-400">{{ category.name }}</span>
      </nav>

      <div class="mb-6">
        <h1 class="text-2xl font-extrabold tracking-tight md:text-4xl">
          <span class="glow-text">{{ category.name }}</span>
          <span class="ml-2 align-middle text-sm font-normal text-slate-500">
            {{ count }} 个镜像
          </span>
        </h1>
        <!-- ① 当前系统简短介绍 -->
        <p class="mt-3 max-w-3xl text-sm leading-relaxed text-slate-400">{{ category.intro }}</p>
        <div class="mt-3 flex flex-wrap gap-1.5">
          <span v-for="k in (category.keywords || '').split(',').filter(Boolean)" :key="k" class="chip">{{ k.trim() }}</span>
        </div>
      </div>

      <!-- ② 该分类下全部镜像（仅展示 meta_unified） -->
      <div class="mb-4 flex items-center justify-between gap-2">
        <SearchBox v-model="query" class="max-w-md flex-1" />
        <span class="shrink-0 text-xs text-slate-500">{{ listed.length }} / {{ count }}</span>
      </div>

      <div v-if="listed.length" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <IsoCard v-for="it in listed" :key="it.iso_key" :item="it" />
      </div>
      <div v-else class="glass flex flex-col items-center gap-3 py-16 text-center">
        <p class="text-sm text-slate-400">该分类下暂无匹配镜像</p>
      </div>
    </div>

    <div v-else class="glass flex flex-col items-center justify-center gap-3 py-24 text-center">
      <p class="text-sm text-slate-400">分类不存在</p>
      <RouterLink to="/" class="btn-ghost">返回首页</RouterLink>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { store, findCategory, categoryName } from '../store'
import { fuzzyFilter } from '../utils/search'
import { setPageMeta } from '../utils/format'
import { SITE_CONFIG } from '../config'
import IsoCard from '../components/IsoCard.vue'
import SearchBox from '../components/SearchBox.vue'

const route = useRoute()
const query = ref('')

const category = computed(() => findCategory(route.params.categoryKey))
const all = computed(() => (store.data?.items || []).filter((it) => it.category_key === (category.value?.key || route.params.categoryKey)))
const count = computed(() => all.value.length)
const listed = computed(() => fuzzyFilter(all.value, query.value, categoryName))

// 深链直载 / 数据就绪后写真实标题（避免被 afterEach 的通用标题覆盖）
watch(
  [() => store.loaded, () => route.params.categoryKey],
  () => {
    const cat = findCategory(route.params.categoryKey)
    const base = SITE_CONFIG.name
    if (cat) {
      setPageMeta(
        `${cat.name} 原版镜像下载 - ${base}`,
        cat.intro || `${cat.name} 官方原版镜像聚合列表，${base} 聚合山己几子木/系统库/HelloWindows 多源数据。`
      )
    } else {
      setPageMeta(`系统分类 - ${base}`, `按系统分类浏览 Windows 原版镜像，${base}。`)
    }
  },
  { immediate: true }
)
</script>
