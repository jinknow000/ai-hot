# 公众号 10 万+ 爆款文章推荐 (WeChat 10w+ Hot Articles)

## 元数据
- **名称**: wechat-10w-hot
- **版本**: 1.0.0
- **平台**: 微信公众号 (WeChat Official Accounts)
- **数据源**: 红狐数据 API
- **更新频率**: 每日

## 功能描述
搜索微信公众号 AI 相关 10 万+ 阅读的爆款文章，返回排名前 5 篇，包含完整互动数据（阅读数、点赞、在看、评论、分享）。

## 触发条件
- 用户询问公众号/10w+/AI 文章推荐时
- 每日自动化采集任务触发时
- 关键词: AI 工具、AI 编程、AI 智能体、Agent、大模型

## API 参数

### 文章搜索接口
- **端点**: `POST https://redfox.hk/story/api/gzhData/searchArticle`
- **请求体**:
```json
{
  "keyword": "AI智能体",
  "offset": 0,
  "sortType": "_4"
}
```

### sortType 说明
| 值 | 排序方式 |
|----|---------|
| `_4` | 按阅读数倒序 (推荐) |
| `_2` | 按发布时间倒序 |

### 文章详情接口
- **端点**: `POST https://redfox.hk/story/api/gzhData/queryArticle`
- **请求体**:
```json
{
  "workUrl": "https://mp.weixin.qq.com/s/xxx"
}
```

### 公众号信息接口
- **端点**: `POST https://redfox.hk/story/api/gzhData/queryAccount`
- **请求体**:
```json
{
  "accountId": "公众号ID"
}
```

## 执行流程
1. 使用 5 个关键词分别搜索 → 去重合并
2. 筛选 readCount ≥ 100000 的文章
3. 按阅读数降序取 top 5
4. 补全文章详情（点赞、在看、评论、分享）
5. 输出结构化数据

## 决策逻辑

### 关键词轮询
5 个固定关键词按顺序搜索:
1. "AI工具"
2. "AI编程"
3. "AI智能体"
4. "Agent"
5. "大模型"

### 去重策略
- 以 `workUrl` 为唯一键去重
- 同一篇文章出现在多个关键词结果中时，保留首次出现的

### 分页策略
- 每个关键词默认取前 10 条
- 合并后按阅读数排序取 top 5

## 评分规则
- 基础分 = 40 + (阅读量归一化 × 30) + (互动率归一化 × 26)
- 互动率 = (点赞 + 在看 + 评论 + 分享) / 阅读量
- 最终分由 LLM 在基础分上 ±8 微调

## 容错策略
- 主 Skill 超时 30 秒 → 降级到备用 Skill (仅搜索 1 个关键词)
- 单篇文章详情失败 → 跳过，使用搜索返回的基础数据
- API 频率限制 → 请求间延迟 0.15-0.25 秒

## 输出格式

```json
{
  "platform": "wechat",
  "sampleSize": 5,
  "items": [
    {
      "title": "文章标题",
      "author": "公众号名称",
      "readCount": 100001,
      "likeCount": 606,
      "wowCount": 89,
      "commentCount": 3,
      "shareCount": 2613,
      "publishTime": "2026-06-07T18:00:00",
      "workUrl": "https://mp.weixin.qq.com/s/xxx"
    }
  ],
  "errors": []
}
```
