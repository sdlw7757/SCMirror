# -*- coding: utf-8 -*-
"""
p2_xitongku.py — 数据源：系统库 (www.xitongku.com)

数据来源（已实测）：
1. https://www.xitongku.com/data/windows.json   —— 全量版本树（UTF-8 BOM）。叶子节点即一条镜像：
   - name          架构（64位 / ARM …）
   - description   多行文本：文件名称 / 版本号 / 文件大小 / 发布时间 / 内置版本 / MD5 / SHA1
   - keywords      JSON 字符串：各下载链接（磁力下载 / 迅雷网盘 / 百度网盘 / 夸克网盘 …）
   - 父级链        Win11 / 26H1 / 消费者版|商业版 / 2026.08 / 64位
2. https://xtk-api.hipcapi.com/index/windowVersion/list —— 生命周期 + KB 补丁信息。

输出：data/raw/xitongku.json（items[] 含 filename/sha1/sha256/size/links/kb/lifecycle 等）
注：系统库叶子仅提供 SHA1（无 SHA256），聚合时以 SHA1 为次级唯一键。
"""
from __future__ import annotations

import io
import json
import re
import sys
from datetime import datetime

from . import common

WINDOWS_JSON_URL = "https://www.xitongku.com/data/windows.json"
OFFICE_JSON_URL = "https://www.xitongku.com/data/office.json"
LIFECYCLE_API_URL = "https://xtk-api.hipcapi.com/index/windowVersion/list"

FAMILY_RULES = [
    ("win11", ["win11"], "Windows 11"),
    ("win10", ["win10"], "Windows 10"),
    ("win8", ["win8.1", "win8"], "Windows 8/8.1"),
    ("win7", ["win7"], "Windows 7"),
    ("winxp", ["winxp", "windows xp"], "Windows XP"),
    ("server", ["server"], "Windows Server"),
]


def detect_category(text: str) -> tuple[str, str]:
    """根据 family 名返回 (category_key, system_name)。"""
    t = text.lower()
    for cat, keys, sysname in FAMILY_RULES:
        if any(k in t for k in keys):
            return cat, sysname
    return "office", text


def walk_tree(nodes, parents=()) -> list[dict]:
    """DFS 遍历版本树，收集叶子镜像。"""
    items = []
    for n in nodes:
        kids = n.get("children") or []
        rec = _leaf_record(n)
        if rec:
            rec["_parents"] = [p["name"] for p in parents]
            items.append(rec)
        items.extend(walk_tree(kids, parents + (n,)))
    return items


def _leaf_record(n: dict) -> dict | None:
    name = (n.get("name") or "").strip()
    if not name:
        return None
    if n.get("children"):
        return None  # 仅收集叶子
    desc = n.get("description") or ""
    fields = {}
    for line in desc.splitlines():
        line = line.strip()
        for key in ("文件名称", "文件名", "版本号", "文件大小", "发布时间", "内置版本", "内含版本", "MD5", "SHA1", "SHA256"):
            if line.startswith(key) and ("：" in line or ":" in line):
                val = re.split(r"[：:]", line, 1)[1].strip()
                fields[key] = val
                break
    kws = {}
    kw_raw = (n.get("keywords") or "").strip()
    if kw_raw:
        try:
            parsed = json.loads(kw_raw)
            if isinstance(parsed, dict):
                kws = parsed
        except Exception:
            pass

    filename = fields.get("文件名") or fields.get("文件名称") or ""
    build = fields.get("版本号") or ""
    size = fields.get("文件大小") or ""
    date = fields.get("发布时间") or ""
    md5 = common.norm_hash(fields.get("MD5"))
    sha1 = common.norm_hash(fields.get("SHA1"))
    sha256 = common.norm_hash(fields.get("SHA256"))
    editions = fields.get("内置版本") or fields.get("内含版本") or ""

    links = []
    primary = ""
    # 过滤不要抓取的链接类型（U 盘装机/定制系统盘/购买U盘是线下服务项，不属于下载资源）
    SKIP_KW = ("定制装机U盘", "定制系统盘", "购买U盘")
    for rk, rv in kws.items():
        if not rv:
            continue
        if any(sk in rk for sk in SKIP_KW):
            continue
        links.append({"name": rk, "url": rv})
        if not primary and rv.startswith(("magnet:", "ed2k://")):
            primary = rv
    if not primary and links:
        primary = links[0]["url"]

    return {
        "name": name,
        "description": desc,
        "filename": filename,
        "build": build,
        "size": size,
        "md5": md5,
        "sha1": sha1,
        "sha256": sha256,
        "date": date,
        "editions": editions,
        "links": links,
        "url": primary,
        "raw_id": n.get("id"),
        "raw_node": n.get("name"),
    }


