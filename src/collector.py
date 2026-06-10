"""
RedFox 数据采集器 - 多平台并行采集
==============================
负责调用 RedFox API 采集抖音、小红书、公众号三平台数据。
- 并行采集，单平台失败不阻塞其他平台
- 多关键词轮询 + 去重
- API 调用限速 (0.15-0.25s 延迟)
- 平台级容错 + 备用 Skill 降级
"""
import json
import time
import random
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional

from .skill_loader import SkillLoader

REDFOX_BASE = "https://redfox.hk/story/api"
SIXTYS_API_BASE = "https://60s.viki.moe/v2"
REQUEST_DELAY_MIN = 0.15
REQUEST_DELAY_MAX = 0.25
TIMEOUT = 30

# AI 话题过滤关键词 (用于抖音热搜过滤)
AI_FILTER_KEYWORDS = [
    "AI", "人工智能", "大模型", "ChatGPT", "GPT", "Claude", "Gemini",
    "DeepSeek", "Kimi", "文心", "通义", "智能体", "Agent", "AIGC",
    "机器学习", "深度学习", "神经网络", "LLM", "OpenAI", "Copilot",
    "Cursor", "Codex", "Midjourney", "Stable Diffusion", "Sora",
    "豆包", "元宝", "千问", "百川", "智谱", "讯飞", "商汤",
    "自动驾驶", "机器人", "具身智能", "AI绘画", "AI视频", "AI编程",
    "AI写作", "AI搜索", "AI音乐", "AI教育", "AI医疗",
]


