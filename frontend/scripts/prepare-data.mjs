// prepare-data.mjs —— 将仓库根 data/iso_data.json 复制到 frontend/public/data/iso_data.json
// 使构建/预渲染/运行时均能直接读取（纯静态，前端不计算统计）。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.join(here, '..', '..')
const src = path.join(root, 'data', 'iso_data.json')
const outDir = path.join(here, '..', 'public', 'data')
const out = path.join(outDir, 'iso_data.json')

fs.mkdirSync(outDir, { recursive: true })

if (fs.existsSync(src)) {
  const raw = fs.readFileSync(src, 'utf-8')
  fs.writeFileSync(out, raw, 'utf-8')
  const obj = JSON.parse(raw)
  console.log(
    `[prepare-data] 已复制 ${src} -> ${out}（${obj.stats?.total ?? 0} 条镜像，${(obj.items?.length ?? 0).toLocaleString()} 条记录）`
  )
} else {
  // 数据缺失时提供最小可运行结构，避免构建/页面崩溃
  const fallback = {
    site: {
      name: '海云镜像',
      name_en: 'SeaCloud Mirror',
      url: '',   // 域名自适应，避免写死
      github: 'https://github.com/sdlw7757/SCMirror',
      disclaimer:
        '【免责声明】本站仅聚合整理网络公开元信息与下载链接，不存储镜像文件。软件版权归微软所有，请使用正版。本站仅供学习参考，不对文件安全与完整性负责。',
      sources: {},
    },
    stats: { total: 0, today_new: 0, today_update: 0, today_count: 0, last_sync: '', by_category: {} },
    categories: [],
    items: [],
  }
  fs.writeFileSync(out, JSON.stringify(fallback, null, 2), 'utf-8')
  console.warn('[prepare-data] 未找到 data/iso_data.json，已写 fallback 空数据（可运行）')
}
