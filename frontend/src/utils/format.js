// format.js —— 展示格式化工具

export function typeLabel(t) {
  return { consumer: '消费者版（零售）', business: '商业版（批量）' }[t] || ''
}

export function typeShort(t) {
  return { consumer: '零售', business: '批量' }[t] || ''
}

export function archLabel(a) {
  return { x64: 'x64 位', x86: 'x86 位', arm64: 'ARM64' }[a || ''] || a || '未知'
}

export function truncate(str, n = 48) {
  if (!str) return ''
  return str.length > n ? str.slice(0, n) + '…' : str
}

/** 把完整时间 "2026-09-11 22:36:26" 简化为日期 */
export function shortTime(s) {
  if (!s) return '-'
  return String(s).slice(0, 10)
}

export function hashText(h, n = 16) {
  if (!h) return '-'
  return h.length > n ? `${h.slice(0, n)}…` : h
}

// 三站唯一色彩映射（全站唯一来源，任意组件都调用此处）：
// 山己几子木=青(cyan) · 系统库=绿(emerald) · HelloWindows=紫(violet)
export function sourceColor(source) {
  return {
    sjjzm: { badge: 'bg-cyan-500/15 text-cyan-300 border-cyan-400/30', dot: 'bg-cyan-400' },
    xitongku: { badge: 'bg-emerald-500/15 text-emerald-300 border-emerald-400/30', dot: 'bg-emerald-400' },
    hello: { badge: 'bg-violet-500/15 text-violet-300 border-violet-400/30', dot: 'bg-violet-400' },
  }[source] || { badge: 'bg-slate-500/15 text-slate-300 border-slate-400/30', dot: 'bg-slate-400' }
}

export function fmtCount(n) {
  return Number(n || 0).toLocaleString('zh-CN')
}

/** 是否为外链（ed2k/magnet/http…） */
export function isExternal(u) {
  return /^(https?:|ed2k:|magnet:|thunder:)/i.test(u || '')
}

export function domainOf(u) {
  try {
    return new URL(u).hostname.replace(/^www\./, '')
  } catch {
    return u
  }
}

/** 根据下载链接类型取展示名 */
export function linkDisplayName(u, fallback = '下载') {
  if (/^ed2k:/i.test(u)) return 'ED2K'
  if (/^magnet:/i.test(u)) return '磁力链接'
  if (/thunder:/i.test(u)) return '迅雷'
  const d = domainOf(u)
  if (d.includes('alipan') || d.includes('aliyundrive')) return '阿里云盘'
  if (d.includes('weiyun')) return '腾讯微云'
  if (d.includes('pan.baidu')) return '百度网盘'
  if (d.includes('189.cn')) return '天翼云盘'
  if (d.includes('caiyun.139')) return '移动云盘'
  if (d.includes('quark')) return '夸克网盘'
  if (d.includes('123pan') || d.includes('123.cn')) return '123云盘'
  if (d.includes('xunlei')) return '迅雷云盘'
  return fallback
}

/** 页面 TDK 设置（动态 title/description，预渲染同样生效） */
export function setPageMeta(title, description) {
  if (typeof document === 'undefined') return
  document.title = title
  let desc = document.querySelector('meta[name="description"]')
  if (!desc) {
    desc = document.createElement('meta')
    desc.setAttribute('name', 'description')
    document.head.appendChild(desc)
  }
  desc.setAttribute('content', description)
}

/** 复制文本 */
export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    try {
      const ta = document.createElement('textarea')
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      return true
    } catch {
      return false
    }
  }
}