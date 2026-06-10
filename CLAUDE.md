# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI 热点雷达 (AI Hot Radar) — daily automated aggregation of AI-related trending content from Douyin (60s API), Xiaohongshu (暂无), and WeChat (RedFox API) platforms, with LLM structured analysis and opportunity scoring. Generates a static HTML site deployed via Cloudflare Pages.

📖 **运维手册**: [OPERATIONS.md](./OPERATIONS.md) — 修改频率、切换部署、更换数据源等操作指南

## Commands

```bash
# Run the full daily pipeline (with demo data if no API key)
python -m src.run_daily_agent

# Run for a specific date
python -m src.run_daily_agent --date 2026-06-09

# Collect only (skip LLM analysis)
python -m src.run_daily_agent --collect-only

# Analyze existing data only
python -m src.run_daily_agent --analyze-only --data dist/data/latest.json

# Start API proxy for online query feature
python src/api_proxy.py --port 5173

# View generated site
open dist/index.html
```

## Architecture

### Data Flow
```
GitHub Actions (00:30 CST)
  → SkillLoader (reads skills/*/SKILL.md)
  → RedFoxCollector (parallel 3-platform fetch via ThreadPoolExecutor)
  → LlmAnalyzer (OpenAI-compatible API, base score pre-computation + LLM fine-tune)
  → Validator (JSON schema enforcement)
  → SiteBuilder (data-embedded HTML → dist/)
  → SSH deploy to Nginx server
```

### Key Design Decisions

- **No database** — All data stored as JSON files (`dist/data/latest.json`, `dist/archive/YYYY-MM-DD.json`)
- **Multi-layer fault tolerance**: Main Skill → Backup Skill → Built-in fallback logic. Single platform failure never blocks others.
- **Base score pre-computation (40-96)** — Interaction data (likes/comments/shares) determines base score; LLM only adjusts ±10. This prevents hallucinated scores.
- **Pure HTML/CSS/JS frontend** — No framework. Single page reads `{{SITE_DATA}}` placeholder replaced at build time. Dark theme, responsive, platform-tagged cards.
- **Skills system** — Each skill is `SKILL.md` (decision manual) + `scripts/` (Python collectors) + `references/` (API docs). Skills are agent-portable across Codex/Claude Code.
- **API rate limiting** — 0.15-0.25s delay between RedFox API calls to avoid throttling.
- **Image hotlink bypass** — Nginx proxies WeChat cover images with correct Referer header (`/wechat-img/ → mmbiz.qpic.cn`).

### Three-Platform Scoring Differences

| Platform | Score Formula | Why |
|----------|---------------|-----|
| WeChat | readCount log-normalized + interaction rate | Read count is primary metric |
| Douyin | like×0.3 + comment×0.25 + share×0.25 + collect×0.2 | Shares and comments have higher weight |
| Xiaohongshu | like×0.35 + collect×0.35 + comment×0.2 + share×0.1 | Collections are uniquely valuable on RED |

### Environment Variables

- `REDFOX_API_KEY` — RedFox Data API key (required for real data; demo mode otherwise)
- `LLM_API_KEY` — LLM API key (OpenAI-compatible; template fallback otherwise)
- `LLM_BASE_URL` — Default `https://api.deepseek.com`
- `LLM_MODEL` — Default `deepseek-v4-pro`
- `DEPLOY_HOST/USER/PATH/SSH_KEY` — GitHub Actions deployment targets

### CI/CD

- **GitHub Actions** (`.github/workflows/daily-aihot.yml`): Trigger daily at 00:30 CST, workflow_dispatch, push to main. Validation fails if any platform returns 0 items.
- **Gitee Pipelines** (`.gitee-ci.yml`): Mirror config for domestic deployment. Uses shell tasks instead of marketplace actions. Same cron schedule.
- **Secrets**: All credentials via GitHub Secrets / Gitee 环境变量, never in repo.
- **Artifacts**: `aihot-site` retained 7 days (GitHub only).
