<template>
  <footer class="mt-auto border-t border-white/10 bg-ink-900/60">
    <div class="mx-auto max-w-7xl px-4 py-8 md:px-6">
      <div class="flex flex-col items-center gap-4 text-center md:flex-row md:items-start md:justify-between md:text-left">
        <!-- 站点信息 -->
        <div class="flex max-w-md flex-col items-center gap-2 md:items-start">
          <div class="flex items-center gap-2">
            <span class="text-base font-bold text-white glow-text">{{ site.name }}</span>
            <span class="text-[10px] uppercase tracking-[0.24em] text-slate-500">{{ site.name_en }}</span>
          </div>
          <p class="text-xs leading-relaxed text-slate-500">
            聚合整理<a :href="homeOf('sjjzm')" target="_blank" rel="noopener noreferrer" class="font-medium text-cyan-300 underline-offset-2 transition hover:underline">山己几子木</a>、<a :href="homeOf('xitongku')" target="_blank" rel="noopener noreferrer" class="font-medium text-cyan-300 underline-offset-2 transition hover:underline">系统库</a>、<a :href="homeOf('hello')" target="_blank" rel="noopener noreferrer" class="font-medium text-cyan-300 underline-offset-2 transition hover:underline">HelloWindows</a>三站的 Windows 官方原版镜像元信息，以 SHA256 为主键统一去重与聚合。
          </p>
        </div>

        <!-- ① 项目 GitHub 仓库可点击链接（抽为配置常量，改 src/config.js 即可） -->
        <a
          :href="github"
          target="_blank"
          rel="noopener noreferrer"
          class="group inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300 transition hover:border-cyan-400/40 hover:text-cyan-300"
        >
          <svg viewBox="0 0 16 16" class="h-4 w-4" fill="currentColor">
            <path d="M8 0C3.6 0 0 3.6 0 8c0 3.5 2.3 6.5 5.5 7.6.4.1.5-.2.5-.4v-1.5c-2.2.5-2.7-1-2.7-1-.4-.9-.9-1.2-.9-1.2-.7-.5.1-.5.1-.5.8.1 1.3.9 1.3.9.7 1.2 1.9.9 2.3.7.1-.5.3-.9.5-1.1-1.8-.2-3.6-.9-3.6-4 0-.9.3-1.6.8-2.2-.1-.2-.4-1 .1-2.1 0 0 .7-.2 2.2.8a7.7 7.7 0 0 1 4 0c1.5-1 2.2-.8 2.2-.8.5 1.1.2 1.9.1 2.1.5.6.8 1.3.8 2.2 0 3.1-1.9 3.8-3.6 4 .3.3.6.8.6 1.6v2.2c0 .2.1.5.5.4A8 8 0 0 0 16 8c0-4.4-3.6-8-8-8Z" />
          </svg>
          GitHub 项目仓库
        </a>
      </div>

      <!-- ② 简短免责声明（弱化字体，仅页脚展示） + 网站地图入口 -->
      <div class="mt-6 border-t border-white/5 pt-5">
        <p class="mb-2 text-center">
          <a
            href="/sitemap.xml"
            target="_blank"
            rel="nofollow"
            class="text-[11px] text-slate-500 underline-offset-2 transition hover:text-cyan-300 hover:underline"
          >
            网站地图 (sitemap.xml)
          </a>
        </p>
        <p class="text-center text-[11px] leading-relaxed text-slate-600">{{ disclaimer }}</p>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'
import { store } from '../store'
import { SITE_CONFIG } from '../config'

const site = computed(() => store.data?.site || {})
const github = computed(() => store.data?.site?.github || SITE_CONFIG.github)
const disclaimer = computed(() => store.data?.site?.disclaimer || SITE_CONFIG.disclaimer)
// 三站主页超链接（优先数据源里真实 home，缺省用内置常量兜底）
const SOURCE_HOMES = {
  sjjzm: 'https://msdn.sjjzm.com/',
  xitongku: 'https://www.xitongku.com/',
  hello: 'https://hellowindows.cn/',
}
const homeOf = (k) => (store.data?.site?.sources?.[k]?.home)?.replace(/\/+$/, '') || SOURCE_HOMES[k]
</script>
