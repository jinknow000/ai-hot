#!/usr/bin/env python3
"""
AI 热点雷达 - 每日自动化 Agent 入口
==================================
DailyAihotAgentRunner 主流程:
1. SkillLoader 加载 SKILL.md / references
2. RedFoxCollector 并行采集三平台数据
3. LlmAnalyzer 调 LLM 生成结构化分析
4. Validator 校验 JSON 字段和长度
5. SiteBuilder 生成 HTML / JSON

用法:
    # 完整运行
    python -m src.run_daily_agent

    # 指定日期
    python -m src.run_daily_agent --date 2026-06-09

    # 仅采集 (跳过 LLM 分析)
    python -m src.run_daily_agent --collect-only

    # 仅分析 (使用已有数据)
    python -m src.run_daily_agent --analyze-only --data dist/data/latest.json

环境变量:
    REDFOX_API_KEY: 红狐数据 API Key (必须)
    LLM_API_KEY: LLM API Key (必须，除非 --collect-only)
    LLM_BASE_URL: LLM API 地址 (默认 https://api.deepseek.com)
    LLM_MODEL: LLM 模型 (默认 deepseek-chat)
"""
import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Windows 控制台 UTF-8 编码修复
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.skill_loader import SkillLoader
from src.collector import RedFoxCollector
from src.llm_analyzer import LlmAnalyzer
from src.validator import Validator
from src.site_builder import SiteBuilder


def main():
    parser = argparse.ArgumentParser(
        description="AI 热点雷达 - 每日自动化 Agent"
    )
    parser.add_argument("--date", help="日期 YYYY-MM-DD (默认今天)")
    parser.add_argument("--collect-only", action="store_true", help="仅采集，跳过 LLM 分析")
    parser.add_argument("--analyze-only", action="store_true", help="仅分析，使用已有数据")
    parser.add_argument("--data", help="已有数据文件路径 (配合 --analyze-only)")
    parser.add_argument("--skills-dir", default="skills", help="Skills 目录")
    parser.add_argument("--dist-dir", default="dist", help="输出目录")
    parser.add_argument("--output", help="输出 JSON 文件路径")
    args = parser.parse_args()

    date = args.date or datetime.now().strftime("%Y-%m-%d")
    print(f"\n{'='*60}")
    print(f"  AI 热点雷达 - DailyAihotAgentRunner")
    print(f"  日期: {date}")
    print(f"{'='*60}\n")

    # ====== Phase 1: 加载 Skills ======
    print("[Phase 1/5] 加载 Agent Skills...")
    skill_loader = SkillLoader(args.skills_dir)
    all_skills = skill_loader.load_all()
    print(f"  已加载 {len(all_skills)} 个 Skills:")
    for name, cfg in all_skills.items():
        title = cfg.get("metadata", {}).get("title", name)
        scripts_count = len(cfg.get("scripts", []))
        refs_count = len(cfg.get("references", []))
        print(f"    - {name}: {title} ({scripts_count} scripts, {refs_count} refs)")

    # ====== Phase 2: 数据采集 ======
    if args.analyze_only:
        print("\n[Phase 2/5] 跳过采集 (--analyze-only)")
        if not args.data or not Path(args.data).exists():
            print("  ❌ 需要 --data 指定已有的数据文件", file=sys.stderr)
            sys.exit(1)
        with open(args.data, encoding="utf-8") as f:
            collect_result = json.load(f)
        print(f"  已加载数据: {args.data}")
    else:
        print("\n[Phase 2/5] 并行采集三平台数据...")
        api_key = os.getenv("REDFOX_API_KEY")
        if not api_key:
            print("  ⚠️ REDFOX_API_KEY 未设置，使用模拟数据模式")
            collect_result = _mock_collect(date)
        else:
            collector = RedFoxCollector(api_key, args.skills_dir)
            collect_result = collector.collect_all(date)

        # 校验采集结果
        validator = Validator()
        valid, errors = validator.validate_collect_result(collect_result)
        if not valid:
            print("  ⚠️ 采集结果校验警告:")
            for e in errors:
                print(f"    - {e}")

        total = collect_result.get("collectStats", {}).get("totalItems", 0)
        print(f"  采集完成: 共 {total} 条")
        for pname, pdata in collect_result.get("platforms", {}).items():
            print(f"    {pname}: {pdata.get('sampleSize', 0)} 条, "
                  f"错误 {len(pdata.get('errors', []))} 个")

        # 保存采集原始数据
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(collect_result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"  原始数据已保存: {args.output}")

    # ====== Phase 3: LLM 分析 ======
    if args.collect_only:
        print("\n[Phase 3/5] 跳过 LLM 分析 (--collect-only)")
        analysis_result = _mock_analysis(collect_result)
    else:
        print("\n[Phase 3/5] LLM 结构化分析...")
        llm_api_key = os.getenv("LLM_API_KEY")
        if not llm_api_key:
            print("  ⚠️ LLM_API_KEY 未设置，使用模板分析")
            analysis_result = _mock_analysis(collect_result)
        else:
            # 构建 Skill 上下文
            skill_contexts = {}
            for name, cfg in all_skills.items():
                ctx = f"## {cfg['metadata'].get('title', name)}\n\n"
                ctx += cfg.get("raw_md", "")[:2000]  # 前 2000 字符
                for ref in cfg.get("references", [])[:1]:
                    ctx += f"\n\n### {ref['name']}\n{ref['content'][:1000]}"
                skill_contexts[name] = ctx

            analyzer = LlmAnalyzer(
                api_key=llm_api_key,
                base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
                model=os.getenv("LLM_MODEL", "deepseek-chat"),
            )
            try:
                analysis_result = analyzer.analyze(collect_result, skill_contexts)
                print(f"  分析完成: {len(analysis_result.get('topPicks', []))} 条精选推荐")
            except Exception as e:
                print(f"  ❌ LLM 分析失败: {e}")
                print("  降级到模板分析")
                analysis_result = _mock_analysis(collect_result)

    # ====== Phase 4: 校验 ======
    print("\n[Phase 4/5] 数据校验...")
    validator = Validator()
    valid, errors = validator.validate_analysis_result(analysis_result)
    if valid:
        print("  ✅ 分析结果校验通过")
    else:
        print("  ⚠️ 校验警告:")
        for e in errors[:5]:
            print(f"    - {e}")

    # ====== Phase 5: 构建站点 ======
    print("\n[Phase 5/5] 构建静态站点...")
    site_data = {
        "date": date,
        "platforms": collect_result.get("platforms", {}),
        "analysis": analysis_result,
        "collectStats": collect_result.get("collectStats", {}),
        "meta": {
            "skillsLoaded": len(all_skills),
            "buildTime": datetime.now().isoformat(),
            "version": "1.0.0",
        },
    }

    # 最终校验
    valid, errors = validator.validate_site_data(site_data)
    if not valid:
        print("  ⚠️ 站点数据校验警告:")
        for e in errors:
            print(f"    - {e}")
        if any("为空" in e for e in errors):
            print("  ❌ 关键数据为空，站点生成终止")
            sys.exit(1)

    builder = SiteBuilder(args.dist_dir, "templates")
    index_path = builder.build(site_data, date)
    print(f"  ✅ 站点已生成: {index_path}")

    # 检查各平台数据量 (任一平台 0 条视为失败)
    zero_platforms = [
        pname for pname, pdata in site_data["platforms"].items()
        if pdata.get("sampleSize", 0) == 0
    ]
    if zero_platforms:
        print(f"  ⚠️ 以下平台采集量为 0: {', '.join(zero_platforms)}")
        print("  标记为部分失败 (GitHub Actions 会视为 failure)")

    print(f"\n{'='*60}")
    print(f"  ✅ DailyAihotAgentRunner 执行完毕")
    print(f"  站点: {Path(args.dist_dir).resolve() / 'index.html'}")
    print(f"  数据: {Path(args.dist_dir).resolve() / 'data' / 'latest.json'}")
    print(f"{'='*60}\n")


