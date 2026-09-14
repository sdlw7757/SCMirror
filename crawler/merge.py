# -*- coding: utf-8 -*-
"""
merge.py —— 海云镜像 三站数据合并（累积式、以 SHA256 为全局唯一主键）

规则（严格遵守）：
1. 以 SHA256 为全局唯一主键；数据源仅提供 SHA1 时，SHA1 作为次级唯一键参与聚合
   （SHA1=40 位、SHA256=64 位十六进制，长度不同不会互相碰撞）。
2. 同一个唯一键聚合为一条主数据（item），其内部：
   - meta_unified：择优汇总（用于列表/筛选/SEO）
   - sources_raw：三站各自独立的原始快照，一站一条，完整原样保存。
3. 禁止覆盖、禁止合并三站原始数据 —— sources_raw 按 source 区分，永不合二为一；
   每次抓取只更新对应数据源自己的那条快照（刷新采集时间），不影响其他源。
4. 择优：
   - 标题        = 山己几子木 (sjjzm)
   - 生命周期+KB = 系统库   (xitongku)
   - 哈希+大小   = HelloWindows (hello)
5. 累积保留：首次出现的镜像记录 first_seen，之后记录 last_seen；本轮未出现的数据源
   旧快照保留不删，避免数据回退。
"""
from __future__ import annotations

import datetime
import re

from . import common


# --------------------------------------------------------------------------
# 数据源原始快照 → 单条独立 source entry
# --------------------------------------------------------------------------
def build_source_entry(src_key: str, rec: dict, crawled_at: str) -> dict:
    src = common.SOURCES[src_key]
    entry = {
        "source": src_key,
        "source_name": src["name"],
        "home": src["home"],
        "filename": rec.get("filename", "") or "",
        "hash": {
            "sha256": common.norm_hash(rec.get("sha256")),
            "sha1": common.norm_hash(rec.get("sha1")),
            "md5": common.norm_hash(rec.get("md5")),
        },
        "url": rec.get("url", "") or "",
        "urls": rec.get("links") or [],
        "size": rec.get("size", "") or "",
        "crawl_time": crawled_at,
        # 完整原样保存该数据源此轮抓取的原始记录
        "raw": _slim(rec),
    }
    return entry


def _source_fingerprint(entry: dict) -> tuple:
    """内容指纹：用于判断该源快照是否真正变化（决定 stats/百度增量是否虚高）。"""
    h = entry.get("hash") or {}
    urls = entry.get("urls") or []
    items = []
    for u in urls:
        if isinstance(u, dict):
            items.append((u.get("name") or "", u.get("url") or ""))
    return (
        entry.get("filename") or "",
        h.get("sha256") or "",
        h.get("sha1") or "",
        h.get("md5") or "",
        entry.get("size") or "",
        tuple(sorted(items)),
        entry.get("crawl_time") or "",
    )


def _slim(rec: dict) -> dict:
    """保留原始记录完整副本（原样保存）；剔除无意义的空键以减小体积。"""
    out = {k: v for k, v in rec.items() if v not in (None, "", [], {})}
    return out


def _candidate(entry: dict) -> dict:
    """从一份 source entry 的原始数据中提取可用于汇总的候选字段。"""
    raw = entry.get("raw") or {}
    return {
        "title": raw.get("title", ""),
        "version": raw.get("version", ""),
        "build": raw.get("build", ""),
        "arch": raw.get("arch", ""),
        "type": raw.get("type", ""),
        "size": raw.get("size", ""),
        "sha256": common.norm_hash(raw.get("sha256")),
        "date": raw.get("date", ""),
        "kb": raw.get("kb", ""),
        "lifecycle": raw.get("lifecycle", ""),
        "lifecycle_state": raw.get("lifecycle_state", ""),
        "support_end": raw.get("support_end", ""),
        "editions": raw.get("editions", ""),
        "category_key": raw.get("category_key", ""),
        "publish_date": raw.get("publish_date", ""),
    }


def _pick(entries: list[dict], priority: list[str], field: str) -> str:
    """按择优优先级返回第一个非空字段值。"""
    ordered = sorted(entries, key=lambda e: priority.index(e["source"]) if e["source"] in priority else 999)
    for e in ordered:
        val = _candidate(e).get(field, "")
        if val:
            return val
    return ""


