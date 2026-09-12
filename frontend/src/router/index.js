// router/index.js —— 全站路由
// 页面清单：
//   /                   首页
//   /category/:categoryKey  系统分类详情页（win11/win10/win7/server…）
//   /detail/:isoKey     镜像详情页
//   /tool-hash          哈希校验工具
//   /wiki               知识库
import { createRouter, createWebHistory } from 'vue-router'
import { loadData, findItem, findCategory } from '../store'
import { SITE_CONFIG } from '../config'
import { setPageMeta } from '../utils/format'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
    meta: { title: `${SITE_CONFIG.name} - 多源 Windows 原版镜像聚合查询` },
  },
  {
    path: '/category/:categoryKey',
    name: 'category',
    component: () => import('../views/CategoryView.vue'),
    meta: { title: (to) => '' },
  },
  {
    path: '/detail/:isoKey',
    name: 'detail',
    component: () => import('../views/DetailView.vue'),
    meta: { title: (to) => '' },
  },
  {
    path: '/tool-hash',
    name: 'tool-hash',
    component: () => import('../views/ToolHashView.vue'),
    meta: { title: `SHA256 哈希校验工具 - ${SITE_CONFIG.name}` },
  },
  {
    path: '/wiki',
    name: 'wiki',
    component: () => import('../views/WikiView.vue'),
    meta: { title: `知识库 - ${SITE_CONFIG.name}` },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  // base 跟随 Vite 的 build.base（import.meta.env.BASE_URL）：
  // 根部署='/',子路径部署='/SCMirror/'（VITE_BASE 注入）。保证 SPA 内路由/链接同样带前缀。
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

// 预取数据（预渲染时 fetch 静态 JSON，事件触发由 App.vue 负责）
loadData().catch(() => {})

// 动态 TDK：分类页/详情页生成独立 title 与 description，均带站点名“海云镜像”
router.afterEach((to) => {
  const base = SITE_CONFIG.name
  if (to.name === 'category') {
    const cat = findCategory(to.params.categoryKey)
    if (cat) {
      const name = cat.name || to.params.categoryKey
      const desc = cat.intro || `${name} 官方原版镜像聚合列表，海云镜像聚合山己几子木/系统库/HelloWindows 多源数据。`
      setPageMeta(`${name} 原版镜像下载 - ${base}`, desc)
    } else {
      setPageMeta(`系统分类 - ${base}`, `按系统分类浏览 Windows 原版镜像，${base}。`)
    }
  } else if (to.name === 'detail') {
    const item = findItem(to.params.isoKey)
    if (item) {
      const m = item.meta_unified || {}
      const title = `${m.title || 'Windows 镜像'} 下载 - ${base}`
      setPageMeta(title, m.desc || `${m.title} 官方原版镜像信息与多源下载链接，${base}。`)
    } else {
      setPageMeta(`镜像详情 - ${base}`, `Windows 原版镜像详情，${base}。`)
    }
  } else if (to.meta.title) {
    setPageMeta(String(to.meta.title), `海云镜像聚合整理三站 Windows 官方原版镜像元信息与下载链接。`)
  }
})

export default router