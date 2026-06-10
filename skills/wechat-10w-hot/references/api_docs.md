# 公众号 API 参考文档

## RedFox 公众号数据接口

### 1. 文章搜索接口
- **端点**: `POST https://redfox.hk/story/api/gzhData/searchArticle`
- **参数**:
  - `keyword` (str): 搜索关键词
  - `offset` (int): 偏移量
  - `sortType` (str): `_4` 按阅读数倒序, `_2` 按发布时间倒序

### 2. 文章详情接口
- **端点**: `POST https://redfox.hk/story/api/gzhData/queryArticle`
- **参数**:
  - `workUrl` (str): 文章链接

### 3. 公众号搜索接口
- **端点**: `POST https://redfox.hk/story/api/gzhData/searchAccount`
- **参数**:
  - `name` (str): 公众号名称

### 4. 公众号信息接口
- **端点**: `POST https://redfox.hk/story/api/gzhData/queryAccount`
- **参数**:
  - `accountId` (str): 公众号 ID

## 响应字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| readCount | int | 阅读数 |
| likeCount | int | 点赞数 |
| wowCount | int | 在看数 |
| commentCount | int | 评论数 |
| shareCount | int | 分享数 |
| publishTime | str | 发布时间 |
| workUrl | str | 文章链接 |