# --------------------------------------------------------------------------
# 分类 / 显示字段工具
# --------------------------------------------------------------------------
def detect_category(rec_or_text: dict | str) -> str:
    """对原始记录或字符串做分类检测。rec 带 category_key 时优先使用。"""
    if isinstance(rec_or_text, dict):
        ck = rec_or_text.get("category_key") or ""
        if ck in common.CATEGORY_KEYS and ck != "other":
            return ck
        text = " ".join([
            str(rec_or_text.get("title", "")),
            str(rec_or_text.get("category_text", "")),
            str(rec_or_text.get("filename", "")),
        ])
    else:
        text = rec_or_text
    t = text.lower().replace(" ", "")
    for keys, cat in common.CATEGORY_RULES:
        if cat == "server" and "server" in t:
            return cat
        if any(k.replace(" ", "") in t for k in keys):
            return cat
    return "other"


def normalize_arch(rec: dict) -> str:
    arch = rec.get("arch", "") or ""
    if arch:
        return arch
    return common.normalize_arch(rec.get("filename", "") or rec.get("title", ""))


def _type_label(t: str) -> str:
    return {"consumer": "消费者版（零售）", "business": "商业版（批量）"}.get(t, "")


def build_iso_key(meta: dict, key: str) -> str:
    cat = meta.get("category_key", "other")
    ver = common.slugify(meta.get("version", "")) or "v"
    arch = meta.get("arch", "x64") or "x64"
    typ = meta.get("type", "") or "ed"
    h8 = (key or "0")[:8]
    token = f"{cat}-{ver}-{arch}-{typ}-{h8}"
    return common.slugify(token) or f"iso-{h8}"


def build_description(meta: dict) -> str:
    parts = [meta.get("title", "Windows 镜像")]
    extras = []
    if meta.get("version"):
        extras.append(f"版本 {meta['version']}")
    if meta.get("build"):
        extras.append(f"内部构建 {meta['build']}")
    if meta.get("arch"):
        extras.append(f"架构 {meta['arch']}")
    tl = _type_label(meta.get("type", ""))
    if tl:
        extras.append(tl)
    if meta.get("size"):
        extras.append(f"大小 {meta['size']}")
    if meta.get("sha256"):
        extras.append(f"SHA256 {meta['sha256'][:24]}…")
    if meta.get("kb"):
        extras.append(f"最新补丁 {meta['kb']}")
    if meta.get("lifecycle"):
        extras.append(meta["lifecycle"])
    desc = f"{parts[0]}官方原版镜像下载。" + "，".join(extras) + "。"
    desc += f"本站聚合整理多源原始信息（山己几子木/系统库/HelloWindows），仅供学习参考。{common.SITE_NAME} | {common.SITE_NAME_EN}"
    return desc


