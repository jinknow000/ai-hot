# 🔭 AI 热点雷达 (AI Hot Radar)

> 每日自动聚合抖音·小红书·公众号三大平台 AI 热点，LLM 结构化分析与机会评分。

**在线演示**: [aihot.paicoding.com](https://aihot.paicoding.com) （配置 API Key 后可部署自己的实例）

## 功能特性

- 🤖 **全自动采集** — GitHub Actions 每天凌晨 00:30 自动运行，无需人工干预
- 📡 **三平台覆盖** — 抖音、小红书、微信公众号，AI 热点一网打尽
- 🧠 **LLM 分析** — 结构化分析 + 机会评分（0-100），告诉你今天什么值得写
- 📊 **可视化面板** — 每日摘要、精选推荐、平台数据、策略洞察，一目了然
- 🔍 **在线查询** — 内置 9 个 RedFox API 查询卡片，实时搜索三平台数据
- 💰 **低成本运行** — 无数据库、纯静态站点，日均 API 调用 15-20 次
- 🔌 **Agent Skills** — 4 个标准化 Skills，可复用到 Codex、Claude Code 等 Agent 平台

## 技术架构

```
DailyAihotAgentRunner
├── SkillLoader          # 读取 SKILL.md / references
├── RedFoxCollector      # 并行采集三平台数据 (红狐数据 API)
├── LlmAnalyzer          # LLM 结构化分析 (OpenAI 兼容接口)
├── Validator            # JSON 字段校验
└── SiteBuilder          # 静态 HTML 生成
```

**核心设计**:
- **无数据库** — 数据写入 JSON 文件（`dist/data/latest.json` + 按日归档）
- **纯静态前端** — 单页面 HTML/CSS/JS，数据嵌入渲染
- **三层容错** — 主 Skill → 备用 Skill → 内置降级逻辑
- **基础分 + LLM 微调** — 互动数据算出 40-96 基础分，LLM 只做 ±10 微调

## 项目结构

```
ai-hot/
├── .github/workflows/daily-aihot.yml   # CI/CD 每日构建
├── skills/                              # Agent Skills (4 个)
│   ├── douyin-search/                   # 抖音热门作品搜索
│   ├── wechat-10w-hot/                  # 公众号 10w+ 爆款文章
│   ├── xiaohongshu-weeklytop/           # 小红书爆款笔记
│   └── trending-hub/                    # 全网热点追踪 (7 平台)
├── src/
│   ├── skill_loader.py                  # Skills 加载器
│   ├── collector.py                     # RedFox 数据采集器
│   ├── llm_analyzer.py                  # LLM 分析引擎
│   ├── validator.py                     # 数据校验器
│   ├── site_builder.py                  # 静态站点生成器
│   ├── api_proxy.py                     # API 代理服务
│   └── run_daily_agent.py              # 主入口
├── templates/index.html                 # HTML 模板
├── dist/                                # 构建输出 (index.html + data/)
├── nginx/aihot.conf                     # Nginx 配置
└── requirements.txt                     # Python 依赖
```

## 快速开始

### 🚀 在线部署（推荐，5 分钟）

→ 详见 **[DEPLOY.md](DEPLOY.md)** 完整部署指南

无需服务器，无需域名。Gitee Pipelines + Gitee Pages，完全免费，全自动运行。

### 💻 本地运行

```bash
git clone https://gitee.com/YOUR_USERNAME/ai-hot.git
cd ai-hot
cp .env.example .env
# 编辑 .env 填入你的 API Key
```

必填:
- `REDFOX_API_KEY` — [红狐数据](https://redfox.hk) API Key（新用户 300 次免费额度）
- `LLM_API_KEY` — LLM API Key（支持 DeepSeek、OpenAI 等兼容接口）

可选:
- `LLM_BASE_URL` — 默认 `https://api.deepseek.com`
- `LLM_MODEL` — 默认 `deepseek-v4-pro`

### 3. 本地运行

```bash
# 安装依赖 (Python 3.11+)
pip install requests openai

# 运行 (无 API Key 时使用演示数据)
python -m src.run_daily_agent

# 查看站点
open dist/index.html
```

### 4. 一键部署到 Gitee Pages（免费，无需服务器）

**5 分钟上线，零成本**。详见 [DEPLOY.md](DEPLOY.md)。

1. 推送代码到 [Gitee](https://gitee.com)
2. 配置 6 个环境变量（API Key + Gitee 令牌）
3. 开启 Gitee Pages，部署分支选 `pages`
4. 运行流水线 → 访问 `https://你的用户名.gitee.io/ai-hot`

每天凌晨 00:30 全自动：采集 → LLM 分析 → 生成页面 → Gitee Pages 自动部署。

#### 其他部署方式

- **GitHub Pages**: 使用 `.github/workflows/daily-aihot.yml`，GitHub Actions 定时构建 + Pages 托管
- **自有服务器**: 使用 `scripts/server-setup.sh` 一键安装 Nginx + SSH 自动部署

### 5. 服务器部署

```bash
# Nginx 配置
sudo cp nginx/aihot.conf /etc/nginx/sites-available/aihot
sudo ln -s /etc/nginx/sites-available/aihot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# API 代理服务
REDFOX_API_KEY=ak_your_key python src/api_proxy.py --port 5173 &
```

## Agent Skills 使用

Skills 可在 Codex、Claude Code 等 Agent 平台直接使用：

```
# 安装 Skills
我想装这几个 Skills：https://redfox.hk/skills
包括：全网热点追踪、小红书爆款笔记、公众号 10 万+ 爆款文章推荐
```

每个 Skill 的结构:
- `SKILL.md` — 决策手册（触发条件、API 参数、执行流程、评分规则、容错策略）
- `scripts/` — Python 采集脚本
- `references/` — API 参考文档

## API

项目依赖 [红狐数据](https://redfox.hk) 新媒体数据 API：

| 平台 | 接口数 | 说明 |
|------|--------|------|
| 公众号 | 6 | 搜索文章/账号、查询文章/账号详情、作品列表 |
| 小红书 | 2 | 账号详情、作品详情 |
| 抖音 | 2 | 账号详情、作品详情 |
| 工具类 | 3 | AI 图片生成、视频生成 |

新用户 300 次免费调用额度，无需月付。

## License

MIT © 2026
