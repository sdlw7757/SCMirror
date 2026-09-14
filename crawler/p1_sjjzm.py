# -*- coding: utf-8 -*-
"""
p1_sjjzm.py — 数据源：山己几子木 (msdn.sjjzm.com)

站点结构（已实测）：
- 首页列出分类导航：win11.html / win10.html / win81.html / win8.html / win7.html / winxp.html / office.html
- 每个系统分类页面内嵌多个 `<div class="box">`，一个 box 即一条镜像，内含：
    - `.name h1`       标题（含 版本 / 架构 / 版本类型）
    - `.tag span`      标记（架构 / 语言 / 日期 / 内置版本）
    - `table.param`    文件名 / SHA-256 / SHA-1 / MD5 / 文件大小
    - `.download .item` 各网盘下载地址（阿里云盘、微云、百度网盘、天翼云盘…）
- 若分类页本身无 box，则回退抓取其版本子页（/win11/24h2.html 等）。

输出：data/raw/sjjzm.json，包含 items[]（每条含 title/sha256/sha1/size/links 等）
"""
from __future__ import annotations

import io
import re
import sys

from bs4 import BeautifulSoup

from . import common


def _decode(soup_text: str) -> str:
    return str(soup_text).strip()


def fetch_edition_links() -> list[dict]:
    """从首页解析六类 Windows 分类页链接。"""
    html, err = common.http_get_text(common.SOURCES["sjjzm"]["home"])
    out = []
    if not html:
        return out, err
    soup = BeautifulSoup(html, "html.parser")
    # 左侧导航 <a href="...winXX.html">（含 office.html → Office 大分类）
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        m = re.search(r"/(win\d+|winxp|office)\.html$", href)
        if not m:
            continue
        key = m.group(1)
        cat = {
            "win11": "win11", "win10": "win10", "win81": "win8",
            "win8": "win8", "win7": "win7", "winxp": "winxp",
            "office": "office",
        }.get(key)
        text = (a.get_text() or "").strip()
        if cat and not any(x["cat"] == cat for x in out):
            out.append({"cat": cat, "page": key, "url": href, "text": text})
    return out, None


def extract_boxes(html: str) -> list[dict]:
    """从一个分类页中解析所有 box 镜像块。"""
    soup = BeautifulSoup(html, "html.parser")
    boxes = soup.select("div.box")
    results = []
    for b in boxes:
        rec = _parse_box(b)
        if rec:
            results.append(rec)
    return results


