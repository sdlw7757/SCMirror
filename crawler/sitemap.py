# -*- coding: utf-8 -*-
"""
sitemap.py —— 生成 sitemap.xml 与 robots.txt（写入 frontend/public/ 以随静态站部署）

sitemap 必须包含：镜像详情页 /detail/<iso_key> 以及全部系统分类页 /category/<key>，
同时包含首页与工具/知识库等。
robots.txt 声明允许抓取并指向 sitemap。
"""
from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET

from . import common


def _sitemap_dir() -> str:
    # 仓库根 / frontend / public
    here = os.path.dirname(os.path.abspath(__file__))          # crawler/
    root = os.path.dirname(here)                                # 仓库根
    return os.path.join(root, "frontend", "public")


def _encode(text: str) -> str:
    # 显式 ASCII 白名单：\w 在 str 模式下会匹配中文/Unicode，不能真正“净化”URL 字符
    return re.sub(r"[^A-Za-z0-9\-. /:?=&%+#]", "", str(text)) or "-"


def build_urls(items: list[dict], categories: list[dict]) -> list[dict]:
    """生成 sitemap URL 列表。loc 前缀：配置了 SITE_URL 则用绝对地址，否则用相对路径（域名自适应）。"""
    urls = []
    base = common.SITE_URL  # 可能为 ""（未配置域名）

    def add(path, lastmod="", changefreq="weekly", priority="0.8"):
        urls.append({
            "loc": f"{base}{path}" if base else path,
            "lastmod": lastmod or common.today_str(),
            "changefreq": changefreq,
            "priority": priority,
        })

    add("/", common.today_str(), "daily", "1.0")
    add("/tool-hash", common.today_str(), "monthly", "0.6")
    add("/wiki", common.today_str(), "monthly", "0.6")

    for cat in categories:
        add(f"/category/{_encode(cat['key'])}", common.today_str(), "daily", "0.9")

    for it in items:
        lastmod = it.get("last_seen") or common.today_str()
        add(f"/detail/{_encode(it.get('iso_key',''))}", lastmod, "daily", "0.9")

    return urls


def build_sitemap_xml(urls: list[dict]) -> str:
    urlset = ET.Element("urlset")
    urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
    for u in urls:
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = u["loc"]
        if u.get("lastmod"):
            ET.SubElement(url, "lastmod").text = u["lastmod"]
        ET.SubElement(url, "changefreq").text = u["changefreq"]
        ET.SubElement(url, "priority").text = u["priority"]
    return ET.tostring(urlset, encoding="unicode", xml_declaration=True)


def build_robots_txt() -> str:
    base = common.SITE_URL
    sitemap_line = f"Sitemap: {base}/sitemap.xml" if base else "Sitemap: /sitemap.xml"
    return (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"{sitemap_line}\n"
    )


def _atomic_write(path: str, text: str) -> None:
    """原子写文本：先写临时文件再 os.replace，避免中途被杀留下截断文件。"""
    import tempfile
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", suffix=".txt", dir=d or ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.remove(tmp)
        except Exception:
            pass
        raise


def write_sitemap(items: list[dict], categories: list[dict]) -> dict:
    out_dir = _sitemap_dir()
    os.makedirs(out_dir, exist_ok=True)
    urls = build_urls(items, categories)
    sitemap_path = os.path.join(out_dir, "sitemap.xml")
    robots_path = os.path.join(out_dir, "robots.txt")

    _atomic_write(sitemap_path, build_sitemap_xml(urls))
    _atomic_write(robots_path, build_robots_txt())

    return {
        "sitemap": sitemap_path,
        "robots": robots_path,
        "url_count": len(urls),
    }


if __name__ == "__main__":
    import sys, io, json
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    db = common.read_json(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "iso_data.json"))
    if db:
        res = write_sitemap(db.get("items", []), db.get("categories", []))
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("data/iso_data.json 不存在")
