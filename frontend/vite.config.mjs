import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { createRequire } from 'node:module'
import fs from 'node:fs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// vite-plugin-prerender 的 ESM dist 内部仍使用 `require`，在严格 ESM 下会崩溃。
// 在加载该插件前，把 `require` 注入到全局作用域（createRequire 按本文件位置解析），使其可用。
const __require = createRequire(import.meta.url)
globalThis.require = __require
globalThis.__filename = import.meta.url
globalThis.__dirname = __dirname

/**
 * 读取仓库根 data/iso_data.json，枚举需要浏览器级预渲染的路由。
 * 文件缺失或解析失败时回退为基础 SPA 路由，保证构建不中断。
 */
function collectRoutes() {
  const routes = ['/', '/tool-hash', '/wiki']
  try {
    const dbPath = path.join(__dirname, '..', 'data', 'iso_data.json')
    if (fs.existsSync(dbPath)) {
      const db = JSON.parse(fs.readFileSync(dbPath, 'utf-8'))
      for (const c of db.categories || []) {
        if (c.key) routes.push(`/category/${c.key}`)
      }
      for (const it of db.items || []) {
        if (it.iso_key) routes.push(`/detail/${it.iso_key}`)
      }
    }
  } catch (e) {
    console.warn('[prerender] 读取 data/iso_data.json 失败:', e.message)
  }
  return routes
}

// Vite 支持异步配置：先确保全局 require 注入，再动态引入插件。
// 默认关闭浏览器级预渲染（速度快、不依赖无头浏览器）；每一条路由的完整静态 HTML
// 由 scripts/generate-static.mjs 在构建后确定性生成（Cloudflare Pages 稳定可用，适合百度收录）。
// 如需「可选、浏览器级」的完整 DOM 预渲染，可显式设置 PRERENDER=browser。
export default async () => {
  const vitePrerender = (await import('vite-plugin-prerender')).default
  const prerenderEnabled = process.env.PRERENDER === 'browser'

  return defineConfig({
    plugins: [
      vue(),
      prerenderEnabled &&
        vitePrerender({
          staticDir: path.join(__dirname, 'dist'),
          routes: collectRoutes(),
          renderer: new vitePrerender.PuppeteerRenderer({
            headless: true,
            renderAfterDocumentEvent: 'dsh-prerender-ready',
            renderAfterTime: 3000,
            timeout: 60000,
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
          }),
          postProcess(renderedRoute) {
            renderedRoute.route = renderedRoute.originalRoute
            return renderedRoute
          },
        }),
    ],
    resolve: {
      alias: {
        '@': path.join(__dirname, 'src'),
      },
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['vue', 'vue-router'],
          },
        },
      },
    },
    server: {
      port: 5173,
      host: true,
    },
  })
}