def _parse_box(box) -> dict | None:
    name_el = box.select_one("div.name h1")
    if not name_el:
        return None
    title = _decode(name_el.get_text())
    if not title:
        return None

    # tag 位：架构 / 语言 / 日期 / 内置版本
    tags = [_decode(s.get_text()) for s in box.select("div.tag span")]
    tags = [t for t in tags if t]

    # param 表
    params = {}
    for tr in box.select("table.param tr"):
        tds = tr.select("td")
        if len(tds) == 2:
            k = _decode(tds[0].get_text())
            v = _decode(tds[1].get_text())
            params[k] = v

    # download items
    links = []
    for item in box.select("div.download div.item"):
        label = item.select_one("div.label")
        inp = item.select_one("input.input") or item.select_one("input")
        if not label or not inp:
            continue
        name = _decode(label.get_text())
        val = (inp.get("value") or "").strip()
        if name and val:
            # 保留密码/提取码项（天翼/百度/移动云盘等），用 isPwd 标记，前端单独展示
            links.append({"name": name, "url": val, "isPwd": ("密码" in name or "提取码" in name)})

    filename = params.get("文件名") or ""
    sha256 = common.norm_hash(params.get("SHA-256"))
    sha1 = common.norm_hash(params.get("SHA-1"))
    md5 = common.norm_hash(params.get("MD5"))
    size = params.get("文件大小") or ""
    date = next((t for t in tags if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t)), "")

    itype = ""
    if "消费者" in title or "consumer" in title.lower():
        itype = "consumer"
    elif "商业" in title or "business" in title.lower():
        itype = "business"

    # 版本：优先标题，其次从 tags 找（部分标题不含版本号，版本在 tag 里）
    version = ""
    vm = re.search(r"\b(2[0-9]H[12]|first|other)\b", title, re.I)
    if vm:
        version = vm.group(1).upper()
    else:
        for t in tags:
            m = re.search(r"\b(2[0-9]H[12]|first|other)\b", t, re.I)
            if m:
                version = m.group(1).upper()
                break

    # 架构：标题优先，其次 tags（MSDN 标题常不含架构，架构在 tag 里）
    arch = common.normalize_arch(title) or common.normalize_arch(" ".join(tags))

    # 主下载地址：跳过密码/提取码项；优先磁力/ED2K，否则回退首个 http 链接
    primary = ""
    for L in links:
        if L.get("isPwd"):
            continue
        u = L["url"]
        if u.startswith(("magnet:", "ed2k://")):
            primary = u
            break
    if not primary:
        for L in links:
            if L.get("isPwd"):
                continue
            u = L["url"]
            if u.lower().startswith(("http://", "https://")):
                primary = u
                break

    return {
        "title": title,
        "tags": tags,
        "filename": filename,
        "sha256": sha256,
        "sha1": sha1,
        "md5": md5,
        "size": size,
        "version": version,
        "arch": arch,
        "type": itype,
        "date": date,
        "links": links,
        "url": primary,
        "editions": [t for t in tags if t and not t.endswith("位") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", t)],
    }


def fetch_version_subpages(page: str) -> list[str]:
    """分类页无 box 时，抓取 /winXX/*.html 版本子页。"""
    parent = f"https://msdn.sjjzm.com/{page}.html"
    html, err = common.http_get_text(parent)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    subs = []
    for a in soup.select("div.menu ul li a[href]"):
        href = (a.get("href") or "").strip()
        if re.search(r"/" + re.escape(page) + r"/[a-z0-9]+\.html$", href, re.I):
            subs.append(href)
    # 去重保序
    seen = set()
    uniq = []
    for u in subs:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def crawl() -> dict:
    """
    聚合抓取山己几子木三站数据。返回:
    {
      "source": "sjjzm",
      "crawled_at": "YYYY-MM-DD HH:MM:SS",
      "items": [ {...}, ... ],
      "warnings": [...],
    }
    """
    items = []
    warnings = []

    links, err = fetch_edition_links()
    if err:
        warnings.append(f"首页解析失败: {err}")
        return _snapshot([], warnings)

    for entry in links:
        page_html, e1 = common.http_get_text(entry["url"])
        if not page_html:
            warnings.append(f"抓取失败 {entry['url']}: {e1}")
            continue
        boxes = extract_boxes(page_html)
        # office 分类页只内嵌最新版本(2024)的 box，其余版本(2021/2019)在版本子页 → 始终抓子页
        if not boxes or entry["cat"] == "office":
            # 回退/补全：抓版本子页
            for sub in fetch_version_subpages(entry["page"]):
                sub_html, e2 = common.http_get_text(sub)
                if not sub_html:
                    warnings.append(f"子页失败 {sub}: {e2}")
                    continue
                for b in extract_boxes(sub_html):
                    b["category_key"] = entry["cat"]
                    items.append(b)
            # 尝试从菜单识别版本
        for b in boxes:
            b["category_key"] = entry["cat"]
            items.append(b)

        # 从页面菜单补充版本号（针对无 version 的）
        soup = BeautifulSoup(page_html, "html.parser")
        for li in soup.select("div.menu ul li"):
            a = li.select_one("a[href]")
            if not a:
                continue
            li_version = re.search(r"\b(2[0-9]H[12]|first|other)\b", _decode(a.get_text()), re.I)
            active = "active" in (li.get("class") or [])
            if li_version and not active:
                pass  # 版本已在标题中，此处仅作兜底

    return _snapshot(items, warnings)


def _snapshot(items, warnings) -> dict:
    return {
        "source": "sjjzm",
        "crawled_at": common.now_str(),
        "items": items,
        "warnings": warnings,
    }


if __name__ == "__main__":
    import json as _json
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    snap = crawl()
    print(_json.dumps(snap, ensure_ascii=False, indent=2)[:8000])
    print(f"\n... 共 {len(snap['items'])} 条")
