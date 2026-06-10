"""
抖音热门作品搜索 - RedFox API 采集脚本
===============================
基于关键词搜索抖音 AI 热门视频，返回 top 5 爆款作品及互动数据。
"""
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Optional


API_BASE = "https://redfox.hk/story/api/dyData"
REQUEST_DELAY = 0.2  # API 请求间隔 (秒)
TIMEOUT = 30  # 请求超时 (秒)


def _api_post(endpoint: str, body: dict, api_key: str) -> dict:
    """统一的 API POST 请求封装"""
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


def expand_keywords(base_keyword: str) -> list[str]:
    """泛化关键词扩展为 10 个细分关键词"""
    mapping = {
        "AI": ["AI工具", "AI绘画", "AI编程", "AI视频", "AI写作",
                "AI教育", "AI医疗", "AI金融", "AI法律", "AI客服"],
        "大模型": ["GPT", "Claude", "Gemini", "文心一言", "通义千问",
                   "Kimi", "DeepSeek", "ChatGPT", "大模型应用", "LLM"],
        "AI工具": ["AI编程助手", "AI绘图工具", "AI视频生成",
                    "AI文案工具", "AI配音", "AI办公", "AI搜索引擎"],
    }
    return mapping.get(base_keyword, [base_keyword])


def fetch_hot_works(keyword: str, api_key: str, count: int = 5) -> dict:
    """
    主采集函数 - 搜索抖音热门 AI 作品

    Args:
        keyword: 搜索关键词
        api_key: RedFox API Key
        count: 返回作品数量 (默认 5)

    Returns:
        {"platform": "douyin", "sampleSize": N, "items": [...], "errors": [...]}
    """
    errors = []
    items = []

    # Step 1: 关键词搜索
    kw_list = expand_keywords(keyword)
    all_works = []

    for kw in kw_list[:3]:  # 最多用 3 个扩展关键词，减少 API 调用
        result = _api_post("search", {
            "keyword": kw,
            "offset": 0,
            "count": 10,
        }, api_key)

        if result.get("code") != 2000:
            errors.append(f"搜索 '{kw}' 失败: {result.get('msg')}")
            continue

        works = result.get("data", {}).get("list", [])
        all_works.extend(works)
        time.sleep(REQUEST_DELAY)

    if not all_works:
        return {
            "platform": "douyin",
            "sampleSize": 0,
            "items": [],
            "errors": errors + ["关键词搜索返回空结果"],
        }

    # 去重 (按 workId)
    seen = set()
    unique_works = []
    for w in all_works:
        wid = w.get("workId") or w.get("id")
        if wid and wid not in seen:
            seen.add(wid)
            unique_works.append(w)

    # 按互动量预排序取 top
    def _score(w):
        return (w.get("likeCount", 0) or 0) * 0.3 + \
               (w.get("commentCount", 0) or 0) * 0.25 + \
               (w.get("shareCount", 0) or 0) * 0.25 + \
               (w.get("collectCount", 0) or 0) * 0.2

    unique_works.sort(key=_score, reverse=True)
    top_works = unique_works[:count]

    # Step 2: 补全作品详情
    for w in top_works:
        wid = w.get("workId") or w.get("id")
        if not wid:
            items.append(w)
            continue

        detail = _api_post("queryWork", {"workId": wid}, api_key)
        time.sleep(REQUEST_DELAY)

        if detail.get("code") == 2000 and detail.get("data"):
            d = detail["data"]
            items.append({
                "title": d.get("title") or w.get("title", ""),
                "author": d.get("author") or w.get("author", ""),
                "likeCount": d.get("likeCount") or w.get("likeCount", 0),
                "commentCount": d.get("commentCount") or w.get("commentCount", 0),
                "shareCount": d.get("shareCount") or w.get("shareCount", 0),
                "collectCount": d.get("collectCount") or w.get("collectCount", 0),
                "commentHotWords": d.get("commentHotWords", []),
                "coverUrl": d.get("coverUrl", ""),
                "workUrl": d.get("workUrl", ""),
            })
        else:
            items.append(w)
            errors.append(f"获取作品 '{wid}' 详情失败")

    return {
        "platform": "douyin",
        "sampleSize": len(items),
        "items": items,
        "errors": errors,
    }


# Skill 入口 - 供 SkillLoader 调用
def run(config: dict) -> dict:
    """Skill 标准入口

    Args:
        config: {"api_key": "xxx", "keyword": "AI", "count": 5}

    Returns:
        结构化 JSON 结果
    """
    return fetch_hot_works(
        keyword=config.get("keyword", "AI"),
        api_key=config["api_key"],
        count=config.get("count", 5),
    )
