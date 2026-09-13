<template>
  <div class="min-h-screen flex flex-col bg-ink-950 text-slate-200">
    <SiteNav />
    <main class="flex-1 w-full">
      <RouterView v-if="store.loaded" />
      <!-- 数据就绪前的轻量提示（首屏由 SSR 骨架承载，避免大转圈叠加遮挡） -->
      <div v-else class="py-2 text-center">
        <p class="inline-flex items-center gap-2 text-xs text-slate-500">
          <span class="h-2 w-2 animate-pulse rounded-full bg-cyan-400"></span>
          数据同步中…
        </p>
      </div>
    </main>
    <SiteFooter />
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount } from 'vue'
import { store, loadData } from './store'
import SiteNav from './components/SiteNav.vue'
import SiteFooter from './components/SiteFooter.vue'

// 预渲染就绪事件：数据加载完成且首帧渲染后触发，供 vite-plugin-prerender 捕获
function fireReady() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event('dsh-prerender-ready'))
  }
}

onMounted(async () => {
  try {
    await loadData()
  } catch (e) {
    // 数据加载失败也触发就绪，避免预渲染挂起
    console.error(e)
  }
  // 给首帧渲染留一点时间
  setTimeout(fireReady, 300)
})

// 兜底：极端情况下 8 秒后仍触发一次
const t = setTimeout(fireReady, 8000)
onBeforeUnmount(() => clearTimeout(t))
</script>