class RedFoxCollector:
    """红狐数据多平台采集器"""

    # 三平台采集配置
    # 公众号: RedFox API 关键词搜索
    # 抖音: 60s API 热搜榜 + AI 关键词过滤
    # 小红书: 暂无可用免费 API (RedFox xhsData 仅支持按 ID 查询)
    PLATFORM_CONFIG = {
        "douyin": {
            "skill": "douyin-search",
            "api_prefix": "dyData",
            "keywords": ["AI"],
            "count": 5,
            "data_source": "60s-api",  # RedFox 不支持抖音搜索，改用 60s API
        },
        "xiaohongshu": {
            "skill": "xiaohongshu-weeklytop",
            "api_prefix": "xhsData",
            "keywords": ["AI工具", "AI编程", "AI智能体", "Agent", "大模型"],
            "count": 5,
            "data_source": "none",  # 小红书暂无可用免费搜索 API
        },
        "wechat": {
            "skill": "wechat-10w-hot",
            "api_prefix": "gzhData",
            "keywords": ["AI工具", "AI编程", "AI智能体", "Agent", "大模型"],
            "count": 5,
            "data_source": "redfox",   # RedFox searchArticle 可用
        },
    }

    def __init__(self, api_key: str, skills_dir: str = "skills"):
        self.api_key = api_key
        self.skill_loader = SkillLoader(skills_dir)

    def collect_all(self, date: Optional[str] = None) -> dict:
        """并行采集三平台数据

        Returns:
            {
                "date": "2026-06-09",
                "platforms": {
                    "douyin": {...},
                    "xiaohongshu": {...},
                    "wechat": {...}
                },
                "errors": [...],
                "collectStats": {...}
            }
        """
        date = date or datetime.now().strftime("%Y-%m-%d")
        results = {
            "date": date,
            "platforms": {},
            "errors": [],
            "collectStats": {
                "startTime": datetime.now().isoformat(),
                "platformStats": {},
            },
        }

        # 并行采集
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self._collect_platform, name, config, date): name
                for name, config in self.PLATFORM_CONFIG.items()
            }

            for future in as_completed(futures):
                name = futures[future]
                try:
                    result = future.result()
                    results["platforms"][name] = result
                    results["collectStats"]["platformStats"][name] = {
                        "sampleSize": result.get("sampleSize", 0),
                        "errorCount": len(result.get("errors", [])),
                    }
                except Exception as e:
                    results["platforms"][name] = {
                        "platform": name,
                        "sampleSize": 0,
                        "items": [],
                        "errors": [str(e)],
                    }
                    results["errors"].append(f"{name} 采集失败: {e}")

        results["collectStats"]["endTime"] = datetime.now().isoformat()
        total_items = sum(
            p.get("sampleSize", 0) for p in results["platforms"].values()
        )
        results["collectStats"]["totalItems"] = total_items

        return results

    def _collect_platform(self, name: str, config: dict, date: str) -> dict:
        """采集单个平台数据"""
        errors = []

        # 加载 Skill 配置
        skill_config = self.skill_loader.load_one(config["skill"])

        # 尝试执行 Skill 脚本
        try:
            exec_script = config.get("exec_script") or (
                self.skill_loader.get_exec_script(config["skill"])
            )
            if exec_script:
                result = self._run_skill_script(exec_script, config)
                # Skill 成功但无数据时，继续尝试降级方案
                if result.get("sampleSize", 0) > 0:
                    return result
                errors.extend(result.get("errors", []))
        except Exception as e:
            errors.append(f"Skill 脚本执行失败: {e}, 降级到内置采集")

        # 降级: 使用内置采集逻辑
        return self._fallback_collect(name, config, errors)

    def _run_skill_script(self, script_path: str, config: dict) -> dict:
        """动态加载并运行 Skill 脚本"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("skill_module", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "run"):
            return module.run({
                "api_key": self.api_key,
                "keyword": config.get("keywords", ["AI"])[0],
                "keywords": config.get("keywords"),
                "count": config.get("count", 5),
            })

        # 尝试直接调用 fetch 函数
        for attr_name in dir(module):
            if attr_name.startswith("fetch_"):
                func = getattr(module, attr_name)
                return func(
                    api_key=self.api_key,
                    count=config.get("count", 5),
                    keyword=config.get("keywords", ["AI"])[0],
                )

        raise RuntimeError(f"Skill 脚本无 run() 入口: {script_path}")

    def _fallback_collect(self, platform: str, config: dict,
                          errors: list) -> dict:
        """内置降级采集逻辑 (不依赖 Skill 脚本)"""
        if platform == "wechat":
            return self._collect_wechat_fallback(config, errors)
        elif platform == "douyin":
            return self._collect_douyin_fallback(config, errors)
        elif platform == "xiaohongshu":
            return self._collect_xhs_fallback(config, errors)
        return {
            "platform": platform,
            "sampleSize": 0,
            "items": [],
            "errors": errors,
        }

    def _collect_wechat_fallback(self, config: dict, errors: list) -> dict:
        """公众号采集降级方案"""
        items = []
        keywords = config.get("keywords", ["AI工具"])

        for kw in keywords[:3]:  # 降级只查 3 个词
            result = self._api_post("gzhData/searchArticle", {
                "keyword": kw,
                "offset": 0,
                "sortType": "_4",
            })
            if result.get("code") == 2000:
                articles = result.get("data", {}).get("list", [])
                for a in articles:
                    if (a.get("readCount", 0) or 0) >= 100000:
                        items.append({
                            "title": a.get("title", ""),
                            "author": a.get("author", ""),
                            "readCount": a.get("readCount", 0),
                            "likeCount": a.get("likeCount", 0),
                            "wowCount": a.get("wowCount", 0),
                            "commentCount": a.get("commentCount", 0),
                            "shareCount": a.get("shareCount", 0),
                            "publishTime": a.get("publishTime", ""),
                            "workUrl": a.get("workUrl", ""),
                        })
            else:
                errors.append(f"公众号降级搜索 '{kw}' 失败: {result.get('msg')}")
            time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))

        # 去重 + 排序
        seen = set()
        unique_items = []
        for item in items:
            url = item.get("workUrl", "")
            if url and url not in seen:
                seen.add(url)
                unique_items.append(item)

        unique_items.sort(key=lambda x: x.get("readCount", 0) or 0, reverse=True)

        return {
            "platform": "wechat",
            "sampleSize": min(len(unique_items), 5),
            "items": unique_items[:5],
            "errors": errors,
        }

    def _collect_douyin_fallback(self, config: dict, errors: list) -> dict:
        """抖音采集方案 - 使用 60s API 获取抖音热搜榜，AI 关键词过滤"""
        return self._collect_from_60s_api(
            platform="douyin",
            endpoint="/douyin",
            count=config.get("count", 5),
            errors=errors,
        )

    def _collect_from_60s_api(self, platform: str, endpoint: str,
                               count: int, errors: list) -> dict:
        """从 60s API 拉取热搜数据，过滤 AI 相关话题

        60s API (https://github.com/vikiboss/60s) 是一个开源免费的热搜聚合 API。
        返回各平台实时热搜榜，无认证、无请求限制。
        """
        url = f"{SIXTYS_API_BASE}{endpoint}"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "AI-Hot-Radar/1.0"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:300]
            errors.append(f"60s API HTTP {e.code}: {body}")
            return {"platform": platform, "sampleSize": 0, "items": [], "errors": errors}
        except Exception as e:
            errors.append(f"60s API 请求失败: {e}")
            return {"platform": platform, "sampleSize": 0, "items": [], "errors": errors}

        # 解析响应
        topics = result.get("data", [])
        if not isinstance(topics, list) or not topics:
            errors.append(f"60s API 返回空数据: {json.dumps(result, ensure_ascii=False)[:200]}")
            return {"platform": platform, "sampleSize": 0, "items": [], "errors": errors}

        # AI 关键词过滤
        ai_items = []
        for topic in topics:
            title = topic.get("title", "")
            if self._is_ai_related(title):
                ai_items.append({
                    "title": title,
                    "platform": platform,
                    "hotValue": topic.get("hot_value", 0),
                    "coverUrl": topic.get("cover", ""),
                    "workUrl": topic.get("link", ""),
                    "eventTime": topic.get("event_time", ""),
                    "source": "60s-api",
                })

        # 按热度值降序
        ai_items.sort(key=lambda x: x.get("hotValue", 0) or 0, reverse=True)

        return {
            "platform": platform,
            "sampleSize": min(len(ai_items), count),
            "items": ai_items[:count],
            "errors": errors if ai_items else errors + ["60s API 未找到 AI 相关话题"],
        }

    @staticmethod
    def _is_ai_related(title: str) -> bool:
        """判断标题是否包含 AI 相关关键词"""
        title_lower = title.lower()
        for kw in AI_FILTER_KEYWORDS:
            if kw.lower() in title_lower:
                return True
        return False

    def _collect_xhs_fallback(self, config: dict, errors: list) -> dict:
        """小红书采集降级方案 - RedFox 小红书 API 仅支持按 ID 查询"""
        # 当前 RedFox API 的 xhsData 仅支持 queryAccount/queryWork，
        # 不提供关键词搜索。
        return {
            "platform": "xiaohongshu",
            "sampleSize": 0,
            "items": [],
            "errors": errors + ["小红书搜索 API 暂不可用（RedFox xhsData 仅支持按 ID 查询，不支持关键词搜索）"],
        }

    def _api_post(self, endpoint: str, body: dict) -> dict:
        """统一的 API POST 请求"""
        url = f"{REDFOX_BASE}/{endpoint}"
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "X-API-KEY": self.api_key,
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
