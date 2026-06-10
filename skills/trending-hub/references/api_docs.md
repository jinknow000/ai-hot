# 全网热点 API 参考文档

## RedFox 全网热点数据接口

### 1. 热点查询接口
- **端点**: `POST https://redfox.hk/story/api/trendingData/query`
- **参数**:
  - `platform` (str): `all` 全平台, 或指定平台 `weibo`/`zhihu`/`baidu`/`douyin`/`bilibili`/`kuaishou`/`toutiao`
  - `count` (int): 返回数量

## 覆盖平台
| 平台 | 更新频率 |
|------|---------|
| 百度 | 实时 |
| 知乎 | 实时 |
| 微博 | 实时 |
| 抖音 | 实时 |
| B站 | 每小时 |
| 快手 | 每小时 |
| 今日头条 | 每小时 |

## AI 话题过滤规则
自动过滤标题中包含以下任一关键词的热点:
AI, 人工智能, 大模型, ChatGPT, GPT, Claude, Gemini, DeepSeek, Kimi, 文心, 通义, 智能体, Agent, AIGC, 机器学习, 深度学习, 神经网络, LLM, OpenAI, Copilot, Cursor, Codex, Midjourney, Stable Diffusion, Sora
