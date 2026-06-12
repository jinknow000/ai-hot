#!/usr/bin/env python3
"""Gitee CI 主入口 — 完整流水线: 采集 → LLM 分析 → 构建站点"""
import os
import sys
from pathlib import Path
from datetime import datetime

# 项目根
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# 环境变量
os.environ.setdefault("REDFOX_API_KEY", "ak_31fa2c7b257c47fab7f84229da48f247")
os.environ.setdefault("LLM_API_KEY", "sk-T-BGJJiZO338gkWaPVOywA")
os.environ.setdefault("LLM_BASE_URL", "https://yx-api.yixiong-tech.com/openai/v1")
os.environ.setdefault("LLM_MODEL", "deepseek-v4-pro")

DATE = os.environ.get("DATE", datetime.now().strftime("%Y-%m-%d"))
print(f"[main.py] 采集日期: {DATE}")

from src.run_daily_agent import main as run_pipeline

# 构造命令行参数
sys.argv = ["main.py", "--date", DATE]

run_pipeline()
