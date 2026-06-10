# 🔭 AI 热点雷达 — 运维手册

## 技术栈一览

```
┌──────────────────────────────────────────────────────┐
│                    数据采集层                          │
│  公众号: RedFox API (gzhData/searchArticle)           │
│  抖音:   60s API (60s.viki.moe/v2/douyin)            │
│  小红书: 暂无可用免费 API                             │
├──────────────────────────────────────────────────────┤
│                    LLM 分析层                          │
│  OpenAI 兼容接口 → yx-api.yixiong-tech.com           │
│  模型: deepseek-v4-pro                               │
├──────────────────────────────────────────────────────┤
│                    站点生成层                          │
│  Python SiteBuilder → dist/index.html                │
│  纯 HTML/CSS/JS，数据嵌入 {{SITE_DATA}}              │
├──────────────────────────────────────────────────────┤
│                    定时调度层                          │
│  GitHub Actions / Gitee Pipelines → cron 触发        │
├──────────────────────────────────────────────────────┤
│                    部署层                              │
│  Cloudflare Pages (当前) / Nginx + VPS (备选)        │
└──────────────────────────────────────────────────────┘
```

---

## 一、配置速查表

### 所有可配置项一览

| 配置项 | 位置 | 说明 |
|--------|------|------|
| 🔑 RedFox API Key | `.gitee-ci.yml:41` / GitHub Secrets | 红狐数据接口密钥 |
| 🔑 LLM API Key | `.gitee-ci.yml:42` / GitHub Secrets | LLM 分析接口密钥 |
| 🔗 LLM 地址 | `.gitee-ci.yml:43` | LLM API 的 Base URL |
| 🤖 LLM 模型 | `.gitee-ci.yml:44` | 模型名 (如 `deepseek-v4-pro`) |
| ⏰ 采集频率 | `.gitee-ci.yml:10` / `.github/workflows/daily-aihot.yml:6` | cron 表达式 |
| 📡 部署目标 | `.gitee-ci.yml:77-80` | Cloudflare 项目名/账号 |
| 🎯 关键词 | `src/collector.py:48-59` | AI 过滤关键词列表 |
| 🔢 采集数量 | `src/collector.py:38-60` | 每个平台返回条数 |
| 📊 评分公式 | `src/collector.py:106-113` | 抖音互动量加权公式 |
| 🏷️ AI 关键词 | `src/collector.py:25-32` | 热搜过滤关键词 |

---

## 二、修改采集频率

### Gitee Pipelines（当前使用）

文件：`.gitee-ci.yml` 第 10 行

```yaml
triggers:
  schedule:
    - cron: "30 3 * * *"   # ← 改这里
```

**cron 表达式**：`分 时 日 月 星期`（UTC 时间，北京时间 = UTC+8）

| 频率 | cron (UTC) | 说明 |
|------|------------|------|
| 每天 11:30 (当前) | `30 3 * * *` | UTC 03:30 = 北京 11:30 |
| 每天 08:00 | `0 0 * * *` | UTC 00:00 = 北京 08:00 |
| 每天 20:00 | `0 12 * * *` | UTC 12:00 = 北京 20:00 |
| 每 6 小时 | `0 */6 * * *` | 00:00, 06:00, 12:00, 18:00 UTC |
| 每 2 小时 | `0 */2 * * *` | — |
| 每天 2 次 (09:00, 21:00) | `0 1,13 * * *` | — |

### GitHub Actions（备用）

文件：`.github/workflows/daily-aihot.yml` 第 6 行

```yaml
on:
  schedule:
    - cron: "30 16 * * *"  # ← 改这里 (UTC，北京 00:30)
```

---

## 三、切换部署平台

### 当前方案：Cloudflare Pages

配置文件：`.gitee-ci.yml` 第 71-83 行

**需要改的变量**（在 `.gitee-ci.yml` 里直接改）：

