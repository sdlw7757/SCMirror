// config.js —— 全局站点配置常量（名称、GitHub 链接、免责声明集中于此，便于修改）
// 域名不写死：siteBase() 运行时取当前访问域名，更换网址无需改任何代码。
export function siteBase() {
  if (typeof window !== 'undefined' && window.location && window.location.origin) {
    return String(window.location.origin).replace(/\/$/, '')
  }
  return ''
}

export const SITE_CONFIG = {
  name: '海云镜像',
  name_en: 'SeaCloud Mirror',
  // 自适应：浏览器打开时即当前访问域名；未在浏览器环境（构建/SSR）时为空
  url: siteBase(),

  // ① 页脚 GitHub 仓库跳转链接：修改这里即可全局生效
  github: 'https://github.com/sdlw7757/SCMirror',

  // ② 简短版免责声明（仅页脚展示，弱化字体）
  disclaimer:
    '【免责声明】本站仅聚合整理网络公开元信息与下载链接，不存储镜像文件。软件版权归微软所有，请使用正版。本站仅供学习参考，不对文件安全与完整性负责。',
}

export const DATA_URL = '/data/iso_data.json'

// SHA-256 校验工具下载链接（集中于此，便于更换）
export const HASHER_URL = 'https://yun.139.com/shareweb/#/w/i/2xG3tQkP7njig'