#!/usr/bin/env python3
"""Gitee CI 入口: 采集 -> LLM 分析 -> Cloudflare Pages 部署"""
import os, sys, subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("REDFOX_API_KEY", "ak_31fa2c7b257c47fab7f84229da48f247")
os.environ.setdefault("LLM_API_KEY", "sk-T-BGJJiZO338gkWaPVOywA")
os.environ.setdefault("LLM_BASE_URL", "https://yx-api.yixiong-tech.com/openai/v1")
os.environ.setdefault("LLM_MODEL", "deepseek-v4-pro")

DATE = os.environ.get("DATE", datetime.now().strftime("%Y-%m-%d"))
print(f"[main.py] {DATE}")

from src.run_daily_agent import main as run_pipeline
sys.argv = ["main.py", "--date", DATE]

# Step 1: 采集 + 分析 + 构建
try:
    run_pipeline()
except SystemExit as e:
    if e.code is not None and e.code != 0:
        print(f"[main.py] 流水线失败, exit={e.code}")
        sys.exit(e.code)

# Step 2: 部署
DIST = ROOT / "dist" / "index.html"
if not DIST.exists():
    print("[main.py] dist/index.html 不存在")
    sys.exit(1)

os.environ["CLOUDFLARE_API_TOKEN"] = "cfut_B1bH5ayOog5t5virlh2zrK31YAvUxud2WuZAcE6qd71515b0"
os.environ["CLOUDFLARE_ACCOUNT_ID"] = "5831b786b959cfc2fcd5a273fb5bbc7d"

print("[main.py] 安装 wrangler...")
subprocess.run(["npm", "install", "-g", "wrangler"], check=False, capture_output=True)

print("[main.py] 部署到 Cloudflare Pages...")
r = subprocess.run(
    ["npx", "wrangler", "pages", "deploy", str(ROOT / "dist"),
     "--project-name=ai-hot", "--commit-dirty=true"],
    check=False, capture_output=True, text=True, cwd=str(ROOT)
)
print(r.stdout)
if r.returncode != 0:
    print(r.stderr)
    sys.exit(1)

print("[main.py] 部署完成: https://ai-hot.pages.dev")
