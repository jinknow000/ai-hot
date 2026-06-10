"""
Skills 加载器 - 三层加载机制
===========================
读取 skills/ 目录下的 SKILL.md 文件，解析元数据和执行配置。
支持同名 Skill 覆盖和热重载。
"""
import os
import re
import json
from pathlib import Path
from typing import Optional


class SkillLoader:
    """Agent Skills 加载器

    三层加载机制:
    1. 读取 SKILL.md → 解析元数据和决策逻辑
    2. 加载 scripts/ 下的 Python 采集脚本
    3. 加载 references/ 下的参考文档 (注入 LLM prompt)
    """

    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self._cache: dict[str, dict] = {}

    def load_all(self) -> dict[str, dict]:
        """加载所有 Skills，返回 {skill_name: skill_config}"""
        if not self.skills_dir.exists():
            return {}

        skills = {}
        for skill_dir in sorted(self.skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_config = self.load_one(skill_dir.name)
            if skill_config:
                skills[skill_dir.name] = skill_config

        return skills

    def load_one(self, skill_name: str) -> Optional[dict]:
        """加载单个 Skill"""
        # 缓存检查
        if skill_name in self._cache:
            return self._cache[skill_name]

        skill_dir = self.skills_dir / skill_name
        if not skill_dir.is_dir():
            return None

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            return None

        config = {
            "name": skill_name,
            "dir": str(skill_dir),
            "metadata": {},
            "scripts": [],
            "references": [],
            "raw_md": "",
        }

        # Layer 1: 解析 SKILL.md
        raw_content = skill_md.read_text(encoding="utf-8")
        config["raw_md"] = raw_content
        config["metadata"] = self._parse_metadata(raw_content)

        # Layer 2: 加载 scripts
        scripts_dir = skill_dir / "scripts"
        if scripts_dir.is_dir():
            for script_file in sorted(scripts_dir.glob("*.py")):
                config["scripts"].append({
                    "name": script_file.stem,
                    "path": str(script_file),
                    "content": script_file.read_text(encoding="utf-8"),
                })

        # Layer 3: 加载 references
        refs_dir = skill_dir / "references"
        if refs_dir.is_dir():
            for ref_file in sorted(refs_dir.glob("*")):
                if ref_file.suffix in (".md", ".txt", ".json"):
                    config["references"].append({
                        "name": ref_file.name,
                        "path": str(ref_file),
                        "content": ref_file.read_text(encoding="utf-8"),
                    })

        self._cache[skill_name] = config
        return config

    def _parse_metadata(self, raw_md: str) -> dict:
        """从 SKILL.md 提取元数据"""
        metadata = {}

        # 提取标题 (# 开头)
        title_match = re.search(r'^#\s+(.+)$', raw_md, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        # 提取 YAML-like 字段 (**字段**: 值)
        field_pattern = r'\*\*([^*]+)\*\*:\s*(.+)'
        for match in re.finditer(field_pattern, raw_md):
            key = match.group(1).strip()
            value = match.group(2).strip()
            metadata[key] = value

        # 提取平台信息
        platform_match = re.search(r'平台[：:]\s*(.+)', raw_md)
        if platform_match:
            metadata["platform"] = platform_match.group(1).strip()

        # 提取 API 端点
        endpoints = re.findall(r'`(POST|GET)\s+(https://[^`]+)`', raw_md)
        metadata["api_endpoints"] = [
            {"method": m, "url": u} for m, u in endpoints
        ]

        # 提取关键词
        kw_section = re.search(r'关键词[：:]\s*(.+?)(?:\n|$)', raw_md)
        if kw_section:
            metadata["keywords"] = [
                kw.strip() for kw in kw_section.group(1).split("、")
            ]

        return metadata

    def get_exec_script(self, skill_name: str) -> Optional[str]:
        """获取 Skill 的执行脚本路径 (第一个 .py)"""
        config = self.load_one(skill_name)
        if config and config["scripts"]:
            return config["scripts"][0]["path"]
        return None

    def get_reference_context(self, skill_name: str) -> str:
        """获取 Skill 的参考文档内容 (用于注入 LLM prompt)"""
        config = self.load_one(skill_name)
        if not config or not config["references"]:
            return ""

        parts = []
        for ref in config["references"]:
            parts.append(f"--- {ref['name']} ---\n{ref['content']}")
        return "\n\n".join(parts)

    def clear_cache(self):
        """清除缓存 (热重载)"""
        self._cache.clear()

    def reload(self, skill_name: str) -> Optional[dict]:
        """热重载单个 Skill"""
        self._cache.pop(skill_name, None)
        return self.load_one(skill_name)
