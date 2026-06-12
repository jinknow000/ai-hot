#!/usr/bin/env python3
"""Gitee CI 入口——流水线在 shell 步骤中已执行，此处仅返回成功"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist" / "index.html"

if DIST.exists():
    print(f"✅ 站点已存在: {DIST}")
    sys.exit(0)
else:
    print("⚠️ dist/index.html 不存在，尝试执行完整流水线...")
    sys.path.insert(0, str(ROOT))
    from src.run_daily_agent import main
    main()
