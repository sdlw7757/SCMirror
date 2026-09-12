<template>
  <div class="mx-auto max-w-5xl px-4 pb-16 md:px-6">
    <div class="pt-8 md:pt-12">
      <nav class="mb-3 flex items-center gap-1.5 text-xs text-slate-500">
        <RouterLink to="/" class="transition hover:text-cyan-300">首页</RouterLink>
        <span>/</span>
        <span class="text-slate-400">哈希校验工具</span>
      </nav>

      <div class="mb-6">
        <h1 class="text-2xl font-extrabold tracking-tight md:text-3xl">
          <span class="glow-text">SHA256 哈希校验工具</span>
        </h1>
        <p class="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
          在浏览器本地计算文件/文本的 <span class="font-mono text-cyan-300">SHA256</span>（不上传任何数据），
          并可在本站聚合库中检索对应镜像。
        </p>
        <a
          :href="HASHER_URL"
          target="_blank"
          rel="noopener noreferrer nofollow"
          class="btn-primary mt-3 !text-sm"
        >
          <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
          </svg>
          下载 SHA-256 官方校验工具
        </a>
      </div>

      <!-- 文件哈希 -->
      <section class="glass mb-6 p-5">
        <h2 class="mb-3 flex items-center gap-2 text-base font-semibold text-slate-100">
          <span class="h-4 w-1 rounded bg-cyan-400"></span>文件校验
        </h2>
        <label
          class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-white/15 bg-ink-900/40 px-4 py-10 text-center transition hover:border-cyan-400/40 hover:bg-ink-900/60"
          :class="{ 'opacity-50': working }"
        >
          <svg viewBox="0 0 24 24" class="h-8 w-8 text-cyan-400" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 16V4m0 0 4 4m-4-4-4 4" />
            <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
          </svg>
          <p class="text-sm text-slate-300">点击选择 ISO 镜像文件，计算其 SHA256</p>
          <p class="text-xs text-slate-500">文件仅在本机读取，不会上传</p>
          <input type="file" class="hidden" @change="onFile" :disabled="working" />
        </label>

        <div v-if="fileResult" class="mt-4 space-y-2">
          <div class="rounded-lg border border-white/5 bg-ink-900/60 p-3">
            <p class="mb-1 text-xs text-slate-500">文件名</p>
            <p class="break-all text-sm text-slate-200">{{ fileName }}</p>
          </div>
          <div class="rounded-lg border border-white/5 bg-ink-900/60 p-3">
            <p class="mb-1 flex items-center gap-2 text-xs text-slate-500">
              SHA256
              <span v-if="working" class="text-cyan-300">计算中…</span>
            </p>
            <p class="break-all font-mono text-sm text-cyan-200">{{ fileResult }}</p>
          </div>
          <div class="flex flex-wrap gap-2">
            <button class="btn-primary !text-xs" @click="copy(fileResult)">复制</button>
            <button class="btn-ghost !text-xs" @click="searchHash(fileResult)">在站内搜索</button>
          </div>
        </div>
      </section>

      <!-- 文本哈希 -->
      <section class="glass mb-6 p-5">
        <h2 class="mb-3 flex items-center gap-2 text-base font-semibold text-slate-100">
          <span class="h-4 w-1 rounded bg-cyan-400"></span>文本 / URL 校验
        </h2>
        <textarea
          v-model="textInput"
          rows="3"
          placeholder="粘贴任意文本（例如一个下载链接），实时计算 SHA256…"
          class="input-dark resize-y"
        ></textarea>
        <div v-if="textResult" class="mt-3 rounded-lg border border-white/5 bg-ink-900/60 p-3">
          <p class="mb-1 text-xs text-slate-500">SHA256</p>
          <p class="break-all font-mono text-sm text-cyan-200">{{ textResult }}</p>
          <div class="mt-2 flex flex-wrap gap-2">
            <button class="btn-primary !text-xs" @click="copy(textResult)">复制</button>
            <button class="btn-ghost !text-xs" @click="searchHash(textResult)">在站内搜索</button>
          </div>
        </div>
      </section>

      <!-- 站内检索 -->
      <section class="glass p-5">
        <h2 class="mb-3 flex items-center gap-2 text-base font-semibold text-slate-100">
          <span class="h-4 w-1 rounded bg-cyan-400"></span>按哈希检索镜像
        </h2>
        <input v-model="searchInput" placeholder="输入 SHA256 / SHA1 片段（至少 6 位）…" class="input-dark" />
        <div v-if="hashResults.length" class="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
          <RouterLink :to="`/detail/${it.iso_key}`" class="glass glass-hover block p-4" v-for="it in hashResults" :key="it.iso_key">
            <span class="badge-cyan">{{ categoryName(it.category_key) }}</span>
            <p class="mt-2 text-sm font-semibold text-slate-100">{{ it.meta_unified.title }}</p>
            <code class="mt-1 block font-mono text-[11px] text-slate-500">{{ it.meta_unified.sha256 }}</code>
          </RouterLink>
        </div>
        <p v-else-if="searchInput.length >= 6" class="mt-3 text-xs text-slate-500">未在聚合库中检索到匹配镜像</p>
        <p v-if="!secureCtx" class="mt-3 rounded-lg border border-amber-400/30 bg-amber-500/10 p-3 text-xs text-amber-300">
          提示：SHA256 计算需在 HTTPS 或 localhost 安全上下文中进行。
        </p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { findItemsByHash, categoryName } from '../store'
import { copyText } from '../utils/format'
import { HASHER_URL } from '../config'

const route = useRoute()
const secureCtx = computed(() => typeof window !== 'undefined' && window.isSecureContext)

const working = ref(false)
const fileResult = ref('')
const fileName = ref('')
const textInput = ref('')
const textResult = ref('')
const searchInput = ref(route.query.h || '')

// 预填充：从详情页跳转带 ?h= 时直接检索
const hashResults = computed(() => (searchInput.value.length >= 6 ? findItemsByHash(searchInput.value) : []))

watch(textInput, async (v) => {
  if (!secureCtx.value) return
  if (!v.trim()) return (textResult.value = '')
  textResult.value = await sha256Text(v)
})

async function sha256Text(str) {
  const data = new TextEncoder().encode(str)
  const buf = await crypto.subtle.digest('SHA-256', data)
  return toHex(buf)
}

function toHex(buf) {
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, '0')).join('')
}

async function onFile(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  if (!secureCtx.value) {
    alert('当前环境不支持本地 SHA256 计算，请使用 HTTPS')
    return
  }
  fileName.value = file.name
  fileResult.value = ''
  working.value = true
  try {
    const buf = await file.arrayBuffer()
    const digest = await crypto.subtle.digest('SHA-256', buf)
    fileResult.value = toHex(digest)
  } catch (err) {
    fileResult.value = '计算失败：' + err.message
  } finally {
    working.value = false
    e.target.value = ''
  }
}

async function copy(text) {
  if (text) await copyText(text)
}

function searchHash(h) {
  if (h) window.location.href = `/tool-hash?h=${h}`
}
</script>
