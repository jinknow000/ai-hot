# AI 热点雷达 — 无服务器部署方案

> 零成本上线：Gitee Pipelines（CI）+ Gitee Pages（托管）。无需服务器，无需域名。

**站点地址**: `https://你的用户名.gitee.io/ai-hot`

---

## 📋 你需要准备的 3 样东西

| 序号 | 需要什么 | 去哪里获取 | 耗时 |
|------|---------|-----------|------|
| ① | **Gitee 账号** | [gitee.com](https://gitee.com) 免费注册 | 1 分钟 |
| ② | **RedFox API Key** | [redfox.hk](https://redfox.hk) 注册即送 300 次额度 | 2 分钟 |
| ③ | **LLM API Key** | [platform.deepseek.com](https://platform.deepseek.com) 注册送 500w tokens | 2 分钟 |

总计准备时间：**5 分钟**。

---

## 第一步：申请 API Key

### 红狐数据
```
打开 https://redfox.hk → 注册 → 控制台 → 创建 API Key
```
复制 `ak_` 开头的 key，每天消耗约 15 次调用。

### DeepSeek LLM
```
打开 https://platform.deepseek.com → 注册 → API Keys → 创建
```
复制 `sk-` 开头的 key。也可以换其他兼容 OpenAI 接口的模型：
- 通义千问: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- 智谱 GLM: `https://open.bigmodel.cn/api/paas/v4`
- Kimi: `https://api.moonshot.cn/v1`

---

## 第二步：推送代码到 Gitee

```bash
cd "D:/DIY/ai hot"

# 1. 在 Gitee 网页上创建新仓库，名称填 ai-hot
#    网址: https://gitee.com/你的用户名/ai-hot

# 2. 推送到 Gitee
git remote add gitee https://gitee.com/你的用户名/ai-hot.git
git push gitee master
```

推送后 Gitee 仓库页面能看到所有文件。

---

## 第三步：配置 Gitee

### 3.1 获取私人令牌（Access Token）

```
Gitee → 右上角头像 → 设置 → 私人令牌 → 生成新令牌
```

- 名称填 `aihot-deploy`
- 权限勾选: ✅ `projects`（仓库操作）+ ✅ `pages`（Pages 部署）
- 点「提交」后 **立即复制令牌**（只显示一次！）

### 3.2 配置环境变量

```
Gitee 仓库页 → 管理 → 环境变量管理 → 添加变量
```

一共添加 **7 个** 变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `REDFOX_API_KEY` | `ak_xxx` | 红狐 API Key |
| `LLM_API_KEY` | `sk-xxx` | DeepSeek API Key |
| `LLM_BASE_URL` | `https://api.deepseek.com` | LLM 地址 |
| `LLM_MODEL` | `deepseek-chat` | 模型名 |
| `GITEE_ACCESS_TOKEN` | 上一步复制的令牌 | Gitee 私人令牌 |
| `GITEE_REPO` | `你的用户名/ai-hot` | 仓库路径 |

### 3.3 开启 Gitee Pages

```
Gitee 仓库页 → 服务 → Gitee Pages
```

- 部署分支选 `pages`
- 部署目录选 `/`（根目录）
- 点击「开启」

首次开启后会自动构建一次。如果提示没有 `pages` 分支，先手动运行一次流水线（见下一步）。

---

## 第四步：运行流水线

```
Gitee 仓库页 → DevOps → 流水线
```

`.gitee-ci.yml` 已被自动识别。点击 **「运行」** 手动触发第一次构建。

流水线会依次执行：
```
环境准备 → 采集数据+LLM分析 → 推送到pages分支+触发Pages部署
```

全部显示绿色 ✅ 后，访问：
```
https://你的用户名.gitee.io/ai-hot
```

---

## 🎉 完成！

后续**每天凌晨 00:30**，Gitee 会自动：
1. 采集三平台 AI 热点
2. LLM 分析 + 打分
3. 更新 Gitee Pages

**完全不需要人工操作。** 每天早上打开网址就能看到最新的 AI 热点分析。

---

## ❓ 常见问题

**Q: 流水线执行失败？**  
去 DevOps → 流水线 → 点击失败的记录 → 查看日志 → 根据错误信息排查。最常见原因是 API Key 填错。

**Q: Pages 访问 404？**  
确认：① 服务 → Gitee Pages 已开启 ② 分支选 `pages` ③ 第一次需要手动运行流水线生成 pages 分支

**Q: 想用自己的域名？**  
Gitee Pages 支持自定义域名（需实名认证）。在 Pages 设置中绑定即可，会自动生成 HTTPS 证书。

**Q: 某天没有数据怎么办？**  
流水线会标记为失败，手动重新触发一次即可。通常是因为某个平台当天没有 AI 热点。

**Q: API 额度用完了？**
- 红狐数据：登录 redfox.hk 充值，每次调用几分钱
- DeepSeek：登录 platform.deepseek.com 充值，非常便宜

**Q: 以后想要服务器了？**  
项目自带完整服务器部署方案：`.github/workflows/daily-aihot.yml`（GitHub Actions）和 `scripts/server-setup.sh`（服务器一键脚本）随时可用。
