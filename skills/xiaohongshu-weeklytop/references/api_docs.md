# 小红书 API 参考文档

## RedFox 小红书数据接口

### 1. 笔记搜索接口
- **端点**: `POST https://redfox.hk/story/api/xhsData/searchNote`
- **参数**:
  - `keyword` (str): 搜索关键词
  - `sortType` (str): `hot` 按热度, `latest` 按最新
  - `count` (int): 返回数量

### 2. 作品详情接口
- **端点**: `POST https://redfox.hk/story/api/xhsData/queryWork`
- **参数**:
  - `workId` (str): 笔记 ID

### 3. 账号详情接口
- **端点**: `POST https://redfox.hk/story/api/xhsData/queryAccount`
- **参数**:
  - `accountId` (str): 账号 ID

## 响应字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| likeCount | int | 点赞数 |
| collectCount | int | 收藏数 |
| commentCount | int | 评论数 |
| shareCount | int | 分享数 |
| coverUrl | str | 封面图 URL |
| workUrl | str | 笔记链接 |

## 平台特性
- 小红书收藏权重高于其他平台
- 评分公式: 点赞 × 0.35 + 收藏 × 0.35 + 评论 × 0.2 + 分享 × 0.1
