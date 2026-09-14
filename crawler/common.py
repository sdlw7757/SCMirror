# -*- coding: utf-8 -*-
"""
common.py — 海云镜像 爬虫系统共享模块
集中存放站点常量、数据源配置、分类体系、HTTP 请求、时间与哈希工具。

原则：
- 以 SHA256 为全局唯一主键；当某数据源仅提供 SHA1 时，SHA1 作为次级唯一键参与聚合
（SHA1 为 40 位十六进制、SHA256 为 64 位十六进制，长度不同不会冲突）。
- 不输出任何安全评级 / 可信度标签。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone

# ---------------- 站点基础信息 ----------------
SITE_NAME = "海云镜像"
SITE_NAME_EN = "SeaCloud Mirror"
# 域名不写死：部署后通过环境变量 SITE_URL 提供给（爬虫/CI）即可，随时可更换。
# 未设置时为空 → sitemap / robots 使用相对路径，前端运行时用当前访问域名自适应。
SITE_URL = (os.environ.get("SITE_URL", "") or "").strip().rstrip("/")
GITHUB_REPO = "https://github.com/sdlw7757/SCMirror"
GITHUB_REPO_EN = "https://github.com/sdlw7757/SCMirror"

# 简短免责声明（仅展示于页脚）
DISCLAIMER = (
    "【免责声明】本站仅聚合整理网络公开元信息与下载链接，不存储镜像文件。"
    "软件版权归微软所有，请使用正版。本站仅供学习参考，不对文件安全与完整性负责。"
)

# ---------------- 数据源配置 ----------------
# 固定三站：山己几子木 / 系统库 / HelloWindows
SOURCES = {
    "sjjzm": {
        "key": "sjjzm",
        "name": "山己几子木",
        "en": "SJJZM MSDN",
        "home": "https://msdn.sjjzm.com/",
        "prefer": {"title": 1, "edition": 1, "version": 1},   # 标题/版本优先取此站
    },
    "xitongku": {
        "key": "xitongku",
        "name": "系统库",
        "en": "XitongKu",
        "home": "https://www.xitongku.com/",
        "prefer": {"kb": 1, "lifecycle": 1},                  # 生命周期+KB 优先取此站
    },
    "hello": {
        "key": "hello",
        "name": "HelloWindows",
        "en": "HelloWindows",
        "home": "https://hellowindows.cn/",
        "prefer": {"sha256": 1, "size": 1},                   # 哈希+大小 优先取此站
    },
}

# 择优顺序（数值越小优先级越高），与“数据规则”一一对应
TITLE_PRIORITY = ["sjjzm", "xitongku", "hello"]
LIFECYCLE_KB_PRIORITY = ["xitongku", "hello", "sjjzm"]
HASH_SIZE_PRIORITY = ["hello", "sjjzm", "xitongku"]

# ---------------- 分类体系 ----------------
# 分类 key 固定；intro 用于分类页顶部简短介绍；keywords 用于 SEO。
CATEGORIES = [
    {
        "key": "win11",
        "name": "Windows 11",
        "short": "Win11",
        "intro": (
            "Windows 11 是微软最新的桌面操作系统，采用全新 Fluent 设计与圆角视觉，"
            "原生支持 Android 应用（部分版本）、更安全的 VBS 与 TPM 2.0 要求。"
            "本站收录 Windows 11 各版本官方原版镜像（21H2~26H1），分为消费者版与商业版。"
        ),
        "keywords": "Windows 11 镜像下载,Win11 原版,Windows 11 ISO,Win11 消费者版,Win11 商业版",
    },
    {
        "key": "win10",
        "name": "Windows 10",
        "short": "Win10",
        "intro": (
            "Windows 10 是微软长期支持的经典桌面系统（2015 年发布），广泛兼容老硬件。"
            "本站收录 Windows 10 各版本官方原版镜像（1507~22H2），同样区分零售/批量版本。"
        ),
        "keywords": "Windows 10 镜像下载,Win10 原版,Windows 10 ISO,Win10 下载",
    },
    {
        "key": "win8",
        "name": "Windows 8 / 8.1",
        "short": "Win8",
        "intro": (
            "Windows 8 / 8.1 引入现代磁贴界面与更快的启动体验，Windows 8.1 是补充更新版，"
            "对传统桌面用户更友好。本站收录其官方原版镜像。"
        ),
        "keywords": "Windows 8 镜像,Windows 8.1 下载,Win8 ISO,Win8.1 原版",
    },
    {
        "key": "win7",
        "name": "Windows 7",
        "short": "Win7",
        "intro": (
            "Windows 7 是广受好评的经典桌面系统（2009 年发布），现已停止官方支持，"
            "仍在老硬件用户中广泛使用。本站收录其官方原版镜像，供研究参考。"
        ),
        "keywords": "Windows 7 镜像下载,Win7 原版,Windows 7 ISO,Win7 旗舰版,Windows 7 下载",
    },
    {
        "key": "winxp",
        "name": "Windows XP",
        "short": "WinXP",
        "intro": (
            "Windows XP 是微软历史上最经典的桌面系统之一，已完全停止支持。"
            "本站收录其官方原版镜像，仅供收藏与研究参考。"
        ),
        "keywords": "Windows XP 镜像,Win XP 原版,Windows XP ISO",
    },
    {
        "key": "server",
        "name": "Windows Server",
        "short": "Server",
        "intro": (
            "Windows Server 是面向服务器与企业场景的操作系统，涵盖 2008~2025 各版本。"
            "本站收录其官方原版镜像（含 LTSC/数据中心/标准版等）。"
        ),
        "keywords": "Windows Server 下载,Server 2025 镜像,Server 2022 ISO,Windows Server 原版",
    },
    {
        "key": "office",
        "name": "Office",
        "short": "Office",
        "intro": (
            "聚合整理各版本 Microsoft Office 官方原版镜像"
            "（Office 2003 ~ 2024，含专业版 / 专业增强版 / Mac 版等），来自山己几子木 / 系统库 / HelloWindows。"
        ),
        "keywords": "Office 2024,Office 2019,Office 2016,Office 2013,Office 2010,Office 2007,Office 2003",
    },
]

CATEGORY_KEYS = [c["key"] for c in CATEGORIES]
CATEGORY_BY_KEY = {c["key"]: c for c in CATEGORIES}
CATEGORY_BY_NAME = {c["name"].lower(): c["key"] for c in CATEGORIES}

# 分类检测规则：文本命中即归入对应 category。
CATEGORY_RULES = [
    (["win11", "windows 11", "windows11"], "win11"),
    (["win10", "windows 10", "windows10"], "win10"),
    (["win8", "windows 8.1", "windows 81", "windows 8"], "win8"),
    (["win7", "windows 7", "windows7"], "win7"),
    (["winxp", "windows xp", "windowsxp"], "winxp"),
    (["server"], "server"),
    (["office", "microsoft office"], "office"),
]


# ---------------- 时间工具 ----------------
BEIJING_TZ = timezone(timedelta(hours=8))


def now_beijing() -> datetime:
    """返回当前北京时间（UTC+8）。"""
    return datetime.now(BEIJING_TZ)


def now_str() -> str:
    """完整时间字符串，例如 2026-01-15 02:00:00。"""
    return now_beijing().strftime("%Y-%m-%d %H:%M:%S")


def today_str() -> str:
    return now_beijing().strftime("%Y-%m-%d")


def yesterday_str() -> str:
    return (now_beijing() - timedelta(days=1)).strftime("%Y-%m-%d")


# ---------------- HTTP 工具 ----------------
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 "
        "SeaCloudMirror/1.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def http_get_text(
    url: str,
    timeout: int = 30,
    retries: int = 3,
    headers: dict | None = None,
    encoding: str | None = None,
    as_json: bool = False,
) -> tuple[str | dict | None, str | None]:
    """
    抓取文本内容（带重试）。返回 (content_or_json, error)。
    encoding 指定时按该编码解码；否则尝试 utf-8 / gbk 自动回退。
    """
    import random
    import requests
    # 礼貌限速：每次请求前随机小间隔，避免高频抓取触发目标站限流
    time.sleep(random.uniform(0.15, 0.4))
    err = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                url,
                headers=headers or DEFAULT_HEADERS,
                timeout=timeout,
                verify=True,
            )
            # 4xx（404/403 等）说明请求本身有问题，重试无意义，直接返回
            if 400 <= resp.status_code < 500:
                return None, f"HTTP {resp.status_code}: {url}"
            resp.raise_for_status()
            raw = resp.content
            if as_json:
                # 优先用响应声明的编码 / 显式指定编码
                enc = encoding or resp.encoding or "utf-8"
                try:
                    return json.loads(raw.decode(enc)), None
                except Exception:
                    # 常见 UTF-8 BOM / GBK 回退
                    for e in ("utf-8-sig", "utf-8", "gbk"):
                        try:
                            return json.loads(raw.decode(e)), None
                        except Exception:
                            continue
                    return None, f"JSON 解析失败: {url}"
            if encoding:
                text = raw.decode(encoding, errors="replace")
            else:
                for e in ("utf-8", "gbk"):
                    try:
                        text = raw.decode(e)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    text = raw.decode("utf-8", errors="replace")
            return text, None
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}: {e}"
            if attempt < retries:
                time.sleep(1.2 * attempt)
    return None, err


# ---------------- JSON 读写 ----------------
def write_json(path: str, obj) -> None:
    """原子写 JSON：先写临时文件再 os.replace，避免中途被杀留下损坏/截断文件。"""
    import tempfile
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=d or ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            # 紧凑输出（无缩进）：iso_data.json 约 3.1MB→2.2MB，前端下载+解析更快
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, path)
    except Exception:
        try:
            os.remove(tmp)
        except Exception:
            pass
        raise


def read_json(path: str, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except Exception:
        return default


# ---------------- 文本/哈希工具 ----------------
def norm_hash(value: str | None) -> str:
    """规范哈希：去空格、去前缀 col16/col20、转小写、仅保留十六进制字符。"""
    if not value:
        return ""
    s = str(value).strip().lower()
    # 形如 64 位十六进制前的 '0x' / 'hex:' 前缀可忽略
    s = re.sub(r"^(0x|hex:)", "", s)
    s = re.sub(r"[^0-9a-f]", "", s)
    return s


def is_valid_sha256(v) -> bool:
    """是否 64 位合法 SHA-256。"""
    return bool(v) and len(v) == 64


def is_valid_sha1(v) -> bool:
    """是否 40 位合法 SHA-1。"""
    return bool(v) and len(v) == 40


def pick_key(item: dict) -> tuple[str, str]:
    """
    依据“以 SHA256 为全局唯一主键”计算唯一键。
    返回 (key, algorithm)。优先 sha256，缺失时回退 sha1。
    """
    sha256 = norm_hash(item.get("sha256"))
    sha1 = norm_hash(item.get("sha1"))
    if is_valid_sha256(sha256):
        return sha256, "sha256"
    if is_valid_sha1(sha1):
        return sha1, "sha1"
    return "", ""


def slugify(text: str, max_len: int = 40) -> str:
    """生成 URL 友好短串（字母数字与连字符）。"""
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:max_len]


def parse_kb(text: str | None) -> str:
    """从文本中提取 KB 编号，例如 KB5124012。"""
    if not text:
        return ""
    m = re.search(r"KB\d{4,9}", text, re.I)
    return m.group(0).upper() if m else ""


# ---------------- 尺寸/架构工具 ----------------
def normalize_arch(text: str | None) -> str:
    """把“64位”等归一为 x64 / x86 / arm64。"""
    if not text:
        return ""
    t = text.lower()
    if "arm" in t:
        return "arm64"
    if "64" in t or "amd64" in t:
        return "x64"
    if "32" in t or "86" in t:
        return "x86"
    return ""


def sha256_text(text: str) -> str:
    """求某字符串的 SHA256（用于无主键记录时的备用聚合标识，仅供内部）。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
