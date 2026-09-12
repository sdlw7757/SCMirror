# -*- coding: utf-8 -*-
"""
stats.py —— 海云镜像 自动统计
首页统计（无需前端计算）：总收录、今日新增/更新、最后同步时间，写入 JSON 顶层。
"""
from __future__ import annotations

from . import common


def compute_stats(items: list[dict], last_sync: str | None = None) -> dict:
    today = common.today_str()
    total = len(items)

    today_new = 0
    today_update = 0
    by_category: dict[str, int] = {k: 0 for k in common.CATEGORY_KEYS}

    all_crawled = []
    for it in items:
        ck = it.get("category_key", "other")
        by_category[ck] = by_category.get(ck, 0) + 1
        if it.get("first_seen") == today:
            today_new += 1
        if it.get("changed_today"):
            today_update += 1  # 仅内容真正变化的镜像计入“今日更新”
        for src in it.get("sources_raw", []):
            ct = src.get("crawl_time", "")
            if ct:
                all_crawled.append(ct)

    if not last_sync and all_crawled:
        last_sync = max(all_crawled)
    if not last_sync:
        last_sync = common.now_str()

    return {
        "total": total,
        "today_new": today_new,
        "today_update": today_update,
        "today_count": today_new + today_update,  # 今日新增/更新 总量
        "last_sync": last_sync,
        "by_category": by_category,
        "generated_at": common.now_str(),
    }


def build_categories() -> list[dict]:
    """从静态分类体系生成可用于前端导航/分类详情页的数据。"""
    return [dict(c) for c in common.CATEGORIES]


def site_info() -> dict:
    """顶层站点信息（前端页脚/SEO 读取）。"""
    return {
        "name": common.SITE_NAME,
        "name_en": common.SITE_NAME_EN,
        "url": common.SITE_URL,
        "github": common.GITHUB_REPO,
        "disclaimer": common.DISCLAIMER,
        "sources": {
            k: {"name": v["name"], "en": v["en"], "home": v["home"]}
            for k, v in common.SOURCES.items()
        },
    }
