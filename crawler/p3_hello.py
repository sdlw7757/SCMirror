# -*- coding: utf-8 -*-
"""
p3_hello.py — 数据源：HelloWindows (hellowindows.cn)

数据来源（已实测）：
首页 `hello.html` 内嵌一段 Vue 脚本，其中 `data.items` 为分类数组:
    items = [ { category: "Windows11 LTSC", list: [ {...}, ... ] }, ... ]
每个镜像对象字段：
    id / title / links[ {name,url} ] / info / bit / type / activation / date
其中 `info` 为多行文本：
    文件：zh-cn_....iso
    大小：7.98GB
    日期：2026-03-17
    MD5：...
    SHA1：...
    SHA256：...     （新版提供）
下载链接为 https://hellowindows.cn/link?target=... 跳转。

输出：data/raw/hello.json（items[] 含 sha256/sha1/size/links 等）
"""
from __future__ import annotations

import io
import json
import re
import sys

from . import common

HOME = common.SOURCES["hello"]["home"]


def _balance_array(html: str, start: int) -> str | None:
    """从 start('[',排除字符串引号) 扫描到配对的 ']'，返回原始子串。"""
    depth = 0
    in_str = None
    esc = False
    i = start
    while i < len(html):
        ch = html[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
        else:
            if ch in ("\"", "'"):
                in_str = ch
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    return html[start : i + 1]
        i += 1
    return None


def extract_items_array(html: str) -> list | None:
    """
    从内嵌 Vue 脚本中提取 `items: [ ... ]` 数组（平衡括号扫描）。
    页面中存在多个 `items:`，逐个尝试，返回“包含 list 项最多”的完整数据数组，
    以确保返回覆盖 Windows 11 / Windows 10 等全部分类的数据集。
    """
    best = None
    best_score = -1
    cursor = 0
    while True:
        idx = html.find("items:", cursor)
        if idx < 0:
            break
        start = html.find("[", idx)
        if start >= 0:
            raw = _balance_array(html, start)
            if raw:
                try:
                    arr = json.loads(raw)
                except Exception:
                    arr = None
                if isinstance(arr, list) and any(
                    isinstance(x, dict) and (("category" in x) or ("list" in x)) for x in arr
                ):
                    score = 0
                    for x in arr:
                        if isinstance(x, dict):
                            score += len(x.get("list") or 0)
                    if score > best_score:
                        best = arr
                        best_score = score
        cursor = idx + 6
    return best


def parse_info(info: str) -> dict:
    """按“最长键优先 + 每行只归属一个键”解析 info 段落，避免前缀冲突
    （如“文件”误吞“文件大小”导致 filename 被覆盖成大小值）。"""
    # 按长度降序，确保更长更精确的键先匹配；匹配后对当前行 break，只归一个键
    KEYS = ["文件大小", "发布时间", "内置版本", "提取码", "文件", "大小", "版本", "日期", "MD5", "SHA1", "SHA256"]
    fields = {}
    for line in (info or "").splitlines():
        s = line.strip()
        for key in KEYS:
            tail = s[len(key):].lstrip()
            if s.startswith(key) and tail.startswith(("：", ":")):
                val = tail.lstrip("：:").strip()
                fields[key] = val
                break
    return fields


def detect_category(cat_text: str) -> str:
    # 去除空格，兼容 “Windows11 version 26H1” / “Windows10 LTSC/B” 等拼接形式
    t = cat_text.lower().replace(" ", "")
    rules = [
        (["win11", "windows11"], "win11"),
        (["win10", "windows10"], "win10"),
        (["win8.1", "windows8.1", "win8", "windows8"], "win8"),
        (["win7", "windows7"], "win7"),
        (["winxp", "windowsxp"], "winxp"),
        (["server"], "server"),
    ]
    for keys, cat in rules:
        if any(k in t for k in keys):
            return cat
    return "other"


def crawl() -> dict:
    warnings = []
    html, err = common.http_get_text(HOME, timeout=45, retries=3)
    if not html or err:
        warnings.append(f"首页抓取失败: {err}")
        return {"source": "hello", "crawled_at": common.now_str(), "items": [], "warnings": warnings}

    items_outer = extract_items_array(html)
    if items_outer is None:
        warnings.append("未找到 items 数据（页面结构可能变化）")
        return {"source": "hello", "crawled_at": common.now_str(), "items": [], "warnings": warnings}

    items = []
    for grp in items_outer:
        if not isinstance(grp, dict):
            continue
        category = (grp.get("category") or "").strip()
        cat = detect_category(category)
        for it in grp.get("list") or []:
            if not isinstance(it, dict):
                continue
            title = (it.get("title") or "").strip()
            info_fields = parse_info(it.get("info") or "")
            links = it.get("links") or []
            url = links[0].get("url") if links else ""
            rec = {
                "title": title,
                "filename": info_fields.get("文件", ""),
                "size": info_fields.get("大小") or info_fields.get("文件大小", ""),
                "version": info_fields.get("版本", ""),
                "date": info_fields.get("日期") or info_fields.get("发布时间", ""),
                "md5": common.norm_hash(info_fields.get("MD5")),
                "sha1": common.norm_hash(info_fields.get("SHA1")),
                "sha256": common.norm_hash(info_fields.get("SHA256")),
                "bit": (it.get("bit") or "").strip(),
                "type": (it.get("type") or "").strip(),
                "activation": (it.get("activation") or "").strip(),
                "category_key": cat,
                "category_text": category,
                "arch": common.normalize_arch(it.get("bit") or info_fields.get("文件", "")),
                "links": links,
                "url": url,
                "raw_id": it.get("id", ""),
            }
            itype = ""
            if "商业" in (it.get("type") or "") or "business" in (it.get("type") or "").lower():
                itype = "business"
            elif "零售" in (it.get("type") or "") or "零售" in (it.get("activation") or ""):
                itype = "consumer"
            rec["type"] = itype
            items.append(rec)

    return {
        "source": "hello",
        "crawled_at": common.now_str(),
        "items": items,
        "warnings": warnings,
    }


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    snap = crawl()
    print(json.dumps(snap, ensure_ascii=False, indent=2)[:6000])
    print(f"\n... 共 {len(snap['items'])} 条")
    from collections import Counter
    print(Counter(it["category_key"] for it in snap["items"]))
