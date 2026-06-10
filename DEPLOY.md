# AI 热点雷达 — Gitee 部署方案

> Gitee Pipelines（CI）+ Gitee Pages（托管），无需服务器，无需域名。

**站点地址**: `https://jinknow000.gitee.io/ai-hot`

---

## 📋 你的配置

| 项目 | 值 |
|------|-----|
| Gitee 账号 | `jinknow000` |
| 仓库名 | `ai-hot` |
| 每日执行 | **11:30**（北京时间） |
| LLM 端点 | `https://yx-api.yixiong-tech.com/openai/v1`（LiteLLM） |

---

## 第一步：推送代码到 Gitee

```bash
cd "D:/DIY/ai hot"

# 如果还没添加 remote
git remote add gitee https://gitee.com/jinknow000/ai-hot.git

# 推送
git push gitee master
```

---

## 第二步：获取 Gitee 私人令牌

```
https://gitee.com → 右上角头像 → 设置 → 私人令牌 → 生成新令牌
```

- 名称: `aihot-deploy`
- 权限: ✅ `projects` ✅ `pages`
- 生成后**立即复制令牌**（关闭页面后不可见）

---

## 第三步：配置环境变量

```
Gitee 仓库页 → 管理 → 环境变量管理 → 添加变量
```

| 变量名 | 值 |
|--------|-----|
| `REDFOX_API_KEY` | `ak_31fa2c7b257c47fab7f84229da48f247` |
| `LLM_API_KEY` | `sk-T-BGJJiZO338gkWaPVOywA` |
| `LLM_BASE_URL` | `https://yx-api.yixiong-tech.com/openai/v1` |
| `LLM_MODEL` | `deepseek-v4-pro` |
| `GITEE_ACCESS_TOKEN` | `上一步复制的私人令牌` |
| `GITEE_REPO` | `jinknow000/ai-hot` |

---

## 第四步：开启 Gitee Pages + 运行

```
Gitee 仓库页 → 服务 → Gitee Pages
- 分支选 pages
- 目录选 /
- 点击开启
```

然后：
```
DevOps → 流水线 → 点击运行
```

全部绿色 ✅ 后访问：**https://jinknow000.gitee.io/ai-hot**

---

## 🎉 完成

每天 **11:30**（北京时间）全自动运行，无需任何人工操作。