def attach_office_context(items: list[dict]) -> None:
    """Office 树（office.json）专用上下文：family=年份，归入 Office 大分类（key=office）。"""
    for it in items:
        parents = it.pop("_parents", [])
        names = [p for p in parents if p]
        version = names[0] if names else ""          # 年份：2024 / 2019 / 2016 …
        type_ctx = names[1] if len(names) > 1 else ""  # ProPlus / 专业版 / Mac版 …
        sub = names[2] if len(names) > 2 else ""
        arch = common.normalize_arch(it["name"]) or common.normalize_arch(" ".join(names[::-1]))
        itype = "mac" if "mac" in f"{type_ctx} {sub}".lower() else ""
        title = " ".join(x for x in (f"Office {version}", type_ctx, sub, it["name"]) if x).strip()
        it["title"] = title
        it["category_key"] = "office"
        it["version"] = version
        it["type"] = itype
        it["arch"] = arch
        it["month"] = ""


def attach_context(items: list[dict]) -> None:
    """根据父级链填充 title / category / version / type / arch / month。"""
    for it in items:
        parents = it.pop("_parents", [])
        names = [p for p in parents if p]
        family = names[0] if names else ""
        cat, sysname = detect_category(family)
        version = names[1] if len(names) > 1 else ""
        type_ctx = names[2] if len(names) > 2 else ""
        month = names[3] if len(names) > 3 else ""
        itype = ""
        if "消费者" in type_ctx or "consumer" in type_ctx.lower():
            itype = "consumer"
        elif "商业" in type_ctx or "business" in type_ctx.lower():
            itype = "business"
        arch = common.normalize_arch(it["name"]) or common.normalize_arch(
            next((p for p in names[::-1] if re.search(r"位|arm|x64|x86", p or "")), "")
        )

        title = (
            f"{sysname} {version} {type_ctx} {month} {it['name']}".replace("  ", " ").strip()
            if sysname
            else it["name"]
        )
        it["title"] = title
        it["category_key"] = cat
        it["version"] = version
        it["type"] = itype
        it["arch"] = arch
        it["month"] = month


def fetch_lifecycle() -> dict:
    """获取系统库生命周期+KB API，返回 { (sysname_lower, version_lower): entry }。"""
    data, err = common.http_get_text(LIFECYCLE_API_URL, timeout=30, retries=3, as_json=True)
    if not data or err:
        return {}
    entries = (data.get("data") or {}).get("list") or []
    out = {}
    for e in entries:
        name = (e.get("system_name") or "").lower()
        ver = (e.get("system_version") or "").lower()
        if name and ver:
            out[(name, ver)] = e
    return out


def build_lifecycle_record(entry: dict | None) -> dict:
    """由 API 条目生成 lifecycle/kb 字段。"""
    if not entry:
        return {}
    kb = common.parse_kb(entry.get("system_patch"))
    end_dates = [entry.get("system_end_date"), entry.get("system_other_end_date")]
    end_dates = [d for d in end_dates if d]
    support_end = max(end_dates) if end_dates else ""  # 展示用：取原字符串值
    # 状态判断用「解析成日期再比较」，避免字符串字典序（混格式时比较正确）
    parsed_ends = []
    for d in end_dates:
        for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d", "%Y-%m"):
            try:
                parsed_ends.append(datetime.strptime(d, fmt).date())
                break
            except ValueError:
                continue
    status = ""
    if parsed_ends:
        last = max(parsed_ends)
        status = "已停止支持" if common.now_beijing().date() > last else "支持中"
    return {
        "kb": kb,
        "support_end": support_end,
        "publish_date": entry.get("system_pulish_date", ""),
        "inner_version": entry.get("system_inner_version", ""),
        "lifecycle_state": "ended" if status == "已停止支持" else ("supported" if status else ""),
        "lifecycle": status,
        "patch_url": entry.get("system_patch_url", ""),
    }


def crawl() -> dict:
    warnings = []
    tree, err = common.http_get_text(WINDOWS_JSON_URL, timeout=60, retries=3, as_json=True)
    if not tree or err:
        warnings.append(f"版本树抓取失败: {err}")
        # 失败也返回与成功一致的快照结构，避免混入站点元信息污染 raw 快照
        return {"source": "xitongku", "crawled_at": common.now_str(), "items": [], "warnings": warnings}

    items = walk_tree(tree)
    attach_context(items)

    # Office 版本树（office.json）：结构与 windows.json 一致，归入 Office 大分类
    otree, oerr = common.http_get_text(OFFICE_JSON_URL, timeout=60, retries=3, as_json=True)
    if not otree or oerr:
        warnings.append(f"Office 树抓取失败: {oerr}")
    else:
        oitems = walk_tree(otree)
        attach_office_context(oitems)
        items.extend(oitems)

    life = fetch_lifecycle()
    # 为每条匹配 (system_name, version)
    for it in items:
        sysname_l = (
            next((fn for cat, keys, fn in FAMILY_RULES if it["category_key"] == cat), "").lower()
        )
        entry = life.get((sysname_l, it["version"].lower())) if sysname_l and it["version"] else None
        if not entry:
            entry = life.get((sysname_l, "")) if sysname_l else None
        rec = build_lifecycle_record(entry)
        it.update(rec)

    return {
        "source": "xitongku",
        "crawled_at": common.now_str(),
        "items": items,
        "warnings": warnings,
    }


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    snap = crawl()
    print(json.dumps(snap, ensure_ascii=False, indent=2)[:8000])
    print(f"\n... 共 {len(snap['items'])} 条")
    # 分类统计
    from collections import Counter
    print(Counter(it["category_key"] for it in snap["items"]))