def _mock_collect(date: str) -> dict:
    """模拟采集数据 (用于开发/演示)"""
    return {
        "date": date,
        "platforms": {
            "douyin": {
                "platform": "douyin",
                "sampleSize": 5,
                "items": [
                    {
                        "title": f"AI 工具推荐 | {date} 最新 AI 应用合集",
                        "author": "AI科技观察",
                        "likeCount": 12500,
                        "commentCount": 890,
                        "shareCount": 3400,
                        "collectCount": 5600,
                        "commentHotWords": ["好用", "推荐", "效率"],
                        "coverUrl": "",
                        "workUrl": "https://www.douyin.com/video/example1",
                    },
                    {
                        "title": "DeepSeek vs GPT-5 实测对比，谁更强？",
                        "author": "码农实验室",
                        "likeCount": 8900,
                        "commentCount": 1200,
                        "shareCount": 2100,
                        "collectCount": 4300,
                        "commentHotWords": ["DeepSeek", "GPT", "对比"],
                        "coverUrl": "",
                        "workUrl": "https://www.douyin.com/video/example2",
                    },
                ],
                "errors": [],
            },
            "xiaohongshu": {
                "platform": "xiaohongshu",
                "sampleSize": 5,
                "items": [
                    {
                        "title": "2026 年必备的 10 个 AI 编程工具",
                        "author": "程序员小鹿",
                        "likeCount": 6700,
                        "collectCount": 8900,
                        "commentCount": 450,
                        "shareCount": 1200,
                        "coverUrl": "",
                        "workUrl": "https://www.xiaohongshu.com/note/example1",
                    },
                ],
                "errors": [],
            },
            "wechat": {
                "platform": "wechat",
                "sampleSize": 5,
                "items": [
                    {
                        "title": "ChatGPT 与 Codex：AI 编程工具的终极对决",
                        "author": "新智元",
                        "readCount": 100001,
                        "likeCount": 1200,
                        "wowCount": 340,
                        "commentCount": 89,
                        "shareCount": 5600,
                        "publishTime": f"{date}T08:00:00",
                        "workUrl": "https://mp.weixin.qq.com/s/example1",
                    },
                ],
                "errors": [],
            },
        },
        "errors": ["演示模式: REDFOX_API_KEY 未配置"],
        "collectStats": {
            "startTime": f"{date}T00:30:00",
            "endTime": f"{date}T00:30:05",
            "platformStats": {
                "douyin": {"sampleSize": 5, "errorCount": 0},
                "xiaohongshu": {"sampleSize": 5, "errorCount": 0},
                "wechat": {"sampleSize": 5, "errorCount": 0},
            },
            "totalItems": 15,
        },
    }


def _mock_analysis(collect_result: dict) -> dict:
    """模拟 LLM 分析 (模板降级)"""
    from src.llm_analyzer import LlmAnalyzer
    analyzer = LlmAnalyzer(api_key="")
    return analyzer._fallback_analysis(
        collect_result, {},
        "未配置 LLM_API_KEY，使用模板生成",
    )


if __name__ == "__main__":
    main()
