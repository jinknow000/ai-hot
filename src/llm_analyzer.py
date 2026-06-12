"""
LLM 分析引擎 - 结构化分析与机会评分
================================
将三平台采集数据打包发给 LLM，生成:
- dailySummary: 每日整体概述
- topPicks: 跨平台精选推荐 + 机会评分 (0-100)
- platformInsights: 各平台策略洞察
- contentAngles: 内容切入角度建议
- riskNotes: 风险提醒

机会评分机制:
1. 先根据关键词匹配度和互动数据算出基础分 (40-96)
2. LLM 在基础分上微调 (±10)
3. 确保评分有数据支撑，非随意打分
"""
import json
import os
import math
import re
from datetime import datetime
from typing import Optional


class LlmAnalyzer:
    """LLM 结构化分析引擎"""

    # 分析输出的 JSON Schema
    OUTPUT_SCHEMA = {
        "type": "object",
        "properties": {
            "dailySummary": {
                "type": "object",
                "properties": {
                    "totalCollected": {"type": "integer"},
                    "hotTopics": {"type": "array", "items": {"type": "string"}},
                    "overview": {"type": "string"},
                },
                "required": ["totalCollected", "hotTopics", "overview"],
            },
            "topPicks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "platform": {"type": "string"},
                        "opportunityScore": {"type": "integer", "minimum": 0, "maximum": 100},
                        "reason": {"type": "string"},
                        "contentAngle": {"type": "string"},
                        "riskNote": {"type": "string"},
                        "url": {"type": "string"},
                    },
                    "required": ["title", "platform", "opportunityScore", "reason"],
                },
            },
            "platformInsights": {
                "type": "object",
                "properties": {
                    "douyin": {"type": "string"},
                    "xiaohongshu": {"type": "string"},
                    "wechat": {"type": "string"},
                },
            },
            "contentAngles": {
                "type": "array",
                "items": {"type": "string"},
            },
            "riskNotes": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["dailySummary", "topPicks", "platformInsights"],
    }

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com",
                 model: str = "deepseek-v4-pro"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._client = None

    @property
    def client(self):
        """懒加载 OpenAI 兼容客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                raise RuntimeError(
                    "请安装 openai 库: pip install openai>=1.0.0"
                )
        return self._client

    def analyze(self, collect_result: dict,
                skill_contexts: Optional[dict] = None) -> dict:
        """
        对采集数据进行 LLM 结构化分析

        Args:
            collect_result: RedFoxCollector.collect_all() 的输出
            skill_contexts: Skill 参考文档上下文 (可选)

        Returns:
            结构化分析结果 dict
        """
        # Step 1: 预计算基础分 (40-96)
        base_scores = self._compute_base_scores(collect_result)

        # Step 2: 构建 LLM prompt
        prompt = self._build_prompt(collect_result, base_scores, skill_contexts)

        # Step 3: 调用 LLM
        try:
            llm_output = self._call_llm(prompt)
            # Step 4: 校验并修正分数
            validated = self._validate_and_correct(llm_output, base_scores)
            return validated
        except Exception as e:
            # LLM 调用失败 → 降级到模板生成
            return self._fallback_analysis(collect_result, base_scores, str(e))

    def _compute_base_scores(self, collect_result: dict) -> dict:
        """基于互动数据预计算每篇文章的基础分 (40-96)"""
        scores = {}

        for platform_name, platform_data in collect_result.get("platforms", {}).items():
            items = platform_data.get("items", [])
            if not items:
                continue

            # 提取互动数据计算基础分
            interaction_scores = []
            for item in items:
                if platform_name == "wechat":
                    reads = item.get("readCount", 0) or 1
                    interactions = (item.get("likeCount", 0) or 0) + \
                                   (item.get("wowCount", 0) or 0) + \
                                   (item.get("commentCount", 0) or 0) + \
                                   (item.get("shareCount", 0) or 0)
                    # 阅读量归一化 + 互动率
                    read_norm = min(math.log10(max(reads, 1)) / 6, 1.0)  # log10(1M)=6
                    interaction_rate = min(interactions / max(reads, 1) * 100, 1.0)
                    raw = read_norm * 50 + interaction_rate * 46
                elif platform_name == "douyin":
                    interactions = (item.get("likeCount", 0) or 0) * 0.3 + \
                                   (item.get("commentCount", 0) or 0) * 0.25 + \
                                   (item.get("shareCount", 0) or 0) * 0.25 + \
                                   (item.get("collectCount", 0) or 0) * 0.2
                    raw = min(math.log10(max(interactions, 1)) / 5 * 56 + 40, 96)
                else:  # xiaohongshu
                    interactions = (item.get("likeCount", 0) or 0) * 0.35 + \
                                   (item.get("collectCount", 0) or 0) * 0.35 + \
                                   (item.get("commentCount", 0) or 0) * 0.2 + \
                                   (item.get("shareCount", 0) or 0) * 0.1
                    raw = min(math.log10(max(interactions, 1)) / 5 * 56 + 40, 96)

                interaction_scores.append(raw)

            if interaction_scores:
                # 归一化到 40-96
                min_s, max_s = min(interaction_scores), max(interaction_scores)
                if max_s > min_s:
                    for i, item in enumerate(items):
                        key = item.get("workUrl") or item.get("title", "")
                        normalized = 40 + (interaction_scores[i] - min_s) / (max_s - min_s) * 56
                        scores[key] = round(min(max(normalized, 40), 96))
                else:
                    for item in items:
                        key = item.get("workUrl") or item.get("title", "")
                        scores[key] = 68  # 默认中等分

        return scores

    def _build_prompt(self, collect_result: dict, base_scores: dict,
                      skill_contexts: Optional[dict] = None) -> str:
        """构建 LLM 分析 prompt"""
        date = collect_result.get("date", "")
        platforms = collect_result.get("platforms", {})

        # 格式化平台数据为 markdown
        platform_sections = []
        for pname, pdata in platforms.items():
            items = pdata.get("items", [])
            platform_sections.append(f"\n### {pname} (共 {len(items)} 条)\n")
            for i, item in enumerate(items):
                key = item.get("workUrl") or item.get("title", "")
                bs = base_scores.get(key, 68)
                platform_sections.append(
                    f"**{i+1}. {item.get('title', '无标题')}**\n"
                    f"- 作者: {item.get('author', '未知')}\n"
                    f"- 平台: {pname}\n"
                    f"- 基础机会分: {bs}/100\n"
                    f"- 互动数据: {json.dumps({k: v for k, v in item.items() if 'Count' in k or 'count' in k}, ensure_ascii=False)}\n"
                    f"- URL: {item.get('workUrl', '')}\n"
                )

        skill_context_str = ""
        if skill_contexts:
            skill_context_str = "\n## Skill 参考上下文\n"
            for name, ctx in skill_contexts.items():
                skill_context_str += f"\n### {name}\n{ctx}\n"

        return f"""你是一位资深的新媒体内容策略分析师。请分析以下 {date} 的 AI 领域多平台热点数据，输出结构化分析结果。

