# 全网热点追踪 (Trending Hub)

## 元数据
- **名称**: trending-hub
- **版本**: 1.0.0
- **平台**: 百度、知乎、微博、抖音、B站、快手、今日头条 (7 平台聚合)
- **数据源**: 红狐数据 API
- **更新频率**: 每小时

## 功能描述
聚合百度、知乎、微博、抖音、B站、快手、今日头条 7 个平台的热搜数据，按小时更新，过滤出 AI 相关热点话题。

## 触发条件
- 用户询问全网热点/热搜时
- 每日自动化采集任务触发时 (作为辅助数据源)
- 关键词过滤: AI、人工智能、大模型

## API 参数

### 全网热点接口
- **端点**: `POST https://redfox.hk/story/api/trendingData/query`
- **请求体**:
```json
{
  "platform": "all",
  "count": 50
}
```

## 执行流程
1. 拉取 7 平台热搜数据
2. 过滤 AI 相关话题
3. 按热度值降序排列
4. 取 top 20 条
5. 输出结构化数据

## 决策逻辑

### AI 话题过滤规则
- 标题/内容包含: AI、人工智能、大模型、ChatGPT、GPT、Claude、Gemini、DeepSeek、Kimi、文心、通义、智能体、Agent、AIGC
- 热度值 ≥ 10000 的条目优先

### 时间窗口
- 数据按小时更新
- 每日采集任务取最近一次快照

## 输出格式

```json
{
  "platform": "trending-hub",
  "sampleSize": 20,
  "items": [
    {
      "title": "话题标题",
      "platform": "微博",
      "hotValue": 1234567,
      "rank": 1,
      "url": "https://..."
    }
  ],
  "errors": []
}
```