```yaml
# 第 77-78 行
export CLOUDFLARE_API_TOKEN="cfut_xxx"       # Cloudflare API Token
export CLOUDFLARE_ACCOUNT_ID="5831b786..."    # Cloudflare 账户 ID

# 第 81 行
npx wrangler pages deploy ./dist \
  --project-name=ai-hot \      # ← Cloudflare Pages 项目名
  --commit-dirty=true
```

**切换步骤**：
1. 登录 Cloudflare Dashboard → Workers & Pages
2. 创建新 Pages 项目（或使用已有）
3. 生成 API Token（Profile → API Tokens → Create Token → Cloudflare Pages Edit）
4. 将 Token 和 Account ID 填入 `.gitee-ci.yml`

### 备选方案：Nginx + VPS

Nginx 配置模板：`nginx/aihot.conf`

**切换步骤**：
1. 在 GitHub Actions 中取消注释 `deploy` job（`.github/workflows/daily-aihot.yml` 第 83-104 行）
2. 在 GitHub Secrets 中配置：
   - `DEPLOY_SSH_KEY` — SSH 私钥
   - `DEPLOY_HOST` — 服务器 IP
   - `DEPLOY_USER` — SSH 用户
   - `DEPLOY_PATH` — 网站目录（如 `/home/www/aihot`）
3. 服务器上放好 Nginx 配置（参考 `nginx/aihot.conf`）
4. 如果要开启在线查询功能，服务器上启动 API 代理：
   ```bash
   python src/api_proxy.py --port 5173 &
   ```

---

## 四、切换数据源

### RedFox API

**API Key 存放位置**：
- 生产环境：`.gitee-ci.yml` 第 41 行
- 本地开发：设置环境变量 `REDFOX_API_KEY`
- GitHub Actions：GitHub Secrets → `REDFOX_API_KEY`

**公众号搜索关键词**：`src/collector.py` 第 55 行

```python
"wechat": {
    "keywords": ["AI工具", "AI编程", "AI智能体", "Agent", "大模型"],
    "count": 5,         # 返回条数
}
```

### 60s API（抖音热搜）

代码位置：`src/collector.py` 第 248-310 行

- **API 地址**：`SIXTYS_API_BASE = "https://60s.viki.moe/v2"`（第 22 行）
- **无需 API Key**，开箱即用
- AI 过滤关键词：`src/collector.py` 第 25-32 行 `AI_FILTER_KEYWORDS`

**如果 60s API 公共实例挂了**，可以自部署：
```bash
docker run -d --restart always -p 4399:4399 vikiboss/60s:latest
```
然后把 `SIXTYS_API_BASE` 改为 `http://your-server:4399/v2`

### LLM 分析

代码位置：`src/llm_analyzer.py`

```python
# 第 76-80 行
def __init__(self, api_key: str,
             base_url: str = "https://api.deepseek.com",   # ← API 地址
             model: str = "deepseek-v4-pro"):              # ← 模型名
```

**如果 LLM 挂了**，系统会自动降级到模板分析（`src/run_daily_agent.py` 第 152-156 行），不会阻塞流程。

---

## 五、修改评分规则

### 三平台评分公式

文件：`src/collector.py` 和 `src/llm_analyzer.py`

**抖音**（60s API 返回的是热搜排名，没有互动数据）：
- 直接用 `hot_value`（热搜热度值）作为基础分
- LLM 在基础上 ±10 微调

**公众号**（RedFox，有完整互动数据）：
- `src/llm_analyzer.py` 中的 `_compute_base_score()` 方法
- readCount 对数归一化 + 互动率加权

**小红书**（暂无数据源，占位）：
- 公式已在 CLAUDE.md 中定义：like×0.35 + collect×0.35 + comment×0.2 + share×0.1

### 修改 AI 过滤关键词

文件：`src/collector.py` 第 25-32 行

```python
AI_FILTER_KEYWORDS = [
    "AI", "人工智能", "大模型", "ChatGPT", "GPT", "Claude", "Gemini",
    "DeepSeek", "Kimi", "文心", "通义", "智能体", "Agent", "AIGC",
    # ... 按需增删
]
```

