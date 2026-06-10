# 小红书七日爆款笔记 (Xiaohongshu Weekly Top)

## 元数据
- **名称**: xiaohongshu-weeklytop
- **版本**: 1.0.0
- **平台**: 小红书 (Xiaohongshu/RED)
- **数据源**: 红狐数据 API
- **更新频率**: 每日

## 功能描述
查询小红书过去 7 天 AI 相关领域的爆款笔记 TOP50，覆盖 25 个垂直分类，返回排名前 5 条笔记。

## 触发条件
- 用户询问小红书/AI 爆款笔记时
- 每日自动化采集任务触发时
- 关键词: AI 工具、AI 编程、AI 智能体、Agent、大模型

## API 参数

### 账号详情接口
- **端点**: `POST https://redfox.hk/story/api/xhsData/queryAccount`
- **请求体**:
```json
{
  "accountId": "账号ID"
}
```

### 作品详情接口
- **端点**: `POST https://redfox.hk/story/api/xhsData/queryWork`
- **请求体**:
```json
{
  "workId": "作品ID"
}
```

## 执行流程
1. 使用 5 个关键词分别查询爆款笔记
2. 筛选近 7 天发布的笔记
3. 按互动总量降序取 top 5
4. 补全笔记详情
5. 输出结构化数据

## 决策逻辑

### 25 个垂直分类
AI 领域覆盖以下分类:
科技、教育、职场、设计、编程、效率工具、数码、学习、读书、写作、绘画、摄影、视频、音乐、创业、副业、理财、健康、旅游、美食、家居、时尚、美妆、穿搭、育儿

### 关键词策略
5 个关键词按优先级轮询:
1. "AI工具"
2. "AI编程"
3. "AI智能体"
4. "Agent"
5. "大模型"

### 时间窗口
- 自动计算 7 天前日期 → `startDate`
- 当天日期 → `endDate`
- 格式: YYYY-MM-DD

## 评分规则
- 基础分 = 40 + (互动数据归一化 × 56)
- 互动总量 = 点赞 × 0.35 + 收藏 × 0.35 + 评论 × 0.2 + 分享 × 0.1
- 小红书收藏权重比抖音高（平台特性）
- 最终分由 LLM 在基础分上 ±10 微调

## 容错策略
- 主 Skill 超时 30 秒 → 降级到备用 Skill (仅查 2 个关键词)
- 单篇笔记详情失败 → 跳过
- API 频率限制 → 请求间延迟 0.15-0.25 秒

## 输出格式

```json
{
  "platform": "xiaohongshu",
  "sampleSize": 5,
  "items": [
    {
      "title": "笔记标题",
      "author": "作者昵称",
      "likeCount": 5678,
      "collectCount": 2345,
      "commentCount": 123,
      "shareCount": 45,
      "coverUrl": "https://...",
      "workUrl": "https://..."
    }
  ],
  "errors": []
}
```
