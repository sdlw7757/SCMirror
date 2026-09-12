# -*- coding: utf-8 -*-
"""
main.py —— 海云镜像 爬虫系统主入口

流程：抓取三站 → 写原始快照 data/raw/*.json → 合并(merge) → 统计(stats)
      → 写 data/iso_data.json → 生成 sitemap.xml/robots.txt → 百度增量推送

参数：
  --only sjjzm|xitongku|hello   只抓取指定站（默认全抓）
  --skip-crawl                  跳过抓取，直接使用 data/raw 现有快照（用于重跑合并）
  --skip-sitemap                跳过 sitemap 生成
  --skip-baidu                  跳过百度推送
  --dry-run                     只计算并打印统计，不写文件、不推送
"""
from __future__ import annotations

import argparse
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from . import common          # noqa: E402
from . import baidu_push      # noqa: E402
from . import merge as merge_mod  # noqa: E402
from . import p1_sjjzm        # noqa: E402
from . import p2_xitongku     # noqa: E402
from . import p3_hello        # noqa: E402
from . import sitemap as sitemap_mod  # noqa: E402
from . import stats as stats_mod      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw")
DB_PATH = os.path.join(ROOT, "data", "iso_data.json")

CRAWLERS = {
    "sjjzm": p1_sjjzm.crawl,
    "xitongku": p2_xitongku.crawl,
    "hello": p3_hello.crawl,
}
ONLY_ALL = list(CRAWLERS.keys())


def run_crawlers(only: list[str]) -> dict[str, dict]:
    snapshots = {}
    os.makedirs(RAW_DIR, exist_ok=True)
    keys = ONLY_ALL if not only else only
    for key in keys:
        print(f"== 抓取 [{key}] ({common.SOURCES[key]['name']}) ...")
        try:
            snap = CRAWLERS[key]()
        except Exception as e:  # noqa: BLE001
            print(f"   [!] [{key}] 抓取异常，已隔离，不影响其他站: {type(e).__name__}: {e}")
            snap = {"crawled_at": common.now_str(), "items": [], "warnings": [f"异常隔离: {type(e).__name__}: {e}"]}
        snapshots[key] = snap
        raw_path = os.path.join(RAW_DIR, f"{key}.json")
        common.write_json(raw_path, snap)
        warnings = snap.get("warnings", [])
        print(f"   {key}: {len(snap.get('items', []))} 条原始记录"
              + (f"，警告: {len(warnings)}" if warnings else ""))
        for w in warnings[:5]:
            print(f"   [!] {w}")
    return snapshots


def load_raw_snapshots(only: list[str]) -> dict[str, dict]:
    snapshots = {}
    os.makedirs(RAW_DIR, exist_ok=True)
    keys = ONLY_ALL if not only else only
    for key in keys:
        snap = common.read_json(os.path.join(RAW_DIR, f"{key}.json"), {})
        if snap:
            snapshots[key] = snap
            print(f"   载入原始快照 {key}: {len(snap.get('items', []))} 条")
        else:
            print(f"   [!] data/raw/{key}.json 不存在")
    return snapshots


def build_db(snapshots: dict[str, dict]) -> dict:
    existing = common.read_json(DB_PATH)
    merged = merge_mod.merge(snapshots, existing)
    items = merged["items"]

    site = stats_mod.site_info()
    categories = stats_mod.build_categories()
    st = stats_mod.compute_stats(items)

    # 汇总各分类实际存在与否：仅保留有内容的分类（导航干净）
    active_categories = []
    bc = st["by_category"]
    for c in categories:
        if bc.get(c["key"], 0) > 0:
            active_categories.append(c)

    db = {
        "site": site,
        "stats": st,
        "categories": active_categories,
        "items": items,
    }
    return db


def main() -> None:
    parser = argparse.ArgumentParser(description="海云镜像 三站聚合爬虫")
    parser.add_argument("--only", action="append", choices=list(CRAWLERS.keys()))
    parser.add_argument("--skip-crawl", action="store_true")
    parser.add_argument("--skip-sitemap", action="store_true")
    parser.add_argument("--skip-baidu", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"===== 海云镜像 爬虫系统 v1.0  {common.now_str()} =====")

    if args.skip_crawl:
        snapshots = load_raw_snapshots(args.only or [])
    else:
        snapshots = run_crawlers(args.only or [])

    if not snapshots:
        print("[!] 无任何原始数据可合并，终止。")
        sys.exit(1)

    db = build_db(snapshots)
    st = db["stats"]
    print("\n== 合并统计 ==")
    print(f"   总收录: {st['total']}  今日新增: {st['today_new']}  今日更新: {st['today_update']}")
    print(f"   最后同步: {st['last_sync']}")
    for c in db["categories"]:
        print(f"   [{c['key']}] {c['name']}: {st['by_category'].get(c['key'], 0)}")

    if args.dry_run:
        print("\n(--dry-run 模式，不写文件、不推送)")
        sys.exit(0)

    common.write_json(DB_PATH, db)
    print(f"\n== 已写入 {DB_PATH}（共 {st['total']} 条镜像）==")

    if not args.skip_sitemap:
        try:
            res = sitemap_mod.write_sitemap(db["items"], db["categories"])
            print(f"== 已生成 sitemap.xml（{res['url_count']} 条 URL）与 robots.txt ==")
        except Exception as e:  # noqa: BLE001
            print(f"[!] sitemap 生成失败（不影响已写入的 DB）: {type(e).__name__}: {e}")

    if not args.skip_baidu:
        try:
            ret = baidu_push.push_incremental(
                db["items"],
                db["categories"],
                site=os.environ.get("BAIDU_SITE"),
                token=os.environ.get("BAIDU_TOKEN"),
            )
            print(f"== 百度推送: {ret.get('reason')} ==")
        except Exception as e:  # noqa: BLE001
            print(f"[!] 百度推送失败（不影响已写入的 DB）: {type(e).__name__}: {e}")

    print("\n===== 完成 =====")


if __name__ == "__main__":
    main()