# --------------------------------------------------------------------------
# 主合并流程
# --------------------------------------------------------------------------
def merge(snapshots: dict[str, dict], existing_db: dict | None) -> dict:
    """
    snapshots: {source_key: snapshot}
    existing_db: 上一轮 data/iso_data.json（可为 None）
    返回新 db dict。
    """
    today = common.today_str()
    items_by_key: dict[str, dict] = {}
    aliases: dict[str, dict] = {}  # hash -> item 别名索引（sha256/sha1 均可命中）

    # 1) 载入现有 db 作为基线（保留 first_seen 与未刷新源的旧快照）
    if existing_db:
        for it in existing_db.get("items", []):
            key = it.get("key") or ""
            if not key:
                continue  # 历史脏数据：无 key 直接跳过
            items_by_key[key] = it
            aliases.setdefault(key, it)
            for s in it.get("sources_raw") or []:
                h = s.get("hash") or {}
                for hv in (h.get("sha256"), h.get("sha1")):
                    if hv:
                        aliases.setdefault(hv, it)

    # 2) 合并本轮各源快照
    for src_key, snap in snapshots.items():
        crawled_at = snap.get("crawled_at", common.now_str())
        for rec in snap.get("items", []):
            if not isinstance(rec, dict):
                continue
            # 不抓取 Windows Vista 相关镜像（统一排除，标题/文件名含 vista 即跳过）
            _t = str(rec.get("title") or rec.get("filename") or "").lower()
            if "vista" in _t:
                continue
            sha256 = common.norm_hash(rec.get("sha256"))
            sha1 = common.norm_hash(rec.get("sha1"))
            keys = []
            if common.is_valid_sha256(sha256):
                keys.append(sha256)
            if common.is_valid_sha1(sha1):
                keys.append(sha1)
            if not keys:
                print(f"   [!] 跳过无有效哈希记录（长度非法/缺失）: {rec.get('title','') or rec.get('filename','')}")
                continue  # 无效唯一键，不进入主数据，绝不落空键

            # 用别名索引命中（sha256/sha1 任一匹配即可，与顺序无关、幂等）
            item = None
            for k in keys:
                item = aliases.get(k)
                if item:
                    break
            if item is None:
                key, alg = common.pick_key(rec)  # 与别名索引同一长度校验
                if not key:
                    print(f"   [!] 跳过无主键记录: {rec.get('title','') or rec.get('filename','')}")
                    continue
                item = {
                    "iso_key": "",
                    "key": key,
                    "key_algorithm": alg,
                    "category_key": "",
                    "first_seen": today,
                    "last_seen": today,
                    "changed_today": True,
                    "content_updated": today,
                    "meta_unified": {},
                    "sources_raw": [],
                }
                items_by_key[item["key"]] = item
                for k in keys:
                    aliases.setdefault(k, item)

            # 键提升：本记录含 64 位 sha256 而 item 目前以 sha1 为键时，升级为 sha256 主键
            if sha256 and item["key"] != sha256:
                items_by_key.pop(item["key"], None)
                item["key"] = sha256
                item["key_algorithm"] = "sha256"
                items_by_key[sha256] = item
                aliases[sha256] = item

            # 更新此数据源自己的独立快照（禁止覆盖其他源），并对内容变化做指纹判定
            entry = build_source_entry(src_key, rec, crawled_at)
            new_fp = _source_fingerprint(entry)
            replaced = False
            old_fp = None
            for idx, old in enumerate(item["sources_raw"]):
                if old.get("source") == src_key:
                    old_fp = _source_fingerprint(old)
                    item["sources_raw"][idx] = entry
                    replaced = True
                    break
            if not replaced:
                item["sources_raw"].append(entry)
                old_fp = None
            # 内容真变化（该源首次出现或指纹不同）才刷新 content_updated / changed_today
            changed = (not replaced) or (old_fp != new_fp)
            if changed:
                item["changed_today"] = True
                item["content_updated"] = today
            item["last_seen"] = today
            for k in keys:
                aliases[k] = item

    # 3) 为每条重新择优计算 meta_unified
    #    并清除历史遗留的 Windows Vista 条目（已按要求停止收录 Vista）
    items = [
        it for it in items_by_key.values()
        if "vista" not in str((it.get("meta_unified") or {}).get("title") or "").lower()
    ]
    for item in items:
        item["meta_unified"] = _recompute_meta(item)

    # 4) 生成 iso_key（保证唯一、URL 友好）
    used_keys: set[str] = set()
    for item in items:
        meta = item["meta_unified"]
        item["category_key"] = meta.get("category_key", "other")
        base = build_iso_key(meta, item["key"])
        iso = base
        n = 2
        while iso in used_keys:
            iso = f"{base}-{n}"  # n 参与变化，避免碰撞时死循环
            n += 1
            if n > 9999:
                iso = f"{base}-{item.get('key','')[:16]}"
                break
        used_keys.add(iso)
        item["iso_key"] = iso

    # 5) 排序：按分类顺序 → 日期降序 → 版本 → 标题
    cat_rank = {k: i for i, k in enumerate(common.CATEGORY_KEYS)}

    def date_sort(date: str) -> int:
        """把日期字符串转为可排序整数 yyyymmdd（无法解析则回退为 0）。"""
        if not date:
            return 0
        for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"):
            try:
                dt = datetime.datetime.strptime(str(date)[:10], fmt)
                return dt.year * 10000 + dt.month * 100 + dt.day
            except Exception:
                continue
        m = re.search(r"(\d{4})\.(\d{2})", str(date))
        if m:
            return int(m.group(1)) * 10000 + int(m.group(2)) * 100
        m = re.search(r"(\d{4})", str(date))
        if m:
            return int(m.group(1)) * 10000
        return 0

    def sort_key(it):
        meta = it["meta_unified"]
        return (
            cat_rank.get(it["category_key"], 99),
            -date_sort(meta.get("date", "")),
            str(meta.get("version", "") or ""),
            str(meta.get("title", "") or ""),
        )

    items.sort(key=sort_key)
    return {"items": items}


