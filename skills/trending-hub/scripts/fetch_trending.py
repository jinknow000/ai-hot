"""
全网热点追踪 - RedFox API 采集脚本
==============================
聚合 7 平台热搜数据，过滤 AI 相关热点话题。
"""
import json
import time
import urllib.request
import urllib.error
from typing import Optional


API_BASE = "https://redfox.hk/story/api/trendingData"
TIMEOUT = 30

# AI 话题过滤关键词
AI_FILTER_KEYWORDS = [
    "AI", "人工智能", "大模型", "ChatGPT", "GPT", "Claude", "Gemini",
    "DeepSeek", "Kimi", "文心", "通义", "智能体", "Agent", "AIGC",
    "机器学习", "深度学习", "神经网络", "LLM", "OpenAI", "Copilot",
    "Cursor", "Codex", "Midjourney", "Stable Diffusion", "Sora",
]


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


def _is_ai_related(title: str) -> bool:
    """判断话题是否 AI 相关"""
    title_lower = title.lower()
    for kw in AI_FILTER_KEYWORDS:
        if kw.lower() in title_lower:
            return True
    return False


def fetch_trending(api_key: str, count: int = 20) -> dict:
    """
    主采集函数 - 拉取全网 AI 相关热点

    Args:
        api_key: RedFox API Key
        count: 返回数量 (默认 20)

    Returns:
        {"platform": "trending-hub", "sampleSize": N, "items": [...], "errors": [...]}
    """
    errors = []

    result = _api_post("query", {
        "platform": "all",
        "count": 50,
    }, api_key)

    if result.get("code") != 2000:
        return {
            "platform": "trending-hub",
            "sampleSize": 0,
            "items": [],
            "errors": [f"全网热点查询失败: {result.get('msg')}"],
        }

    all_topics = result.get("data", {}).get("list", [])

    # 过滤 AI 相关 + 去重
    seen = set()
    ai_topics = []
    for topic in all_topics:
        title = topic.get("title", "")
        if _is_ai_related(title):
            # 去重
            if title not in seen:
                seen.add(title)
                ai_topics.append({
                    "title": title,
                    "platform": topic.get("platform", ""),
                    "hotValue": topic.get("hotValue", 0),
                    "rank": topic.get("rank", 0),
                    "url": topic.get("url", ""),
                })

    # 按热度值降序
    ai_topics.sort(key=lambda x: x.get("hotValue", 0) or 0, reverse=True)

    return {
        "platform": "trending-hub",
        "sampleSize": min(len(ai_topics), count),
        "items": ai_topics[:count],
        "errors": errors,
    }


def run(config: dict) -> dict:
    """Skill 标准入口"""
    return fetch_trending(
        api_key=config["api_key"],
        count=config.get("count", 20),
    )
