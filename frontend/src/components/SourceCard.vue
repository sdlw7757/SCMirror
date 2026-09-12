<template>
  <div class="glass p-5 h-full flex flex-col">
    <!-- 来源头 -->
    <div class="mb-3 flex items-center justify-between gap-2">
      <div class="flex items-center gap-2">
        <span :class="['h-2.5 w-2.5 rounded-full', colors.dot]"></span>
        <span class="text-sm font-semibold text-slate-100">{{ src.source_name }}</span>
      </div>
      <a
        :href="src.home"
        target="_blank"
        rel="noopener noreferrer"
        class="text-[11px] text-slate-500 underline-offset-2 transition hover:text-cyan-300 hover:underline"
      >
        原文主页 ↗
      </a>
    </div>

    <!-- 采集时间 -->
    <p class="mb-3 flex items-center gap-1.5 text-[11px] text-slate-500">
      <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </svg>
      采集时间：{{ src.crawl_time }}
    </p>

    <!-- 文件名 -->
    <div class="mb-3 rounded-lg border border-white/5 bg-ink-900/60 p-2">
      <p class="mb-1 text-[11px] text-slate-500">原始文件名</p>
      <code class="block break-all font-mono text-xs text-slate-300">{{ src.filename || '-' }}</code>
    </div>

    <!-- 哈希 -->
    <div class="mb-3 space-y-1.5">
      <div v-if="src.hash && src.hash.sha256" class="hashline">
        <span class="hashlabel">SHA256</span>
        <button class="hashvalue" :class="copyState.sha256 ? 'copied' : ''" @click="copy('sha256')">
          {{ short(src.hash.sha256) }}
          <span class="copyicon">⧉</span>
        </button>
      </div>
      <div v-if="src.hash && src.hash.sha1" class="hashline">
        <span class="hashlabel">SHA1</span>
        <button class="hashvalue" :class="copyState.sha1 ? 'copied' : ''" @click="copy('sha1')">
          {{ short(src.hash.sha1) }}
          <span class="copyicon">⧉</span>
        </button>
      </div>
      <div v-if="src.hash && src.hash.md5" class="hashline">
        <span class="hashlabel">MD5</span>
        <span class="hashvalue md5 cursor-default">{{ short(src.hash.md5) }}</span>
      </div>
      <div v-if="src.size" class="hashline">
        <span class="hashlabel">大小</span>
        <span class="hashvalue cursor-default">{{ src.size }}</span>
      </div>
    </div>

    <!-- 官方直链：ED2K / 磁力（醒目，可复制完整地址） -->
    <div v-if="direct.length" class="mb-3">
      <p class="mb-2 flex items-center gap-1.5 text-[11px] font-medium text-emerald-300">
        <svg viewBox="0 0 24 24" class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M13 2 3 14h7l-1 8 10-12h-7l1-8z" />
        </svg>
        官方直链 · ED2K / 磁力（点击复制完整地址）
      </p>
      <div class="grid grid-cols-1 gap-2">
        <div
          v-for="(l, i) in direct"
          :key="'d' + i"
          class="flex items-center justify-between gap-2 rounded-lg border border-emerald-400/30 bg-emerald-500/10 px-3 py-1.5"
        >
          <span class="min-w-0 flex-1 text-xs font-semibold text-emerald-300">{{ linkTitle(l) }}</span>
          <button
            class="shrink-0 rounded-md border border-emerald-400/30 bg-emerald-500/10 px-2 py-1 text-[11px] text-emerald-200 transition hover:bg-emerald-500/20"
            @click="copyUrl(l.url)"
            title="复制完整链接"
          >
            {{ copyIdx === i ? '已复制 ✓' : '复制' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 网盘 / 其他地址（点击自动复制对应密码后跳转） -->
    <div class="mt-auto">
      <template v-if="net.length">
        <p class="mb-2 text-[11px] text-slate-500">网盘地址（{{ net.length }} 项，点击自动复制提取码）</p>
        <div class="grid grid-cols-1 gap-1.5">
          <a
            v-for="(l, i) in net"
            :key="'n' + i"
            :href="l.url"
            target="_blank"
            rel="noopener noreferrer nofollow"
            class="flex items-center justify-between gap-2 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-xs text-slate-300 transition hover:border-cyan-400/40 hover:text-cyan-200"
            @click.prevent="goNet(l)"
          >
            <span class="truncate">{{ l.name || linkDisplayName(l.url) }}</span>
            <span v-if="netPwd(l)" class="shrink-0 text-[10px] text-amber-300/90" title="打开网盘后直接粘贴提取码即可">
              🔑 {{ netPwd(l) }}
            </span>
            <span v-else class="ml-1 shrink-0 text-cyan-300/70">↗</span>
          </a>
        </div>
      </template>
      <a
        v-else
        :href="src.url"
        target="_blank"
        rel="noopener noreferrer nofollow"
        class="flex items-center justify-between rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-xs text-slate-300 hover:border-cyan-400/40"
      >
        <span class="truncate">{{ src.url || '未提供' }}</span>
        <span class="ml-2 shrink-0 text-cyan-300/70">↗</span>
      </a>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { hashText, copyText, linkDisplayName } from '../utils/format'
import { sourceColor } from '../utils/format'

const props = defineProps({ src: { type: Object, required: true } })

const colors = sourceColor(props.src.source)
const copyState = reactive({ sha256: false, sha1: false })
const copyIdx = ref(-1)

function short(h, n = 26) {
  return hashText(h || '', n)
}

async function copy(kind) {
  const h = props.src.hash ? props.src.hash[kind] : ''
  if (!h) return
  const ok = await copyText(h)
  if (!ok) return
  copyState[kind] = true
  setTimeout(() => (copyState[kind] = false), 1600)
}

const urlsList = computed(() => props.src.urls || [])
// ED2K / 磁力：单独醒目直链区
const direct = computed(() =>
  urlsList.value.filter((l) => {
    const u = (l && l.url) || ''
    return u.startsWith('ed2k://') || u.startsWith('magnet:')
  })
)
// 网盘密码表：{ 网盘名(去后缀) : 密码 }，如 百度网盘 -> msdn、移动云盘 -> ytyy
const pwdMap = computed(() => {
  const m = {}
  for (const l of urlsList.value) {
    const n = (l && l.name) || ''
    if ((l && l.isPwd) || n.includes('密码') || n.includes('提取码')) {
      const key = n.replace(/密码|提取码|：|:/g, '').trim()
      if (key) m[key] = l.url
    }
  }
  return m
})
// 根据网盘链接名取对应密码
function netPwd(l) {
  const n = (l && l.name) || ''
  const key = n.replace(/地址|链接|下载/g, '').trim()
  return pwdMap.value[key] || ''
}
// 点击网盘链接：先复制对应密码到剪贴板，再打开网盘
async function goNet(l) {
  if (!l || !l.url) return
  const pwd = netPwd(l)
  if (pwd) await copyText(pwd)
  window.open(l.url, '_blank', 'noopener,noreferrer')
}
// 网盘 / 其他 http 地址（排除密码项）
const net = computed(() =>
  urlsList.value.filter((l) => {
    const u = (l && l.url) || ''
    const n = (l && l.name) || ''
    if (!u) return false
    if (u.startsWith('ed2k://') || u.startsWith('magnet:')) return false
    if ((l && l.isPwd) || n.includes('密码') || n.includes('提取码')) return false
    return true
  })
)
function linkTitle(l) {
  const u = (l && l.url) || ''
  if (u.startsWith('ed2k://')) return 'ED2K 电驴链接'
  if (u.startsWith('magnet:')) return 'BT 磁力链接'
  return (l && (l.name || linkDisplayName(u))) || '下载'
}
async function copyUrl(u) {
  if (!u) return
  const ok = await copyText(u)
  if (!ok) return
  const i = direct.value.findIndex((l) => l.url === u)
  copyIdx.value = i
  setTimeout(() => (copyIdx.value = -1), 1600)
}
</script>

<style scoped>
.hashline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.hashlabel {
  flex: 0 0 auto;
  font-size: 11px;
  color: #64748b;
  width: 44px;
}
.hashvalue {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 11px;
  color: #94a3b8;
  text-align: right;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: color 0.2s;
}
button.hashvalue:hover {
  color: #67e8f9;
}
/* MD5 用绿色强调 */
.hashvalue.md5 {
  color: #34d399;
  font-weight: 600;
}
button.hashvalue.md5:hover {
  color: #6ee7b7;
}
.hashvalue.copied {
  color: #34d399;
}
.copyicon {
  font-size: 12px;
  opacity: 0.6;
}
</style>