def _recompute_meta(item: dict) -> dict:
    entries = item["sources_raw"]
    if not entries:
        return {"category_key": "other"}

    # 择优顺序（与需求一致）
    TITLE_PRI = common.TITLE_PRIORITY
    LIFECYCLE_PRI = common.LIFECYCLE_KB_PRIORITY
    HASH_PRI = common.HASH_SIZE_PRIORITY

    title = _pick(entries, TITLE_PRI, "title") or _pick(entries, LIFECYCLE_PRI, "title") or _pick(entries, HASH_PRI, "title")
    # 标题兜底：用文件名去掉路径
    if not title:
        for e in entries:
            fn = e.get("filename", "")
            if fn:
                title = fn[:-4] if fn.lower().endswith(".iso") else fn
                break

    size = _pick(entries, HASH_PRI, "size") or _pick(entries, TITLE_PRI, "size") or _pick(entries, LIFECYCLE_PRI, "size")
    sha256 = _pick(entries, HASH_PRI, "sha256") or _pick(entries, TITLE_PRI, "sha256") or _pick(entries, LIFECYCLE_PRI, "sha256")
    kb = _pick(entries, LIFECYCLE_PRI, "kb") or _pick(entries, HASH_PRI, "kb") or _pick(entries, TITLE_PRI, "kb")
    lifecycle = _pick(entries, LIFECYCLE_PRI, "lifecycle") or _pick(entries, HASH_PRI, "lifecycle")
    lifecycle_state = _pick(entries, LIFECYCLE_PRI, "lifecycle_state") or _pick(entries, HASH_PRI, "lifecycle_state")
    support_end = _pick(entries, LIFECYCLE_PRI, "support_end") or _pick(entries, HASH_PRI, "support_end")

    # 其余字段任意可用源取
    version = _pick(entries, TITLE_PRI, "version") or _pick(entries, LIFECYCLE_PRI, "version") or _pick(entries, HASH_PRI, "version")
    build = _pick(entries, LIFECYCLE_PRI, "build") or _pick(entries, HASH_PRI, "build") or _pick(entries, TITLE_PRI, "build")
    date = _pick(entries, TITLE_PRI, "date") or _pick(entries, LIFECYCLE_PRI, "date") or _pick(entries, HASH_PRI, "date")
    editions = _pick(entries, LIFECYCLE_PRI, "editions") or _pick(entries, TITLE_PRI, "editions") or _pick(entries, HASH_PRI, "editions")

    # 类型 / 架构 / 分类：优先 sjjzm 标题语义，其次其他源
    itype = ""
    candidate_types = [_candidate(e).get("type", "") for e in entries]
    for t in candidate_types:
        if t in ("consumer", "business"):
            itype = t
            break
    arch = ""
    for e in sorted(entries, key=lambda x: TITLE_PRI.index(x["source"]) if x["source"] in TITLE_PRI else 999):
        a = normalize_arch(e.get("raw") or {})
        if a:
            arch = a
            break

    category_key = "other"
    for e in entries:
        ck = _candidate(e).get("category_key", "") or ""
        if ck and ck != "other":
            category_key = ck
            break
    if category_key == "other":
        category_key = detect_category(entries[0].get("raw") or {})

    meta = {
        "title": str(title or ""),
        "edition": str(title or ""),
        "version": str(version or ""),
        "build": str(build or ""),
        "arch": str(arch or ""),
        "type": str(itype or ""),
        "size": str(size or ""),
        "kb": str(kb or ""),
        "lifecycle": str(lifecycle or ""),
        "lifecycle_state": str(lifecycle_state or ""),
        "support_end": str(support_end or ""),
        "sha256": str(sha256 or ""),
        "date": str(date or ""),
        "editions": str(editions or "") if not isinstance(editions, (list, tuple)) else list(editions),
        "category_key": str(category_key or ""),
        "updated_at": common.today_str(),
        "desc": "",
    }
    meta["desc"] = build_description(meta)
    return meta
