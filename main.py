#!/usr/bin/env python3
"""Gitee CI 入口——代理到 src.run_daily_agent"""
import sys
from src.run_daily_agent import main

if __name__ == "__main__":
    sys.argv[0] = "python -m src.run_daily_agent"
    main()
