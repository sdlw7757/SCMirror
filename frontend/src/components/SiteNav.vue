<template>
  <header class="sticky top-0 z-40 border-b border-white/10 bg-ink-950/80 backdrop-blur-lg">
    <div class="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 md:px-6">
      <!-- Logo：全站统一站名“海云镜像” -->
      <RouterLink to="/" class="group flex items-center gap-2.5" @click="menuOpen = false">
        <span
          class="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-sky-600 shadow-lg shadow-cyan-500/25 transition group-hover:shadow-cyan-400/40"
        >
          <svg viewBox="0 0 24 24" class="h-5 w-5 text-white" fill="currentColor">
            <path
              d="M6 13c0-2.4 1.7-3.8 3.6-3.9C10.4 6.6 12.5 5 15 5c2 0 3.7 1.2 4.4 3 1.7.2 2.6 1.5 2.6 3.2 0 1.8-1.4 3.3-3.4 3.3H7.3A2.7 2.7 0 0 1 6 13Z"
              opacity="0.95"
            />
            <rect x="10" y="15.5" width="5" height="1.6" rx="0.8" opacity="0.85" />
          </svg>
        </span>
        <span class="flex flex-col leading-none">
          <span class="text-lg font-bold tracking-wide text-white glow-text">{{ site.name }}</span>
          <span class="text-[10px] uppercase tracking-[0.28em] text-slate-500">{{ site.name_en }}</span>
        </span>
      </RouterLink>

      <!-- 桌面端分类导航 -->
      <nav class="hidden items-center gap-1 lg:flex">
        <RouterLink
          v-for="c in store.data?.categories || []"
          :key="c.key"
          :to="`/category/${c.key}`"
          class="rounded-lg px-3 py-1.5 text-sm text-slate-300 transition hover:bg-white/5 hover:text-cyan-300"
          active-class="bg-cyan-500/10 text-cyan-300"
        >
          {{ c.short || c.name }}
        </RouterLink>
        <RouterLink
          to="/tool-hash"
          class="rounded-lg px-3 py-1.5 text-sm text-slate-300 transition hover:bg-white/5 hover:text-cyan-300"
          active-class="bg-cyan-500/10 text-cyan-300"
        >
          哈希工具
        </RouterLink>
        <RouterLink
          to="/wiki"
          class="rounded-lg px-3 py-1.5 text-sm text-slate-300 transition hover:bg-white/5 hover:text-cyan-300"
          active-class="bg-cyan-500/10 text-cyan-300"
        >
          知识库
        </RouterLink>
      </nav>

      <div class="flex items-center gap-2">
        <!-- GitHub 仓库链接已收敛到页脚唯一位，避免“仓库地址”重复 -->
        <!-- 移动端汉堡 -->
        <button
          class="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-slate-300 lg:hidden"
          aria-label="菜单"
          @click="menuOpen = !menuOpen"
        >
          <svg v-if="!menuOpen" viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M4 7h16M4 12h16M4 17h16" />
          </svg>
          <svg v-else viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
        </button>
      </div>
    </div>

    <!-- 移动端折叠菜单 -->
    <Transition name="fade-slide">
      <nav v-if="menuOpen" class="border-t border-white/10 bg-ink-900/95 px-4 pb-4 pt-2 backdrop-blur-xl lg:hidden">
        <div class="grid grid-cols-2 gap-2">
          <RouterLink
            v-for="c in store.data?.categories || []"
            :key="c.key"
            :to="`/category/${c.key}`"
            class="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 transition hover:border-cyan-400/40"
            @click="menuOpen = false"
          >
            {{ c.name }}
          </RouterLink>
          <RouterLink to="/tool-hash" class="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200" @click="menuOpen = false">
            哈希工具
          </RouterLink>
          <RouterLink to="/wiki" class="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200" @click="menuOpen = false">
            知识库
          </RouterLink>
        </div>
      </nav>
    </Transition>
  </header>
</template>

<script setup>
import { ref, computed } from 'vue'
import { store } from '../store'

const menuOpen = ref(false)
const site = computed(() => store.data?.site || { name: '海云镜像', name_en: 'SeaCloud Mirror', github: '' })
</script>
