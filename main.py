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

# 部署到 Cloudflare Pages
DIST = ROOT / "dist" / "index.html"
if DIST.exists():
    import subprocess
    os.environ["CLOUDFLARE_API_TOKEN"] = "cfut_B1bH5ayOog5t5virlh2zrK31YAvUxud2WuZAcE6qd71515b0"
    os.environ["CLOUDFLARE_ACCOUNT_ID"] = "5831b786b959cfc2fcd5a273fb5bbc7d"

    print("[deploy] 安装 wrangler...")
    subprocess.run(["npm", "install", "-g", "wrangler", "--quiet"], check=True)

    print("[deploy] 部署到 Cloudflare Pages...")
    subprocess.run([
        "npx", "wrangler", "pages", "deploy", str(ROOT / "dist"),
        "--project-name=ai-hot", "--commit-dirty=true"
    ], check=True, cwd=str(ROOT))

    print("[deploy] 完成: https://ai-hot.pages.dev")
else:
    print("[deploy] dist/index.html 不存在，跳过部署")
    sys.exit(1)
