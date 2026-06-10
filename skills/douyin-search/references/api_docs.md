# 抖音 API 参考文档

## RedFox 抖音数据接口

### 1. 搜索接口
- **端点**: `POST https://redfox.hk/story/api/dyData/search`
- **认证**: Header `X-API-KEY`
- **参数**:
  - `keyword` (str): 搜索关键词
  - `offset` (int): 偏移量
  - `count` (int): 返回数量，最大 20

### 2. 作品详情接口
- **端点**: `POST https://redfox.hk/story/api/dyData/queryWork`
- **参数**:
  - `workId` (str): 作品 ID

### 3. 账号详情接口
- **端点**: `POST https://redfox.hk/story/api/dyData/queryAccount`
- **参数**:
  - `accountId` (str): 账号 ID

## 响应字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| likeCount | int | 点赞数 |
| commentCount | int | 评论数 |
| shareCount | int | 分享数 |
| collectCount | int | 收藏数 |
| commentHotWords | list[str] | 评论热词 |
| coverUrl | str | 封面图 URL |
| workUrl | str | 作品链接 |
