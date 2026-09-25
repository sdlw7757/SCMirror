# -*- coding: utf-8 -*-
"""
baidu_push.py —— 百度收录主动推送（增量）
- 推送接口：POST http://data.zz.baidu.com/urls?site=<site>&token=<token>
- 内容：每行一个 URL，单次不超过 2000 条。
- 策略：
    * 核心导航页（主页 /、/tool-hash、/wiki、全部分类页每次必推）单独优先批次，
      保证即使详情页配额（over quota）失败，主页/工具/知识库/分类页也已被提交。
    * 详情页增量：本轮新增（first_seen==today）或内容变化（lastmod 变化）时补推。
    * 状态文件（data/.baidu_push_state.json）记录已推送 URL 与其 lastmod，避免重复消耗配额。
- 推送 base 必须与百度注册站点（BAIDU_SITE）域名一致。
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
# 推送失败详情：写入仓库 data/，由 CI 自动提交，方便直接查看失败原因
PUSH_ERROR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", ".baidu_push_error.json"
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
        """urls: [{loc, lastmod, is_new, always}]. 增量推送本轮 URL。

        优先级：
          - always（核心导航页：主页/工具/知识库/分类页）→ 单独优先批次，每次必推，
            即使后续详情页因配额（over quota）失败，也要保证核心页已提交且状态落盘。
          - 其余（详情页/首次分类）→ 增量批次，依 lastmod/是否新增判定。
        """
        if not self.site or not self.token:
            return {"ok": False, "reason": "缺少 site/token，跳过推送（本地不默认启用）", "pushed": 0}

        state = self._load_state()
        pushed = state.get("pushed", {})
        today = common.today_str()
        loc_lastmod = {u["loc"]: (u.get("lastmod") or today) for u in urls}

        # 1) 核心导航页：每次运行必推
        core = [u["loc"] for u in urls if u.get("always")]
        # 2) 增量详情/首次分类
        details = []
        for u in urls:
            if u.get("always"):
                continue
            loc = u["loc"]
            lastmod = u.get("lastmod", today)
            is_new = u.get("is_new", False)
            is_cat = u.get("is_category", False)
            prev = pushed.get(loc)
            if prev is None:
                details.append(loc)      # 首次（含历史未推过的分类/详情）
            elif is_cat:
                continue                 # 分类已推送过，不再每日重复推静态
            elif is_new or prev != lastmod:
                details.append(loc)      # 详情新增或内容更新

        batches: list[list[str]] = []
        if core:
            batches.append(core)
        if details:
            for i in range(0, len(details), 1000):
                batches.append(details[i : i + 1000])

        if not batches:
            return {"ok": True, "reason": "无增量 URL", "pushed": 0}

        total_ok = 0
        ok_all = True
        last_fail = None
        for batch in batches:
            resp = self._post_batch(batch)
            if not resp.get("ok"):
                # 配额不足（over quota）等失败：核心页已在此批次之前优先提交，
                # 停止后续批次以保留配额，但保留本轮已成功批次的状态。
                ok_all = False
                last_fail = resp
                break
            total_ok += resp.get("success", 0)
            # 成功后更新状态并立即持久化（避免部分批次失败时已成功批次丢失而重复推送）
            for loc in batch:
                pushed[loc] = loc_lastmod.get(loc, today)
            self._save_state(pushed)

        # 归一失败原因：网络异常(.reason) 或 业务错误(HTTP status + message/error)
        planned = len(core) + len(details)
        fail_reason = None
        if last_fail is not None:
            fail_reason = last_fail.get("reason")
            if not fail_reason:
                if last_fail.get("message"):
                    fail_reason = f"HTTP {last_fail.get('status')}: {last_fail.get('message')}"
                elif last_fail.get("status"):
                    fail_reason = f"HTTP {last_fail.get('status')}"

        if not ok_all:
            # 失败详情落盘到仓库 data/（CI 自动提交），方便直接查看原因
            common.write_json(PUSH_ERROR, {
                "time": common.now_str(),
                "reason": fail_reason or "未知错误",
                "detail": {k: v for k, v in (last_fail or {}).items() if k not in ("reason",)},
            })
        else:
            try:
                os.remove(PUSH_ERROR)
            except OSError:
                pass

        return {
            "ok": ok_all,
            "reason": (f"推送 {total_ok}/{planned} 条 URL；失败: {fail_reason or '-'}"
                       if not ok_all else f"全部推送成功 {total_ok} 条 URL"),
            "pushed": total_ok,
            "core_pushed": min(total_ok, len(core)),
            "debug": (core + details)[:10],
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
                data = r.json() if r.content else {}
                # 业务失败判定：百度对"URL 不属于该站点 / token 无效 / 内容非法"等情况，
                # 可能返回 HTTP 200 但 body 带 error 字段且 success=0。若只看 HTTP 状态码，
                # 会把失败当成功并永久记录为"已推送"，导致该 URL 永不再重试。因此必须同时
                # 检查：HTTP 200 且无 error 字段且（批次非空时）success>0 才算成功。
                biz_err = data.get("error")
                success = int(data.get("success", 0) or 0)
                ok = (
                    r.status_code == 200
                    and (biz_err in (None, 0, "", "0"))
                    and (success > 0 if batch else True)
                )
                return {
                    "ok": ok,
                    "status": r.status_code,
                    "success": success,
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


def build_push_urls(items: list[dict], categories: list[dict], base: str = "", core_only: bool = False) -> list[dict]:
    """依据本轮聚合结果，构造待推送 URL（核心导航页 + 详情 + 分类），标出是否新增。

    - 核心导航页（每次运行都推，保证主页/工具/知识库/分类页常驻百度）：使用 absolute base 前缀。
    - 若 core_only=True，只返回核心导航页（不推详情/全量分类），用于配额紧张时的兜底。
    base 必须是完整可收录的绝对地址前缀（如 https://你的域名）。
    若 base 为空，返回空列表（调用方应跳过推送，避免推相对地址给百度而无法收录）。
    """
    base = (base or "").strip().rstrip("/")
    if not base:
        return []
    today = common.today_str()
    urls: list[dict] = []

    # 核心导航页：每次运行强制推送（always=True → 不受“已推送过”限制）
    core = [
        {"path": "/", "lastmod": today},
        {"path": "/tool-hash", "lastmod": today},
        {"path": "/wiki", "lastmod": today},
    ]
    for cat in categories:
        key = cat.get("key") or ""
        if key:
            core.append({"path": f"/category/{key}", "lastmod": today})

    for c in core:
        urls.append({
            "loc": f"{base}{c['path']}",
            "lastmod": c["lastmod"],
            "is_new": False,
            "is_category": False,
            "always": True,  # 核心页每次必推
        })

    if core_only:
        return urls

    # 详情页增量：本轮新增（first_seen==today）或内容变化时补推
    for it in items:
        first = it.get("first_seen")
        is_new = first == today
        urls.append({
            "loc": f"{base}/detail/{it.get('iso_key','')}",
            "lastmod": it.get("content_updated") or it.get("last_seen") or today,
            "is_new": is_new,
            "is_category": False,
            "always": False,
        })
    return urls


def push_incremental(items: list[dict], categories: list[dict], site=None, token=None, base=None) -> dict:
    pusher = BaiduPusher(site, token)
    # 推送 base 必须与百度注册的站点（BAIDU_SITE）域名保持一致，否则百度无法归属校验。
    # 这里优先取 BAIDU_SITE；仅当其缺失/为裸域名时才回退到 SITE_URL。
    if not base:
        site_v = (pusher.site or "").strip().rstrip("/")
        fallback = (common.SITE_URL or "").strip().rstrip("/")
        base = _normalize_site(site_v) or (fallback if fallback.startswith(("http://", "https://")) else "")
    if not base:
        # 站点 base 缺失是配置错误（BAIDU_SITE 未配或不是合法域名），不能谎报“无增量”。
        return {"ok": False, "reason": "推送 base 为空：请配置 BAIDU_SITE（如 https://517757.xyz）", "pushed": 0}
    urls = build_push_urls(items, categories, base)
    return pusher.push(urls)


def _normalize_site(site: str) -> str:
    """把推送 base 归一为完整可收录绝对地址（补 https://），空/无法识别时返回空串。"""
    s = (site or "").strip().rstrip("/")
    # 已是绝对地址
    if s.startswith(("http://", "https://")):
        return s
    # 合法裸域名 → 补 https://
    if s and "." in s and " " not in s:
        return f"https://{s}"
    return ""


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "iso_data.json")
    db = common.read_json(db_path)
    if db:
        res = push_incremental(db.get("items", []), db.get("categories", []))
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("data/iso_data.json 不存在")