## 数据来源
{''.join(platform_sections)}
{skill_context_str}

## 分析要求

### 1. dailySummary (每日摘要)
- totalCollected: 采集总量
- hotTopics: 3-5 个今日热点话题关键词
- overview: 100 字以内的整体概述

### 2. topPicks (精选推荐)
从数据中挑选 5-8 条最值得关注的内容，按机会评分降序。评分规则：
- 每个条目已给出基础机会分 (基于互动数据计算)，你可在 ±10 范围内微调
- reason: 为什么这条值得关注 (30 字以内)
- contentAngle: 建议的内容切入角度 (40 字以内)
- riskNote: 潜在风险提醒 (如时效性、争议性)

### 3. platformInsights (平台洞察)
- 每个平台 1-2 句话的策略洞察
- 分析该平台当前 AI 内容的趋势特点

### 4. contentAngles (内容角度)
- 3-5 个建议的内容切入角度

### 5. riskNotes (风险提醒)
- 2-3 个需要注意的整体风险

## 输出格式
严格输出以下 JSON，不要包含任何 markdown 代码块标记:
{json.dumps(self.OUTPUT_SCHEMA, ensure_ascii=False, indent=2)}
"""

    def _call_llm(self, prompt: str) -> dict:
        """调用 OpenAI 兼容 LLM API，返回解析后的 JSON dict

        三层容错机制:
        1. response_format 强制 JSON 输出（兼容 OpenAI/DeepSeek）
        2. 正则提取最外层 {...}（处理 markdown 包裹 / 多余文本）
        3. 解析失败时重试一次，将错误信息反馈给 LLM
        """
        messages = [
            {
                "role": "system",
                "content": "你是一个精准的数据分析引擎。请严格按照 JSON Schema 返回结构化分析结果，"
                           "不要包含任何额外文本或 markdown 标记。只输出纯 JSON。",
            },
            {"role": "user", "content": prompt},
        ]

        # 第 1 层: 尝试使用 response_format 强制 JSON 模式
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )
        except Exception:
            # 部分 API 不支持 response_format → 降级调用
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=4096,
            )

        content = response.choices[0].message.content.strip()

        # 第 2 层: JSON 提取（多策略）
        parsed = self._extract_json(content)
        if parsed is not None:
            return parsed

        # 第 3 层: 重试 — 将错误反馈给 LLM
        retry_messages = messages + [
            {"role": "assistant", "content": content},
            {"role": "user", "content": (
                "你返回的内容不是合法 JSON，无法被 json.loads() 解析。"
                "请检查是否有多余逗号、未闭合的引号或括号、或 markdown 包裹。"
                "请直接输出纯 JSON，不要包含 ``` 标记。"
            )},
        ]
        try:
            retry_response = self.client.chat.completions.create(
                model=self.model,
                messages=retry_messages,
                temperature=0.1,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )
        except Exception:
            retry_response = self.client.chat.completions.create(
                model=self.model,
                messages=retry_messages,
                temperature=0.1,
                max_tokens=4096,
            )

        retry_content = retry_response.choices[0].message.content.strip()
        parsed = self._extract_json(retry_content)
        if parsed is not None:
            return parsed

        # 重试仍然失败 → 抛出异常，由 analyze() 降级到模板
        raise ValueError(
            f"LLM 返回内容无法解析为 JSON，已重试 1 次。"
            f"原始内容前 200 字符: {content[:200]}"
        )

    def _extract_json(self, content: str) -> dict | None:
        """从 LLM 响应中提取 JSON 对象，返回 dict 或 None"""
        if not content:
            return None

        # 策略 1: 直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 策略 2: 去除 markdown 代码块标记后解析
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned)
            cleaned = re.sub(r'\n?\s*```\s*$', '', cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 策略 3: 正则提取最外层 {...}（处理前后有多余文本的情况）
        m = re.search(r'\{[\s\S]*\}', cleaned)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass

        # 策略 4: 修复常见 JSON 错误后重试
        fixed = self._repair_json(cleaned)
        if fixed:
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass

        return None

    @staticmethod
    def _repair_json(text: str) -> str | None:
        """尝试修复常见的 LLM 生成的 JSON 错误

        - 尾部多余逗号: {"a": 1,} → {"a": 1}
        - 数组尾部逗号: [1,2,] → [1,2]
        - 对象属性间缺少逗号: {"a":1\n"b":2} → {"a":1,\n"b":2}
        """
        if not text:
            return None

        repaired = text
        # 去除尾部逗号 (在 } 或 ] 之前)
        repaired = re.sub(r',\s*(\})', r'\1', repaired)
        repaired = re.sub(r',\s*(\])', r'\1', repaired)

        # 修复缺失逗号: value\n"key" → value,\n"key"（value 可以是 "str"/数字/bool/null/}]）
        repaired = re.sub(r'([\d}\]"\w])\s*\n\s*(")', r'\1,\n\2', repaired)

        if repaired != text:
            return repaired
        return None

    def _validate_and_correct(self, llm_output: dict,
                              base_scores: dict) -> dict:
        """校验 LLM 输出并修正分数"""
        # 修正机会评分: 确保在基础分 ±10 范围内
        for pick in llm_output.get("topPicks", []):
            title = pick.get("title", "")
            url = pick.get("url", "")
            key = url or title

            if key in base_scores:
                base = base_scores[key]
                llm_score = pick.get("opportunityScore", base)
                # 限制在 ±10
                corrected = max(40, min(96, llm_score))
                if abs(corrected - base) > 10:
                    corrected = base + (10 if corrected > base else -10)
                pick["opportunityScore"] = max(0, min(100, corrected))
            else:
                pick["opportunityScore"] = max(0, min(100,
                    pick.get("opportunityScore", 70)))

        # 确保 dailySummary 有 overview
        if "dailySummary" in llm_output:
            llm_output["dailySummary"].setdefault("totalCollected", 0)
            llm_output["dailySummary"].setdefault("hotTopics", [])
            llm_output["dailySummary"].setdefault("overview", "")

        return llm_output

    def _fallback_analysis(self, collect_result: dict, base_scores: dict,
                           error_msg: str) -> dict:
        """LLM 失败时的模板生成降级方案"""
        date = collect_result.get("date", "")
        platforms = collect_result.get("platforms", {})

        # 合并所有 item
        all_items = []
        for pname, pdata in platforms.items():
            for item in pdata.get("items", []):
                key = item.get("workUrl") or item.get("title", "")
                item["_platform"] = pname
                item["_baseScore"] = base_scores.get(key, 68)
                all_items.append(item)

        # 按基础分排序
        all_items.sort(key=lambda x: x.get("_baseScore", 0), reverse=True)

        total = sum(p.get("sampleSize", 0) for p in platforms.values())

        return {
            "dailySummary": {
                "totalCollected": total,
                "hotTopics": [item.get("title", "")[:20] for item in all_items[:5]],
                "overview": f"{date} 共采集 {total} 条 AI 相关数据。"
                           f"(LLM 分析暂不可用: {error_msg})",
            },
            "topPicks": [
                {
                    "title": item.get("title", ""),
                    "platform": item.get("_platform", ""),
                    "opportunityScore": item.get("_baseScore", 70),
                    "reason": "基于互动数据自动推荐",
                    "contentAngle": "可结合自身领域做深度解读",
                    "riskNote": "请人工核实内容质量",
                    "url": item.get("workUrl", ""),
                }
                for item in all_items[:8]
            ],
            "platformInsights": {
                pname: f"今日采集 {pdata.get('sampleSize', 0)} 条数据"
                for pname, pdata in platforms.items()
            },
            "contentAngles": [
                "AI 工具使用教程与评测",
                "大模型行业应用案例",
                "AI 编程效率提升实践",
            ],
            "riskNotes": [
                f"LLM 分析引擎异常: {error_msg}，当前为模板生成结果",
                "建议人工审核推荐内容的相关性和时效性",
            ],
        }
