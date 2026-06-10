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
REQUEST_DELAY_MIN = 0.15
REQUEST_DELAY_MAX = 0.25
TIMEOUT = 30


class RedFoxCollector:
    """红狐数据多平台采集器"""

    # 三平台采集配置
    PLATFORM_CONFIG = {
        "douyin": {
            "skill": "douyin-search",
            "api_prefix": "dyData",
            "keywords": ["AI"],
            "count": 5,
        },
        "xiaohongshu": {
            "skill": "xiaohongshu-weeklytop",
            "api_prefix": "xhsData",
            "keywords": ["AI工具", "AI编程", "AI智能体", "Agent", "大模型"],
            "count": 5,
        },
        "wechat": {
            "skill": "wechat-10w-hot",
            "api_prefix": "gzhData",
            "keywords": ["AI工具", "AI编程", "AI智能体", "Agent", "大模型"],
            "count": 5,
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
                return self._run_skill_script(exec_script, config)
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
        """抖音采集降级方案"""
        items = []
        kw = config.get("keywords", ["AI"])[0]

        result = self._api_post("dyData/search", {
            "keyword": kw,
            "offset": 0,
            "count": 10,
        })

        if result.get("code") == 2000:
            works = result.get("data", {}).get("list", [])
            for w in works[:5]:
                items.append({
                    "title": w.get("title", ""),
                    "author": w.get("author", ""),
                    "likeCount": w.get("likeCount", 0),
                    "commentCount": w.get("commentCount", 0),
                    "shareCount": w.get("shareCount", 0),
                    "collectCount": w.get("collectCount", 0),
                    "commentHotWords": w.get("commentHotWords", []),
                    "coverUrl": w.get("coverUrl", ""),
                    "workUrl": w.get("workUrl", ""),
                })
        else:
            errors.append(f"抖音降级搜索失败: {result.get('msg')}")

        return {
            "platform": "douyin",
            "sampleSize": len(items),
            "items": items,
            "errors": errors,
        }

    def _collect_xhs_fallback(self, config: dict, errors: list) -> dict:
        """小红书采集降级方案"""
        items = []
        keywords = config.get("keywords", ["AI工具"])

        for kw in keywords[:3]:
            result = self._api_post("xhsData/searchNote", {
                "keyword": kw,
                "sortType": "hot",
                "count": 10,
            })
            if result.get("code") == 2000:
                notes = result.get("data", {}).get("list", [])
                for n in notes:
                    items.append({
                        "title": n.get("title", ""),
                        "author": n.get("author", ""),
                        "likeCount": n.get("likeCount", 0),
                        "collectCount": n.get("collectCount", 0),
                        "commentCount": n.get("commentCount", 0),
                        "shareCount": n.get("shareCount", 0),
                        "coverUrl": n.get("coverUrl", ""),
                        "workUrl": n.get("workUrl", ""),
                    })
            else:
                errors.append(f"小红书降级搜索 '{kw}' 失败: {result.get('msg')}")
            time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))

        # 去重
        seen = set()
        unique_items = []
        for item in items:
            url = item.get("workUrl", "")
            if url and url not in seen:
                seen.add(url)
                unique_items.append(item)

        # 按互动量排序
        def _score(i):
            return (i.get("likeCount", 0) or 0) * 0.35 + \
                   (i.get("collectCount", 0) or 0) * 0.35 + \
                   (i.get("commentCount", 0) or 0) * 0.2 + \
                   (i.get("shareCount", 0) or 0) * 0.1
        unique_items.sort(key=_score, reverse=True)

        return {
            "platform": "xiaohongshu",
            "sampleSize": min(len(unique_items), 5),
            "items": unique_items[:5],
            "errors": errors,
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
