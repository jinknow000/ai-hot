"""
公众号 10w+ 爆款文章推荐 - RedFox API 采集脚本
===========================================
搜索微信公众号 AI 相关 10w+ 爆款文章，返回 top 5。
"""
import json
import time
import urllib.request
import urllib.error
from typing import Optional


API_BASE = "https://redfox.hk/story/api/gzhData"
REQUEST_DELAY = 0.2
TIMEOUT = 30

# 固定关键词列表
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


def _interaction_rate(item: dict) -> float:
    """计算互动率"""
    reads = item.get("readCount", 0) or 1
    interactions = (item.get("likeCount", 0) or 0) + \
                   (item.get("wowCount", 0) or 0) + \
                   (item.get("commentCount", 0) or 0) + \
                   (item.get("shareCount", 0) or 0)
    return interactions / max(reads, 1)


def fetch_hot_articles(api_key: str, count: int = 5,
                       keywords: Optional[list[str]] = None) -> dict:
    """
    主采集函数 - 搜索公众号 AI 爆款文章

    Args:
        api_key: RedFox API Key
        count: 返回数量 (默认 5)
        keywords: 搜索关键词列表 (可选，默认使用内置列表)

    Returns:
        {"platform": "wechat", "sampleSize": N, "items": [...], "errors": [...]}
    """
    errors = []
    kw_list = keywords or DEFAULT_KEYWORDS
    all_articles = []

    # Step 1: 多关键词搜索
    for kw in kw_list:
        result = _api_post("searchArticle", {
            "keyword": kw,
            "offset": 0,
            "sortType": "_4",  # 按阅读数倒序
        }, api_key)

        if result.get("code") != 2000:
            errors.append(f"搜索 '{kw}' 失败: {result.get('msg')}")
            continue

        articles = result.get("data", {}).get("list", [])
        # 筛选 10w+ 阅读
        for a in articles:
            if (a.get("readCount", 0) or 0) >= 100000:
                all_articles.append(a)

        time.sleep(REQUEST_DELAY)

    if not all_articles:
        return {
            "platform": "wechat",
            "sampleSize": 0,
            "items": [],
            "errors": errors + ["未找到 10w+ 文章"],
        }

    # 去重 (按 workUrl)
    seen = set()
    unique_articles = []
    for a in all_articles:
        url = a.get("workUrl", "")
        if url and url not in seen:
            seen.add(url)
            unique_articles.append(a)

    # 按阅读数降序
    unique_articles.sort(key=lambda x: x.get("readCount", 0) or 0, reverse=True)
    top_articles = unique_articles[:count]

    # Step 2: 补全文章详情
    items = []
    for a in top_articles:
        url = a.get("workUrl", "")
        if url:
            detail = _api_post("queryArticle", {"workUrl": url}, api_key)
            time.sleep(REQUEST_DELAY)

            if detail.get("code") == 2000 and detail.get("data"):
                d = detail["data"]
                items.append({
                    "title": d.get("title") or a.get("title", ""),
                    "author": d.get("author") or a.get("author", ""),
                    "readCount": d.get("readCount") or a.get("readCount", 0),
                    "likeCount": d.get("likeCount") or a.get("likeCount", 0),
                    "wowCount": d.get("wowCount") or a.get("wowCount", 0),
                    "commentCount": d.get("commentCount") or a.get("commentCount", 0),
                    "shareCount": d.get("shareCount") or a.get("shareCount", 0),
                    "publishTime": d.get("publishTime", ""),
                    "workUrl": url,
                })
            else:
                items.append(a)
                errors.append(f"获取文章详情失败: {url[:50]}...")
        else:
            items.append(a)

    return {
        "platform": "wechat",
        "sampleSize": len(items),
        "items": items,
        "errors": errors,
    }


def run(config: dict) -> dict:
    """Skill 标准入口"""
    return fetch_hot_articles(
        api_key=config["api_key"],
        count=config.get("count", 5),
        keywords=config.get("keywords"),
    )
