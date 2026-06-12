#!/usr/bin/env python3
"""Gitee CI 入口——禁用以避免与 shell 步骤冲突"""
import sys
print("✅ 跳过 Python 插件，流水线由 shell 步骤执行")
sys.exit(0)
