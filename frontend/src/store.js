// store.js —— 全站数据仓库：一次性加载 data/iso_data.json，供各页面/组件响应式读取
import { reactive } from 'vue'
import { DATA_URL } from './config'

export const store = reactive({
  data: null, // { site, stats, categories, items }
  loaded: false,
  loading: false,
  error: null,
})

let promise = null

export function loadData(force = false) {
  if (store.loaded && !force) return Promise.resolve(store.data)
  if (promise) return promise
  store.loading = true
  promise = fetch(DATA_URL, { credentials: 'same-origin' })
    .then((r) => {
      if (!r.ok) throw new Error(`数据加载失败 HTTP ${r.status}`)
      return r.json()
    })
    .then((data) => {
      // 保证字段齐全，避免组件空指针
      store.data = {
        site: data.site || {},
        stats: data.stats || {},
        categories: data.categories || [],
        items: data.items || [],
      }
      store.loaded = true
      store.loading = false
      store.error = null
      return store.data
    })
    .catch((e) => {
      store.error = e.message
      store.loading = false
      store.loaded = true // 标记完成避免死循环
      throw e
    })
  return promise
}

export function findItem(isoKey) {
  if (!store.data) return null
  return store.data.items.find((it) => it.iso_key === isoKey) || null
}

export function findCategory(key) {
  if (!store.data) return null
  return store.data.categories.find((c) => c.key === key) || null
}

export function categoryName(key) {
  const c = findCategory(key)
  return c ? c.name : key || '其他'
}

export function findItemsByHash(hashHex) {
  const h = String(hashHex || '').toLowerCase().replace(/[^0-9a-f]/g, '')
  if (h.length < 6 || !store.data) return []
  return store.data.items.filter((it) => {
    const m = it.meta_unified || {}
    if (m.sha256 && m.sha256.startsWith(h)) return true
    for (const s of it.sources_raw || []) {
      const hh = s.hash || {}
      if (hh.sha256 && hh.sha256.startsWith(h)) return true
      if (hh.sha1 && hh.sha1.startsWith(h)) return true
    }
    return false
  })
}