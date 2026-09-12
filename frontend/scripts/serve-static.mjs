// serve-static.mjs —— 本地静态目录服务器（最接近 Cloudflare Pages 的生产行为）
//
// 与 `vite preview`（SPA-fallback，会把 /detail/xxx 回退到首页 index.html）不同，
// 本脚本按目录解析：/detail/<iso_key> -> dist/detail/<iso_key>/index.html，
// /category/<key> -> dist/category/<key>/index.html，这样本地就能直接看到每条真实详情页。
// 找不到匹配文件时才对根 index.html 做 SPA-fallback（确保 vue-router 深层路由也能运行）。
//
// 用法：npm run preview  （监听 4173，可用 PORT 覆盖）

import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.join(__dirname, '..', 'dist')
const PORT = Number(process.env.PORT || 4173)

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.xml': 'application/xml; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.ico': 'image/x-icon',
  '.webmanifest': 'application/manifest+json',
}

function resolve(url) {
  if (url === '/') url = '/index.html'
  if (url === '' ) url = '/index.html'
  // 防止路径逃逸
  const clean = '/' + url.replace(/^\/+/, '').split('?')[0]
  const target = path.normalize(path.join(root, clean))
  if (!target.startsWith(root)) return null
  if (fs.existsSync(target)) {
    const st = fs.statSync(target)
    if (st.isDirectory()) {
      const idx = path.join(target, 'index.html')
      if (fs.existsSync(idx)) return idx
    } else if (st.isFile()) {
      return target
    }
  }
  // 目录式下标：/detail/<key> -> <key>/index.html
  const idx = path.join(target, 'index.html')
  if (fs.existsSync(idx)) return idx
  // SPA-fallback：找不到真实静态文件时回退根 index.html（保证 vue-router 可运行）
  const fb = path.join(root, 'index.html')
  return fs.existsSync(fb) ? fb : null
}

const server = http.createServer((req, res) => {
  const rurl = req.url || '/'
  const file = resolve(rurl)
  if (!file) {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' })
    res.end('404 Not Found')
    return
  }
  const ext = path.extname(file).toLowerCase()
  // HTML 不让缓存（避免上次 preview 遗留的旧页/回退首页被浏览器缓存导致“详情空白”）
  const cache =
    ext === '.html'
      ? 'no-cache, no-store, must-revalidate'
      : 'public, max-age=31536000, immutable'
  res.writeHead(200, {
    'Content-Type': MIME[ext] || 'application/octet-stream',
    'Cache-Control': cache,
  })
  fs.createReadStream(file).pipe(res)
})

server.listen(PORT, () => {
  console.log(`[serve-static] 本地预览 http://127.0.0.1:${PORT}`)
  console.log(`[serve-static] 静态目录 ${root}`)
})
