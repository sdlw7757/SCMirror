# -*- coding: utf-8 -*-
"""
baidu_push.py —— 百度收录主动推送（增量）
- 推送接口：POST http://data.zz.baidu.com/urls?site=<site>&token=<token>
- 内容：每行一个 URL，单次不超过 2000 条。
- 增量策略：
    * 保持一份状态文件（data/.baidu_push_state.json）记录已推送 URL 与其 lastmod。
    * 每次先推送“本轮新增/更新的镜像详情页”以及“新增或变化的分类页”。
    * 若状态文件为空（首次），则全量推送所有 URL。
- 本轮参与聚合判定：first_seen==today（新增）或 last_seen==today（更新）。
"""
from __future__ import annotations

import io
import json
import os
import sys
import time

import requests

from . import common

API = "http://data.zz.baidu.com/urls"
PUSH_STATE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", ".baidu_push_state.json"
)


class BaiduPusher:
    def __init__(self, site: str | None = None, token: str | None = None):
        self.site = site or _default_site()
        self.token = token or _default_token()
        self._state = common.read_json(PUSH_STATE, {"pushed": {}})

    def _load_state(self) -> dict:
        state = common.read_json(PUSH_STATE, {})
        return state if isinstance(state, dict) else {}

    def _save_state(self, pushed: dict) -> None:
        common.write_json(PUSH_STATE, {"pushed": pushed})

    def push(self, urls: list[dict]) -> dict:
        """urls: [{loc, lastmod, is_new}]. 增量推送本轮新 URL。"""
        if not self.site or not self.token:
            return {"ok": False, "reason": "缺少 site/token，跳过推送（本地不默认启用）", "pushed": 0}

        state = self._load_state()
        pushed = state.get("pushed", {})

        # 计算本轮增量：
        #   - 完全未推送的 URL 一律推送（首次含全量）
        #   - 详情页：lastmod 变化（内容更新）或本轮新增（first_seen==today）时补推
        #   - 分类页：仅在“从未推送”（首次）时推送，避免每个每日都重复推静态分类
        incremental = []
        today = common.today_str()
        for u in urls:
            loc = u["loc"]
            lastmod = u.get("lastmod", today)
            is_new = u.get("is_new", False)
            is_cat = u.get("is_category", False)
            prev = pushed.get(loc)
            if prev is None:
                incremental.append(loc)  # 首次（含分类首次、全量）
            elif is_cat:
                continue  # 分类已推送过，不再每日重复
            elif is_new or prev != lastmod:
                incremental.append(loc)  # 详情新增或内容更新

        if not incremental:
            return {"ok": True, "reason": "无增量 URL", "pushed": 0}

        total_ok = 0
        # 分组推送，每批 ≤ 1000 条
        ok_all = True
        for i in range(0, len(incremental), 1000):
            batch = incremental[i : i + 1000]
            resp = self._post_batch(batch)
            if not resp.get("ok"):
                ok_all = False
                break
            total_ok += resp.get("success", 0)
            # 成功后更新状态并立即持久化（避免部分批次失败时已成功批次丢失而重复推送）
            for loc in batch:
                pushed[loc] = next((u["lastmod"] for u in urls if u["loc"] == loc), today)
            self._save_state(pushed)

        return {
            "ok": ok_all,
            "reason": f"推送 {total_ok}/{len(incremental)} 条 URL" if not ok_all else f"全部推送成功 {total_ok} 条 URL",
            "pushed": total_ok,
            "debug": incremental[:5],
        }

    def _post_batch(self, batch: list[str]) -> dict:
        url = f"{API}?site={self.site}&token={self.token}"
        body = "\n".join(batch)
        last_err = None
        sess = requests.Session()
        sess.trust_env = False  # 忽略系统/环境代理，避免本机代理故障导致推送失败
        for attempt in range(1, 4):  # 单批重试（指数退避），提升弱网环境推送成功率
            try:
                r = sess.post(
                    url,
                    data=body.encode("utf-8"),
                    headers={"Content-Type": "text/plain", "User-Agent": common.DEFAULT_HEADERS["User-Agent"]},
                    timeout=30,
                )
                data = r.json()
                return {
                    "ok": r.status_code == 200,
                    "success": data.get("success", 0),
                    "remain": data.get("remain", 0),
                    **data,
                }
            except Exception as e:  # noqa: BLE001
                last_err = f"{type(e).__name__}: {e}"
                if attempt < 3:
                    time.sleep(1.5 * attempt)
        return {"ok": False, "reason": last_err or "重试后仍失败"}


def _default_site() -> str:
    return os.environ.get("BAIDU_SITE", "")


def _default_token() -> str:
    return os.environ.get("BAIDU_TOKEN", "")


def build_push_urls(items: list[dict], categories: list[dict], base: str = "") -> list[dict]:
    """依据本轮聚合结果，构造待推送 URL（详情 + 分类），标出是否新增。

    base 必须是完整可收录的绝对地址前缀（如 https://你的域名）。
    若 base 为空，返回空列表（调用方应跳过推送，避免推相对地址给百度而无法收录）。
    """
    base = (base or "").strip().rstrip("/")
    if not base:
        return []
    today = common.today_str()
    urls = []
    for cat in categories:
        urls.append({
            "loc": f"{base}/category/{cat['key']}",
            "lastmod": today,
            "is_new": True,
            "is_category": True,
        })
    for it in items:
        first = it.get("first_seen")
        is_new = first == today
        urls.append({
            "loc": f"{base}/detail/{it.get('iso_key','')}",
            "lastmod": it.get("content_updated") or it.get("last_seen") or today,
            "is_new": is_new,
            "is_category": False,
        })
    return urls


def push_incremental(items: list[dict], categories: list[dict], site=None, token=None) -> dict:
    pusher = BaiduPusher(site, token)
    # 推送前缀取 SITE_URL，缺省时用 BAIDU_SITE，绝不以相对地址推送
    base = (common.SITE_URL or pusher.site or "").strip().rstrip("/")
    urls = build_push_urls(items, categories, base)
    return pusher.push(urls)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "iso_data.json")
    db = common.read_json(db_path)
    if db:
        res = push_incremental(db.get("items", []), db.get("categories", []))
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("data/iso_data.json 不存在")
