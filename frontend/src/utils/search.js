// search.js —— 前端模糊搜索：不要求完全匹配，支持 版本/标题/build号/sha256片段/KB编号
// 输入“10”即可过滤出所有 Windows 10 相关镜像

const WINDOWS_10_ALIAS = /^10$/

function buildHaystack(item, categoryName = '') {
  const m = item.meta_unified || {}
  const parts = [
    m.title,
    m.edition,
    m.version,
    m.build,
    m.arch,
    m.type,
    m.kb,
    m.sha256,
    m.size,
    categoryName,
    item.category_key,
  ]
  return parts.filter(Boolean).join(' ').toLowerCase()
}

/**
 * 模糊过滤 + 打分排序。
 * @param {Array} items 镜像列表
 * @param {string} query 查询词（可为空）
 * @param {Function} categoryName 分类名解析
 * @returns {Array} 过滤+排序后的镜像
 */
export function fuzzyFilter(items, query, categoryName = (k) => k) {
  const q = String(query || '').trim().toLowerCase()
  if (!q) return items

  const isWin10Alias = WINDOWS_10_ALIAS.test(q)
  const tokens = q.split(/\s+/)

  const scored = []
  for (const item of items) {
    const m = item.meta_unified || {}
    const cat = categoryName(item.category_key) || ''
    const hay = buildHaystack(item, cat)

    let ok = true
    let score = 0
    for (const token of tokens) {
      if (!token) continue
      if (!hay.includes(token)) {
        // 特例：输 “10” 时，Windows 10 相关镜像视作命中（标题含 windows10/windows 10）
        if (!(isWin10Alias && (m.title || '').toLowerCase().includes('windows 10'))) {
          ok = false
          break
        }
      }
    }
    if (!ok) continue

    // 加权打分：标题命中权重最高（字段统一 String 强转，防数据源输出数字时崩）
    const S = (x) => String(x || '').toLowerCase()
    const title = S(m.title)
    if (tokens.every((t) => title.includes(t))) score += 20
    if (isWin10Alias) {
      if (title.includes('windows 10') || title.includes('windows10')) score += 30
      if (String(item.category_key) === 'win10') score += 12
    }
    if (S(m.version).includes(q)) score += 8
    if (S(m.build).includes(q)) score += 8
    if (S(m.kb).includes(q)) score += 6
    if (S(m.sha256).startsWith(q)) score += 10
    if (S(m.arch).includes(q)) score += 4

    scored.push({ item, score })
  }

  scored.sort((a, b) => b.score - a.score)
  return scored.map((s) => s.item)
}

/** 高级筛选：按 分类/架构/零售批量/是否终止支持 过滤 */
export function applyFilters(items, filters = {}) {
  return items.filter((item) => {
    const m = item.meta_unified || {}
    if (filters.category && filters.category !== 'all' && item.category_key !== filters.category) return false
    if (filters.arch && filters.arch !== 'all' && (m.arch || '') !== filters.arch) return false
    if (filters.type && filters.type !== 'all' && (m.type || '') !== filters.type) return false
    if (filters.lifecycle && filters.lifecycle !== 'all') {
      const state = m.lifecycle_state || ''
      if (filters.lifecycle === 'ended' && state !== 'ended') return false
      if (filters.lifecycle === 'supported' && state !== 'supported') return false
    }
    return true
  })
}