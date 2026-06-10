"""
数据校验器 - JSON 字段验证与长度检查
==================================
确保采集数据和 LLM 分析结果的数据质量和字段完整性。
"""
import json
from typing import Any, Optional


class Validator:
    """数据校验器

    校验规则:
    - 必填字段检查
    - 字段类型检查
    - 字符串长度限制
    - 数值范围检查
    """

    # 各阶段输出 Schema
    COLLECT_ITEM_SCHEMA = {
        "title": {"type": str, "max_len": 200},
        "author": {"type": str, "max_len": 100},
        "workUrl": {"type": str, "max_len": 500},
    }

    ANALYSIS_SCHEMA = {
        "dailySummary": {"type": dict, "required": True},
        "topPicks": {"type": list, "required": True, "max_len": 10},
        "platformInsights": {"type": dict, "required": True},
        "contentAngles": {"type": list, "max_len": 10},
        "riskNotes": {"type": list, "max_len": 10},
    }

    TOP_PICK_SCHEMA = {
        "title": {"type": str, "max_len": 200},
        "platform": {"type": str, "max_len": 50},
        "opportunityScore": {"type": int, "min": 0, "max": 100},
        "reason": {"type": str, "max_len": 200},
    }

    def validate_collect_result(self, data: dict) -> tuple[bool, list[str]]:
        """校验采集结果"""
        errors = []

        if not isinstance(data, dict):
            return False, ["采集结果必须是 dict"]

        if "date" not in data:
            errors.append("缺少 date 字段")

        platforms = data.get("platforms", {})
        if not platforms:
            errors.append("platforms 为空，没有采集到任何平台数据")

        for pname, pdata in platforms.items():
            if not isinstance(pdata, dict):
                errors.append(f"平台 {pname} 数据格式错误")
                continue

            items = pdata.get("items", [])
            if not isinstance(items, list):
                errors.append(f"平台 {pname} items 必须是 list")
                continue

            for i, item in enumerate(items):
                for field, rules in self.COLLECT_ITEM_SCHEMA.items():
                    value = item.get(field)
                    if value is None:
                        continue  # 选填字段
                    if not isinstance(value, rules["type"]):
                        errors.append(
                            f"平台 {pname} 第 {i+1} 条: "
                            f"{field} 类型错误，期望 {rules['type'].__name__}"
                        )
                    elif "max_len" in rules and len(str(value)) > rules["max_len"]:
                        errors.append(
                            f"平台 {pname} 第 {i+1} 条: "
                            f"{field} 超长 ({len(str(value))} > {rules['max_len']})"
                        )

        return len(errors) == 0, errors

    def validate_analysis_result(self, data: dict) -> tuple[bool, list[str]]:
        """校验 LLM 分析结果"""
        errors = []

        if not isinstance(data, dict):
            return False, ["分析结果必须是 dict"]

        # 检查必填字段
        for field, rules in self.ANALYSIS_SCHEMA.items():
            if rules.get("required") and field not in data:
                errors.append(f"分析结果缺少必填字段: {field}")
                continue

            value = data.get(field)
            if value is None:
                continue

            if not isinstance(value, rules["type"]):
                errors.append(
                    f"字段 {field} 类型错误: "
                    f"期望 {rules['type'].__name__}, 实际 {type(value).__name__}"
                )
            elif "max_len" in rules and len(value) > rules["max_len"]:
                errors.append(
                    f"字段 {field} 超长: {len(value)} > {rules['max_len']}"
                )

        # 校验 topPicks 条目
        for i, pick in enumerate(data.get("topPicks", [])):
            for field, rules in self.TOP_PICK_SCHEMA.items():
                value = pick.get(field)
                if value is None:
                    continue
                if not isinstance(value, rules["type"]):
                    errors.append(
                        f"topPicks[{i}].{field} 类型错误: "
                        f"期望 {rules['type'].__name__}"
                    )
                elif "max_len" in rules and len(str(value)) > rules["max_len"]:
                    errors.append(
                        f"topPicks[{i}].{field} 超长"
                    )
                elif "min" in rules and value < rules["min"]:
                    errors.append(
                        f"topPicks[{i}].{field} 值 {value} < {rules['min']}"
                    )
                elif "max" in rules and value > rules["max"]:
                    errors.append(
                        f"topPicks[{i}].{field} 值 {value} > {rules['max']}"
                    )

        return len(errors) == 0, errors

    def validate_site_data(self, data: dict) -> tuple[bool, list[str]]:
        """校验最终站点数据 (采集 + 分析 合并后的完整数据)"""
        errors = []

        # 检查顶层结构
        required_top = ["date", "platforms", "analysis", "meta"]
        for field in required_top:
            if field not in data:
                errors.append(f"站点数据缺少顶层字段: {field}")

        # 检查每个平台至少有 sampleSize
        for pname, pdata in data.get("platforms", {}).items():
            if "sampleSize" not in pdata:
                errors.append(f"平台 {pname} 缺少 sampleSize")

        # 检查分析结果不为空
        analysis = data.get("analysis", {})
        if not analysis.get("topPicks"):
            errors.append("分析结果 topPicks 为空，站点将无内容展示")

        return len(errors) == 0, errors
