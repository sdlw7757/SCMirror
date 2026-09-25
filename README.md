<div align="center">

# 🌊 海云镜像 · SeaCloud Mirror

**多源 Windows 官方原版镜像聚合查询站**

零服务器 · 全自动更新 · 全自动百度收录

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Vue](https://img.shields.io/badge/Vue-3.x-42b883.svg)](https://vuejs.org/)
[![Vite](https://img.shields.io/badge/Vite-5-646cff.svg)](https://vitejs.dev/)
[![Tailwind](https://img.shields.io/badge/Tailwind-3-38bdf8.svg)](https://tailwindcss.com/)
[![Python](https://img.shields.io/badge/Python-3-3776ab.svg)](https://www.python.org/)
[![Cloudflare Pages](https://img.shields.io/badge/Cloudflare-Pages-f38020.svg)](https://pages.cloudflare.com/)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-scheduled-2088ff.svg)](.github/workflows/crawl.yml)

</div>

---

## ✨ 项目特性

| 特性 | 说明 |
| --- | --- |
| 🖥 **零服务器纯静态** | 部署到 Cloudflare Pages，仅凭静态文件即可运行，无需后端进程 |
| 🔄 **全自动更新** | GitHub Actions 每日 02:00(北京时间) 自动抓取三站 → 合并 → 推送 → 提交 |
| 🔍 **全自动百度收录** | 每次更新自动增量推送 sitemap 到百度，无需人工 | 
| 🧲 **三源聚合** | 山己几子木 / 系统库 / HelloWindows，三站各自独立保存，互不干扰 |
| ⚙️ **域名自适应** | 不绑定固定域名，换网址无需改代码，一处配置即生效 |
| 🔐 **SHA256 主键** | 以 SHA256 为全局唯一主键聚合，杜绝重复与冲突 |

## 📦 快速上手

```bash
# 1) 跑一次爬虫（抓取三站并生成 data/iso_data.json、sitemap.xml、robots.txt）
pip install requests beautifulsoup4 lxml
python -m crawler.main

# 2) 前端：开发 / 构建 / 预览
cd frontend
npm install
npm run dev          # 本地开发
npm run build        # 构建到 dist（Vite 打包 + 确定性全站静态预渲染）
npm run build:browser # 可选：无头浏览器 DOM 级预渲染（PRERENDER=browser，较慢）
npm run preview      # 预览 dist
```

> 爬虫可选参数：`--only sjjzm|xitongku|hello`、`--skip-crawl`、`--skip-sitemap`、`--skip-baidu`、`--dry-run`

## 📁 项目结构

```
SCMirror/
├── .github/workflows/crawl.yml  # GitHub Actions：每日 02:00(北京) 自动抓取+合并+推送+提交
├── crawler/                     # Python 爬虫系统（零服务器）
│   ├── main.py                  # 主入口：抓取→合并→统计→sitemap→百度推送
│   ├── common.py                # 共享配置 / 常量 / HTTP / 分类
│   ├── p1_sjjzm.py              # 数据源① 山己几子木  msdn.sjjzm.com
│   ├── p2_xitongku.py           # 数据源② 系统库    xitongku.com（含生命周期 + KB）
│   ├── p3_hello.py              # 数据源③ HelloWindows  hellowindows.cn
│   ├── merge.py                 # 三站合并（SHA256 全局唯一主键 + 择优汇总）
│   ├── stats.py                 # 自动统计（写入 JSON 顶层，前端直接读取）
│   ├── sitemap.py               # 生成 sitemap.xml + robots.txt
│   └── baidu_push.py            # 百度收录主动推送（增量）
├── data/
│   ├── iso_data.json            # 最终聚合数据（前端 / SEO / 统计来源）
│   ├── raw/                     # 三站原始抓取快照（一站一文件）
│   └── .baidu_push_state.json   # 百度推送增量状态
└── frontend/                    # Vue3 + Vite + TailwindCSS 科技风前台（完整静态）
    ├── src/                     # 组件 / 视图 / 路由 / 工具
    ├── public/                  # favicon / robots.txt / sitemap.xml / data/iso_data.json
    ├── vite.config.mjs          # vite-plugin-prerender（可选浏览器级预渲染）
    ├── scripts/generate-static.mjs # 确定性全站静态预渲染（首页/分类/详情/工具/知识库）
    └── package.json             # 构建命令 npm run build -> dist
```

## 🗂 数据规则（核心）

- 以 **SHA256** 为全局唯一主键；某源仅提供 SHA1 时以 SHA1 作次级唯一键参与聚合（SHA1=40位、SHA256=64位，长度不同不冲突）。
- 每条主数据含两层：
  1. `meta_unified` — 择优汇总字段（用于列表 / 筛选 / SEO）
  2. `sources_raw` — 三站各自独立原始快照，一站一条，原样完整保存
- **择优**：标题=山己几子木 · 生命周期+KB=系统库 · 哈希+大小=HelloWindows
- **禁止覆盖、禁止合并**三站原始数据；未刷新到的源保留旧快照不删。
- 不做任何安全评级 / 可信度标签。

## 🏷 域名配置（重要，自适应）

本项目**不固定域名**（不与某个网址绑定）：

- **爬虫 sitemap / robots**：环境变量 `SITE_URL` 提供绝对域名；未配置自动用**相对路径**。
- **前端页面**：运行时自动取当前访问域名（`window.location.origin`）。
- **百度推送**：site 由环境变量 `BAIDU_SITE` 提供。

### 🔁 换域名：只需改一个 Secret

在 CI 工作流（`.github/workflows/crawl.yml`）中，**`SITE_URL` 与 `BAIDU_SITE` 都取自同一个 GitHub Secret `BAIDU_SITE`**（如 `https://517757.xyz`）：

```yaml
SITE_URL:   ${{ secrets.BAIDU_SITE }}
BAIDU_SITE: ${{ secrets.BAIDU_SITE }}
```

因此**换域名时，只需在仓库 Settings → Secrets → Actions 里把 `BAIDU_SITE` 改成新的完整地址**（如 `https://新域名.com`），代码零改动，sitemap / robots / 百度推送会全部自动跟随新域名。

> 注意：`517757.xyz` **没有写死在代码里**。仓库里出现的 `517757.xyz` 只存在于两处构建/运行时产物，非配置来源：
> - `frontend/public/robots.txt`、`frontend/public/sitemap.xml` —— 上次生成时的静态快照，换域名后下次 `crawl.yml` 运行会自动用新域名重新生成；
> - `crawler/baidu_push.py` 的错误提示文案里的示例（"如 `https://517757.xyz`"），不影响逻辑。

**换域名后建议**：将 `data/.baidu_push_state.json` 重置为空 `{"pushed":{}}`（或删除），因为它记录的是旧域名的 URL，避免旧记录囤积；新域名 URL 会被视为首次全量重新推送。

## 🚀 部署

### 方式一：Cloudflare Pages（推荐，根路径域名）

在 Cloudflare Dashboard → Workers & Pages → 创建项目 → 连接 GitHub 仓库 `sdlw7757/SCMirror`。
**务必按下面配置**（`package.json` 在 `frontend/` 子目录，Root 目录不设会导致 `npm ci` 找不到 lock 而构建失败）：

| 配置项 | 值 |
| --- | --- |
| **Production branch** | `main` |
| **Root directory**（构建根目录） | `frontend` |
| **Build command** | `npm ci && npm run build` |
| **Build output directory** | `dist` |

- 仓库删除重建后，需在 Cloudflare 里**重新连接新仓库**（或删除旧 Pages 项目重建），否则构建会失败/404。
- 推送仓库到 `main` 即自动触发构建；每日自动同步（GitHub Actions 提交新数据）同样会触发重新构建。
- Cloudflare 分配 `*.pages.dev` 为根路径部署，用默认 `/` base 构建即可（**不要**设置 `VITE_BASE`）。

### 方式二：GitHub Pages（默认子路径 `<user>.github.io/<repo>/`）

1. 仓库 **Settings → Pages → Source 选「GitHub Actions」**（不要把仓库根当站点，否则只会渲染 README）。
2. 提交工作流 `.github/workflows/pages.yml` 已随仓库提供，推送 `main` 自动构建并发布 `frontend/dist`。
3. 子路径部署由工作流自动注入 `VITE_BASE=/<repo>/` 与 `SITE_URL`，代码零改动。
4. 绑定自定义域名到根路径后，仅需把工作流里 `VITE_BASE` 改为 `/`。

## 🔗 百度收录

接口：`http://data.zz.baidu.com/urls?site=<site>&token=<token>`

在仓库 Secrets 配置 `BAIDU_SITE`（你的实际完整域名，如 `https://517757.xyz`）与 `BAIDU_TOKEN`。也可在本地通过环境变量直接触发。

推送策略（`crawler/baidu_push.py`）：
- **核心导航页每次必推且优先**：主页 `/`、`/tool-hash`（哈希工具）、`/wiki`（知识库）、全部系统分类页（win11/win10/win8/win7/winxp/server/office）单独优先批次发送，即使详情页因每日配额（`over quota`）失败，核心页也已成功提交。
- **详情页增量**：本轮新增或内容变化（lastmod 变化）时补推。
- 推送 base **优先取 `BAIDU_SITE`**（必须与百度注册站点域名一致，否则百度归属校验不过而不记录），状态文件 `data/.baidu_push_state.json` 记录已推送 URL 与其 lastmod，避免重复消耗额度。
- 失败原因（含 `over quota`）会写入 `data/.baidu_push_error.json` 由 CI 自动提交，方便排查。

## 📄 License

本项目采用 **MIT License**，详见 [LICENSE](LICENSE) 文件。

**重要声明**：本项目仅聚合整理网络公开的元信息与下载链接，**不存储任何镜像文件**。软件版权归微软所有，请使用正版。本项目仅供学习参考，不对文件安全性与完整性负责。

---

<div align="center">

Made with ❤️ · [海云镜像 · SeaCloud Mirror](https://github.com/sdlw7757/SCMirror)

</div>
