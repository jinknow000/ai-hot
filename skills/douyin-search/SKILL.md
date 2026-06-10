# 抖音热门作品搜索 (Douyin Hot Search)

## 元数据
- **名称**: douyin-search
- **版本**: 1.0.0
- **平台**: 抖音 (Douyin)
- **数据源**: 红狐数据 API
- **更新频率**: 每日

## 功能描述
基于关键词搜索抖音热门 AI 相关作品，返回排名前 5 的爆款视频，包含完整互动数据（点赞、评论、分享、收藏、评论热词）。

## 触发条件
- 用户询问抖音/AI 热门视频时
- 每日自动化采集任务触发时
- 关键词: AI、人工智能、大模型、AI工具

## API 参数

### 搜索接口
- **端点**: `POST https://redfox.hk/story/api/dyData/search`
- **请求体**:
```json
{
  "keyword": "AI",
  "offset": 0,
  "count": 10
}
```

### 作品详情接口 (补全)
- **端点**: `POST https://redfox.hk/story/api/dyData/queryWork`
- **请求体**:
```json
{
  "workId": "作品ID"
}
```

## 执行流程
1. 关键词搜索 → 获取作品 ID 列表
2. 对 top 5 作品逐一调用 queryWork 补全详情
3. 提取: 标题、作者、点赞数、评论数、分享数、收藏数、封面图、评论热词
4. 按互动总量降序排列

## 决策逻辑

### 关键词泛化映射
当用户输入泛化词时，自动扩展为细分关键词列表:
- "AI" → ["AI工具", "AI绘画", "AI编程", "AI视频", "AI写作", "AI教育", "AI医疗", "AI金融", "AI法律", "AI客服"]
- "大模型" → ["GPT", "Claude", "Gemini", "文心一言", "通义千问", "Kimi", "DeepSeek"]
- "AI工具" → ["AI编程助手", "AI绘图工具", "AI视频生成", "AI文案工具", "AI配音"]

### 时间参数
- 默认搜索近 7 天数据
- 自动计算 `startDate` 和 `endDate`

### 分页策略
- 每页最多 10 条
- Agent 默认取第 1 页

## 评分规则
- 基础分 = 40 + (互动数据归一化 × 56)，确保 40-96 范围
- 互动总量 = 点赞 × 0.3 + 评论 × 0.25 + 分享 × 0.25 + 收藏 × 0.2
- 最终分由 LLM 在基础分上 ±10 微调

## 容错策略
- 主 Skill 超时 30 秒 → 降级到备用 Skill (仅搜索，不补全详情)
- 单个作品详情失败 → 跳过，标记在 errors 数组
- API 频率限制 → 请求间延迟 0.15-0.25 秒
- 平台完全不可用 → 返回空数组，不阻塞其他平台

## 输出格式

```json
{
  "platform": "douyin",
  "sampleSize": 5,
  "items": [
    {
      "title": "视频标题",
      "author": "作者昵称",
      "likeCount": 12345,
      "commentCount": 678,
      "shareCount": 910,
      "collectCount": 1112,
      "commentHotWords": ["AI", "厉害"],
      "coverUrl": "https://...",
      "workUrl": "https://..."
    }
  ],
  "errors": []
}
```
