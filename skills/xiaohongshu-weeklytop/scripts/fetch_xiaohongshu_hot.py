"""
小红书七日爆款笔记 - RedFox API 采集脚本
====================================
查询小红书过去 7 天 AI 相关领域的爆款笔记，返回 top 5。
"""
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Optional


API_BASE = "https://redfox.hk/story/api/xhsData"
REQUEST_DELAY = 0.2
TIMEOUT = 30

DEFAULT_KEYWORDS = ["AI工具", "AI编程", "AI智能体", "Agent", "大模型"]


def _api_post(endpoint: str, body: dict, api_key: str) -> dict:
    """统一的 API POST 请求"""
    url = f"{API_BASE}/{endpoint}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "X-API-KEY": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"code": e.code, "msg": str(e), "data": None}
    except Exception as e:
        return {"code": -1, "msg": str(e), "data": None}


def fetch_hot_notes(api_key: str, count: int = 5,
                    keywords: Optional[list[str]] = None) -> dict:
    """
    主采集函数 - 查询小红书 AI 爆款笔记

    Args:
        api_key: RedFox API Key
        count: 返回数量 (默认 5)
        keywords: 搜索关键词列表

    Returns:
        {"platform": "xiaohongshu", "sampleSize": N, "items": [...], "errors": [...]}
    """
    errors = []
    kw_list = keywords or DEFAULT_KEYWORDS
    all_notes = []

    # Step 1: 多关键词搜索
    for kw in kw_list[:5]:
        result = _api_post("searchNote", {
            "keyword": kw,
            "sortType": "hot",
            "count": 20,
        }, api_key)

        if result.get("code") != 2000:
            errors.append(f"搜索 '{kw}' 失败: {result.get('msg')}")
            continue

        notes = result.get("data", {}).get("list", [])
        # 筛选近 7 天
        cutoff = datetime.now() - timedelta(days=7)
        for note in notes:
            pub_time = note.get("publishTime", "")
            if pub_time:
                try:
                    pt = datetime.fromisoformat(pub_time.replace("Z", "+00:00"))
                    if pt.tzinfo:
                        pt = pt.replace(tzinfo=None)
                    if pt < cutoff:
                        continue
                except (ValueError, TypeError):
                    pass  # 无法解析时间的保留
            all_notes.append(note)

        time.sleep(REQUEST_DELAY)

    if not all_notes:
        return {
            "platform": "xiaohongshu",
            "sampleSize": 0,
            "items": [],
            "errors": errors + ["未找到近 7 天热门笔记"],
        }

    # 去重 (按 workId)
    seen = set()
    unique_notes = []
    for n in all_notes:
        nid = n.get("workId") or n.get("id")
        if nid and nid not in seen:
            seen.add(nid)
            unique_notes.append(n)

    # 按互动量排序 (小红书: 收藏权重大)
    def _score(n):
        return (n.get("likeCount", 0) or 0) * 0.35 + \
               (n.get("collectCount", 0) or 0) * 0.35 + \
               (n.get("commentCount", 0) or 0) * 0.2 + \
               (n.get("shareCount", 0) or 0) * 0.1

    unique_notes.sort(key=_score, reverse=True)
    top_notes = unique_notes[:count]

    # Step 2: 补全笔记详情
    items = []
    for n in top_notes:
        nid = n.get("workId") or n.get("id")
        if nid:
            detail = _api_post("queryWork", {"workId": nid}, api_key)
            time.sleep(REQUEST_DELAY)

            if detail.get("code") == 2000 and detail.get("data"):
                d = detail["data"]
                items.append({
                    "title": d.get("title") or n.get("title", ""),
                    "author": d.get("author") or n.get("author", ""),
                    "likeCount": d.get("likeCount") or n.get("likeCount", 0),
                    "collectCount": d.get("collectCount") or n.get("collectCount", 0),
                    "commentCount": d.get("commentCount") or n.get("commentCount", 0),
                    "shareCount": d.get("shareCount") or n.get("shareCount", 0),
                    "coverUrl": d.get("coverUrl", ""),
                    "workUrl": d.get("workUrl", ""),
                })
            else:
                items.append(n)
                errors.append(f"获取笔记详情失败: {nid}")
        else:
            items.append(n)

    return {
        "platform": "xiaohongshu",
        "sampleSize": len(items),
        "items": items,
        "errors": errors,
    }


def run(config: dict) -> dict:
    """Skill 标准入口"""
    return fetch_hot_notes(
        api_key=config["api_key"],
        count=config.get("count", 5),
        keywords=config.get("keywords"),
    )