---

## 六、项目文件地图

```
ai hot/
├── .gitee-ci.yml              ← 🎯 CI/CD 主配置（cron、密钥、部署命令）
├── .github/workflows/
│   └── daily-aihot.yml        ← GitHub Actions 备用配置
├── .env.example               ← 本地开发环境变量模板
├── src/
│   ├── run_daily_agent.py     ← 🎯 主入口（流程编排）
│   ├── collector.py           ← 🎯 数据采集（RedFox + 60s API）
│   ├── llm_analyzer.py        ← 🎯 LLM 分析引擎（评分、Schema）
│   ├── skill_loader.py        ← Skills 系统加载器
│   ├── validator.py           ← 数据校验
│   ├── site_builder.py        ← 站点生成（HTML + JSON）
│   └── api_proxy.py           ← API 代理（在线查询功能）
├── skills/                    ← Agent Skills（可移植到其他 Agent）
│   ├── wechat-10w-hot/
│   ├── douyin-search/
│   ├── xiaohongshu-weeklytop/
│   └── trending-hub/
├── dist/                      ← 🎯 构建输出（index.html + data/）
│   ├── index.html
│   └── data/
│       ├── latest.json        ← 最新数据
│       └── archive/           ← 历史归档
├── nginx/
│   └── aihot.conf             ← Nginx 部署配置模板
├── CLAUDE.md                  ← 项目开发文档
├── OPERATIONS.md              ← 本文件（运维手册）
├── README.md                  ← 项目介绍
└── DEPLOY.md                  ← 部署教程
```

---

## 七、本地开发

```bash
# 1. 安装依赖
pip install requests openai

# 2. 设置环境变量
export REDFOX_API_KEY="ak_xxx"
export LLM_API_KEY="sk_xxx"
export LLM_BASE_URL="https://yx-api.yixiong-tech.com/openai/v1"
export LLM_MODEL="deepseek-v4-pro"

# 3. 完整运行
python -m src.run_daily_agent

# 4. 仅采集（跳过 LLM）
python -m src.run_daily_agent --collect-only

# 5. 指定日期
python -m src.run_daily_agent --date 2026-06-09

# 6. 仅分析已有数据
python -m src.run_daily_agent --analyze-only --data dist/data/latest.json

# 7. 启动 API 代理（在线查询）
python src/api_proxy.py --port 5173

# 8. 查看站点
open dist/index.html
```

---

## 八、常见问题

### Q: 抖音/小红书总是 0 条？
- 抖音：60s API 公共实例可能被墙，尝试自部署 `vikiboss/60s`
- 小红书：目前没有免费 API，需要接入付费服务（如 Just One API、TikHub）

### Q: LLM 分析失败？
- 检查 `LLM_MODEL` 是否在 key 允许的模型列表中
- 系统会自动降级到模板分析，不会阻断流程
- 错误信息会打印在 Phase 3 输出中

### Q: 部署到 Cloudflare Pages 失败？
- Cloudflare API Token 权限需要包含 "Cloudflare Pages — Edit"
- 确认 `CLOUDFLARE_ACCOUNT_ID` 正确
- 手动验证：`npx wrangler pages deploy ./dist --project-name=ai-hot`

### Q: 怎么换到 GitHub Actions？
- GitHub Actions 配置在 `.github/workflows/daily-aihot.yml`
- 需要在 GitHub Secrets 中配置所有密钥
- 当前 `.gitee-ci.yml` 是主 CI，GitHub Actions 是备用

### Q: 如何增加新的数据平台？
1. 在 `src/collector.py` 的 `PLATFORM_CONFIG` 中添加配置
2. 在 `skills/` 下创建对应的 Skill 目录和脚本
3. 实现 `_collect_xxx_fallback()` 方法
4. 在 `src/llm_analyzer.py` 中添加该平台的评分逻辑
5. 更新 `dist/index.html` 模板中的平台显示
