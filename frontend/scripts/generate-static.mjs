// generate-static.mjs —— 全站确定性静态预渲染（SEO 骨架，无需无头浏览器）
//
// 作用：在 vite build（产出 SPA dist）之后，为『首页 / 所有系统分类页 / 所有镜像详情页
//       / 哈希工具 / 知识库』逐条生成独立静态 HTML，注入正确的 <title>、<meta description>、
//       canonical 与可被爬虫读取的服务端渲染内容（真实列表/详情）。
// 这样即使是纯静态托管（Cloudflare Pages）也能保证每一条 URL 都有完整可收录的静态页面，
// 与 Baidu 收录 / sitemap / 动态 TDK 完全闭环，且不依赖任何浏览器环境。
//
// 用法：npm run build（在 vite build 后自动执行）

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.join(here, '..')
const dist = path.join(root, 'dist')

// 域名不写死：构建时由环境变量 SITE_URL 提供绝对地址；未设置则用相对路径（域名自适应，部署后可随时更换）。
const BASE_URL = (process.env.SITE_URL || '').trim().replace(/\/+$/, '')
const SITE = {
  name: '海云镜像',
  name_en: 'SeaCloud Mirror',
  url: BASE_URL,
}

// 从 Vite 构建出的 SPA index.html 中提取真实的 CSS/JS 资源引用，
// 使每个静态页面同源加载同一套样式与脚本，并在客户端由 SPA 接管（增量/交互可用）。
const SPA_INDEX = path.join(dist, 'index.html')
let HEAD_ASSETS = ''
let BODY_ASSETS = ''
try {
  const spa = fs.readFileSync(SPA_INDEX, 'utf-8')
  HEAD_ASSETS = (spa.match(/<link[^>]*rel="stylesheet"[^>]*>/gi) || []).join('')
  BODY_ASSETS = (spa.match(/<script[^>]*type="module"[^>]*><\/script>/gi) || [])
    .concat(spa.match(/<script[^>]*src="\/assets\/[^"]*\.js"[^>]*><\/script>/gi) || [])
    .join('')
} catch (e) {
  console.warn('[generate-static] 读取 SPA index.html 失败:', e.message)
}

function esc(s = '') {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function loadDB() {
  try {
    return JSON.parse(fs.readFileSync(path.join(root, 'public', 'data', 'iso_data.json'), 'utf-8'))
  } catch {
    return { site: {}, stats: {}, categories: [], items: [] }
  }
}

function catName(db, key) {
  const c = db.categories?.find((x) => x.key === key)
  return c?.name || key || '其他'
}

function card(item, db) {
  const m = item.meta_unified || {}
  const hash = (m.sha256 || (item.sources_raw?.[0]?.hash?.sha256) || '').slice(0, 16)
  return `<a href="${SITE.url}/detail/${esc(item.iso_key)}" class="ssr-card">
  <span class="ssr-badge">${esc(catName(db, item.category_key))}</span>
  <span class="ssr-chip">${esc(m.arch || '')}</span><span class="ssr-chip">${esc(m.type || '')}</span>
  <h3>${esc(m.title)}</h3>
  <div class="ssr-meta">${esc(m.version || '')}${m.build ? ' · Build ' + esc(m.build) : ''}${m.size ? ' · ' + esc(m.size) : ''}${m.kb ? ' · ' + esc(m.kb) : ''}</div>
  <code>${esc(hash)}</code>
</a>`
}

function wrap(title, description, body, url) {
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<meta name="robots" content="index,follow" />
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}" />
<link rel="canonical" href="${esc(url)}" />
${HEAD_ASSETS}
</head>
<body>
<!-- 服务端静态内容（含静态 footer）：SPA 挂载后整块隐藏，避免与 Vue 页脚重复 -->
<div id="ssr-shell">
<div class="ssr-app">
<div class="ssr-top"><a href="${SITE.url}/" class="ssr-logo"><span class="ssr-logo-mark">🌊</span><b>${esc(SITE.name)}</b><span class="ssr-logo-en">${esc(SITE.name_en)}</span></a></div>
${body}
</div>
<footer class="ssr-foot">
  <a href="${SITE.url}/sitemap.xml" target="_blank" rel="nofollow">网站地图 (sitemap.xml)</a>
  <span class="ssr-copy">SeaCloud Mirror · 海云镜像 · 仅供学习参考</span>
</footer>
</div>
<!-- 客户端交互挂载点：SPA 接管后隐藏上面的静态骨架 -->
<div id="app"></div>
<script>window.__SSR__=true;</script>
<script>
// 数据就绪（SPA 首屏渲染完成，App 层派发 dsh-prerender-ready）后再隐藏静态骨架，
// 避免在数据(约 3.5MB JSON)解析完成前提前隐藏，消除首开"空白/闪烁"
function hideShell() {
  var app = document.getElementById('app')
  var shell = document.getElementById('ssr-shell')
  if (app && shell && app.children.length > 0) shell.style.display = 'none'
}
window.addEventListener('dsh-prerender-ready', hideShell)
// 兜底：极端情况（事件未触发 / 首屏异常）10 秒后强制隐藏，避免永远双份
setTimeout(hideShell, 10000)
</script>
${BODY_ASSETS}
</body>
</html>`
}

function homeSSR(db) {
  const st = db.stats || {}
  const items = (db.items || []).slice(0, 18)
  const cats = (db.categories || [])
    .map((c) => `<a href="${SITE.url}/category/${esc(c.key)}" class="ssr-pill">${esc(c.name)}</a>`)
    .join('\n')
  const cards = items.map((it) => card(it, db)).join('\n')
  const body = `<header class="ssr-head">
  <h1>${esc(SITE.name)} · ${esc(SITE.name_en)}</h1>
  <p>多源 Windows 官方原版镜像聚合查询：以 SHA256 为主键聚合山己几子木 / 系统库 / HelloWindows 三站元信息。</p>
  <div class="ssr-stats">
    <span>总收录 <b>${esc(st.total ?? 0)}</b></span>
    <span>今日新增 <b>${esc(st.today_new ?? 0)}</b></span>
    <span>今日更新 <b>${esc(st.today_update ?? 0)}</b></span>
    <span>最后同步 ${esc((st.last_sync || '').slice(0, 16))}</span>
  </div>
</header>
<section class="ssr-cats">${cats}</section>
<section>
  <h2>最新镜像</h2>
  <div class="ssr-grid">${cards}</div>
  <p class="ssr-more"><a href="${SITE.url}/tool-hash">哈希校验工具</a> · <a href="${SITE.url}/wiki">知识库</a></p>
</section>`
  return {
    title: `${SITE.name} - 多源 Windows 原版镜像聚合查询 | ${SITE.name_en}`,
    description: `${SITE.name}（${SITE.name_en}）聚合整理山己几子木、系统库、HelloWindows 三站 Windows 官方原版镜像元信息，以 SHA256 为主键统一聚合。`,
    body,
    url: `${SITE.url}/`,
  }
}

function categorySSR(db, key) {
  const c = db.categories?.find((x) => x.key === key)
  const items = (db.items || []).filter((it) => it.category_key === key)
  const cards = items.slice(0, 60).map((it) => card(it, db)).join('\n')
  const name = c?.name || catName(db, key)
  const intro = c?.intro || `${name} 官方原版镜像聚合列表。`
  const body = `<header class="ssr-head">
  <h1>${esc(name)} 原版镜像</h1>
  <p>${esc(intro)}</p>
  <p class="ssr-count">共收录 ${items.length} 条镜像</p>
</header>
<div class="ssr-grid">${cards}</div>`
  return {
    title: `${name} 原版镜像下载 - ${SITE.name}`,
    description: `${intro} 由 ${SITE.name}（${SITE.name_en}）聚合多源数据。`,
    body,
    url: `${SITE.url}/category/${esc(key)}`,
  }
}

function detailSSR(db, isoKey) {
  const item = (db.items || []).find((it) => it.iso_key === isoKey)
  if (!item) {
    return {
      title: `未找到镜像 - ${SITE.name}`,
      description: '未找到该镜像。请返回首页重新搜索。',
      body: `<header class="ssr-head"><h1>未找到该镜像</h1><p><a href="${SITE.url}/">返回首页</a></p></header>`,
      url: `${SITE.url}/detail/${esc(isoKey)}`,
    }
  }
  const m = item.meta_unified || {}
  const sources = (item.sources_raw || [])
    .map((s) => `<div class="ssr-src"><b>${esc(s.source_name)}</b><br />文件名：${esc(s.filename || '-')}<br />SHA256：${esc(s.hash?.sha256 || '-')}<br />采集：${esc(s.crawl_time || '-')}</div>`)
    .join('\n')
  const body = `<header class="ssr-head">
  <span class="ssr-badge">${esc(catName(db, item.category_key))}</span>
  <h1>${esc(m.title)}</h1>
  <p>${esc(m.desc || `${m.title} 官方原版镜像，多源聚合对照。`)}</p>
  <dl class="ssr-dl">
    <dt>版本</dt><dd>${esc(m.version || '-')}</dd>
    <dt>Build</dt><dd>${esc(m.build || '-')}</dd>
    <dt>架构</dt><dd>${esc(m.arch || '-')}</dd>
    <dt>大小</dt><dd>${esc(m.size || '-')}</dd>
    <dt>SHA256</dt><dd><code>${esc(m.sha256 || '-')}</code></dd>
    <dt>生命周期</dt><dd>${esc(m.lifecycle || '-')}</dd>
    <dt>KB</dt><dd>${esc(m.kb || '-')}</dd>
  </dl>
</header>
<section><h2>三站原始数据对照</h2>${sources}</section>`
  return {
    title: `${m.title} 下载 - ${SITE.name}`,
    description: (m.desc || `${m.title} 官方原版镜像。`).slice(0, 150),
    body,
    url: `${SITE.url}/detail/${esc(isoKey)}`,
  }
}

function toolSSR() {
  const body = `<header class="ssr-head"><h1>SHA256 哈希校验工具</h1><p>在浏览器本地计算文件的 SHA256，可对照本站聚合库中各数据源公布的哈希，校验是否为官方原版。</p></header>`
  return { title: `SHA256 哈希校验工具 - ${SITE.name}`, description: '海云镜像 SHA256 哈希校验工具：本地计算文件/文本哈希，用于校验官方原版 Windows 镜像。', body, url: `${SITE.url}/tool-hash` }
}

function wikiSSR() {
  const body = `<header class="ssr-head"><h1>Windows 镜像知识库</h1><p>常见概念、版本区分与校验方法，帮助你正确选择与验证官方原版镜像。</p></header>`
  return { title: `知识库 - ${SITE.name}`, description: '海云镜像知识库：消费者版/商业版区分、32/64/ARM 位选择、哈希校验方法与支持生命周期说明。', body, url: `${SITE.url}/wiki` }
}

const SSRCSS = `<style>
.ssr-app{max-width:1200px;margin:0 auto;padding:20px;background:#05080f;color:#e2e8f0;font-family:system-ui,'Microsoft YaHei',sans-serif}
.ssr-top{padding:8px 14px;border-bottom:1px solid #1e293b;margin-bottom:18px;border-radius:10px;background:#0d1424}
.ssr-logo{display:inline-flex;align-items:center;gap:8px;color:#e2e8f0;text-decoration:none;font-weight:700;font-size:15px}
.ssr-logo-mark{font-size:18px}
.ssr-logo b{color:#67e8f9}
.ssr-logo-en{margin-left:2px;font-size:10px;letter-spacing:.2em;color:#64748b;font-weight:400;text-transform:uppercase}
.ssr-head{background:linear-gradient(120deg,#0e7490,#0284c7);color:#fff;padding:28px;border-radius:14px;margin-bottom:18px}
.ssr-head h1{margin:0;font-size:26px}
.ssr-head p{color:#cffafe;opacity:.92}
.ssr-stats{display:flex;flex-wrap:wrap;gap:14px;margin-top:12px;background:rgba(255,255,255,.12);border-radius:10px;padding:10px 14px}
.ssr-stats b{color:#a5f3fc}
.ssr-cats{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px}
.ssr-pill{background:#0e7490;color:#fff;padding:6px 12px;border-radius:999px;text-decoration:none}
.ssr-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.ssr-card{background:#0d1424;border:1px solid #1e293b;border-radius:12px;padding:14px;color:#e2e8f0;text-decoration:none;display:block}
.ssr-card h3{font-size:15px;margin:6px 0}
.ssr-card code{color:#67e8f9;font-size:11px}
.ssr-badge{background:#155e75;color:#a5f3fc;border-radius:6px;padding:2px 8px;font-size:12px}
.ssr-chip{background:#1e293b;border:1px solid #334155;border-radius:6px;padding:1px 7px;font-size:11px;margin-right:4px}
.ssr-meta{font-size:12px;color:#94a3b8;margin-top:4px}
.ssr-more{margin-top:16px}
.ssr-dl{display:grid;grid-template-columns:80px 1fr;gap:8px 12px;font-size:14px}
.ssr-dl dt{color:#94a3b8}
.ssr-src{background:#0d1424;border:1px solid #1e293b;border-radius:10px;padding:12px;margin-bottom:10px;font-size:13px}
.ssr-count{color:#cffafe}
.ssr-foot{text-align:center;padding:14px 10px;font-size:11px;color:#64748b;border-top:1px solid #1e293b;margin-top:26px}
.ssr-foot a{color:#64748b;text-decoration:underline;text-underline-offset:2px}
.ssr-foot .ssr-copy{display:block;margin-top:4px;color:#475569}
</style>`

function main() {
  const db = loadDB()
  const meta = (r) => ({ ...r, body: SSRCSS + r.body })
  const pages = [
    { route: '/', target: 'index.html', meta: meta(homeSSR(db)) },
    { route: '/tool-hash', target: 'tool-hash/index.html', meta: meta(toolSSR()) },
    { route: '/wiki', target: 'wiki/index.html', meta: meta(wikiSSR()) },
  ]
  for (const c of db.categories || []) {
    pages.push({ route: `/category/${c.key}`, target: `category/${c.key}/index.html`, meta: meta(categorySSR(db, c.key)) })
  }
  for (const it of db.items || []) {
    pages.push({ route: `/detail/${it.iso_key}`, target: `detail/${it.iso_key}/index.html`, meta: meta(detailSSR(db, it.iso_key)) })
  }

  let written = 0
  for (const p of pages) {
    const html = wrap(p.meta.title, p.meta.description, p.meta.body, p.meta.url)
    const out = path.join(dist, p.target)
    fs.mkdirSync(path.dirname(out), { recursive: true })
    fs.writeFileSync(out, html, 'utf-8')
    written += 1
  }
  console.log(`[generate-static] 已生成 ${written} 个静态页面（含全部分类页与镜像详情页）`)
}

main()
