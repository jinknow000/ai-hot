# AI 热点雷达 — Gitee 部署方案

> 从零到上线，分 4 步完成。预计耗时：30 分钟。

---

## 📋 你需要准备的信息

| 序号 | 需要什么 | 去哪里获取 | 示例 |
|------|---------|-----------|------|
| ① | **Gitee 账号** | [gitee.com](https://gitee.com) 注册 | `your-username` |
| ② | **RedFox API Key** | [redfox.hk](https://redfox.hk) → 注册 → 控制台 → API Key | `ak_xxxxxxxxxxxx` |
| ③ | **LLM API Key** | [platform.deepseek.com](https://platform.deepseek.com) → API Keys（新用户送 500w tokens） | `sk-xxxxxxxxxxxx` |
| ④ | **服务器** | 任意 Linux 服务器（1核1G 即可） | IP: `123.45.67.89` |
| ⑤ | **SSH 登录方式** | 服务器的 root/普通用户 + 密钥 | 用户: `root`, 端口: `22` |
| ⑥ | **域名**（可选） | 任意域名注册商，A 记录指向服务器 IP | `aihot.yourdomain.com` |

---

## 第一步：申请 API Key（5 分钟）

### 1.1 红狐数据 API Key

```
打开 https://redfox.hk → 注册/登录 → 控制台 → API 管理 → 创建 Key
```

- 新用户 **300 次免费调用额度**
- 这个项目每天消耗约 15-20 次调用
- 300 次够免费用 **15-20 天**，之后按量付费 ⚠️

### 1.2 DeepSeek API Key

```  
打开 https://platform.deepseek.com → 注册 → API Keys → 创建
```

- 新用户赠送 **500 万 tokens**
- 每次分析消耗约 2000-3000 tokens
- 500 万 tokens 够免费用 **好几年**

> 💡 也可以用其他兼容 OpenAI 接口的模型：
> - 通义千问: `https://dashscope.aliyuncs.com/compatible-mode/v1`
> - 智谱 GLM: `https://open.bigmodel.cn/api/paas/v4`
> - Kimi (月之暗面): `https://api.moonshot.cn/v1`
> - 任意 Ollama 本地模型

---

## 第二步：推送代码到 Gitee（5 分钟）

```bash
# 在项目目录执行
cd "D:/DIY/ai hot"

# 添加 Gitee 远程仓库（替换 YOUR_USERNAME）
git remote add gitee https://gitee.com/YOUR_USERNAME/ai-hot.git

# 推送
git push gitee master

# Gitee 默认分支名是 master，无需改为 main
```

推送后在 Gitee 仓库页面应该能看到所有文件。

---

## 第三步：配置服务器（10 分钟）

### 3.1 SSH 登录服务器

```bash
ssh root@你的服务器IP
```

### 3.2 一键安装环境

在服务器上执行：

```bash
# 更新系统
apt update && apt upgrade -y  # Ubuntu/Debian
# 或
yum update -y                 # CentOS

# 安装 Nginx
apt install nginx -y
systemctl enable nginx
systemctl start nginx
```

### 3.3 创建部署目录

```bash
mkdir -p /home/www/aihot
chown -R $USER:$USER /home/www/aihot
```

### 3.4 配置 Nginx

```bash
# 创建配置文件（把 DOMAIN 换成你的域名或服务器 IP）
cat > /etc/nginx/sites-available/aihot << 'NGINX'
server {
    listen 80;
    server_name 你的域名或IP;

    root /home/www/aihot;
    index index.html;

    access_log /var/log/nginx/aihot_access.log;
    error_log /var/log/nginx/aihot_error.log;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    gzip on;
    gzip_types text/html text/css application/javascript application/json;
    gzip_min_length 256;

    location / {
        try_files $uri $uri/ /index.html;
        expires 1h;
    }

    location /data/ {
        expires -1;
        add_header Cache-Control "no-cache, must-revalidate";
    }

    # API 代理（如需在线查询功能）
    location /api/ {
        proxy_pass http://127.0.0.1:5173/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 30s;
    }

    # 微信公众号封面图防盗链代理
    location /wechat-img/ {
        proxy_pass https://mmbiz.qpic.cn/;
        proxy_set_header Host mmbiz.qpic.cn;
        proxy_set_header Referer "https://mp.weixin.qq.com/";
    }
}
NGINX

# 启用站点
ln -s /etc/nginx/sites-available/aihot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # 删除默认站点（可选）

# 测试 + 重载
nginx -t && systemctl reload nginx
```

### 3.5 配置 SSH 密钥（让 Gitee 能自动部署）

```bash
# 在服务器上生成专用密钥对
ssh-keygen -t ed25519 -f ~/.ssh/gitee_deploy -N "" -C "gitee-aihot-deploy"

# 把公钥加入 authorized_keys
cat ~/.ssh/gitee_deploy.pub >> ~/.ssh/authorized_keys

# 显示私钥并生成 base64 编码（直接复制粘贴到 Gitee）
cat ~/.ssh/gitee_deploy | base64 -w0 && echo
```

> ⚠️ 把输出的私钥**完整复制保存**，包括 `-----BEGIN OPENSSH PRIVATE KEY-----` 和 `-----END OPENSSH PRIVATE KEY-----`

---

## 第四步：配置 Gitee 流水线（10 分钟）

### 4.1 配置环境变量

打开 Gitee 仓库页面 → **管理** → **环境变量管理** → **添加变量**：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `REDFOX_API_KEY` | `ak_你的key` | 第二步申请的红狐 API Key |
| `LLM_API_KEY` | `sk-你的key` | 第二步申请的 DeepSeek API Key |
| `LLM_BASE_URL` | `https://api.deepseek.com` | LLM 接口地址 |
| `LLM_MODEL` | `deepseek-chat` | 模型名称 |
| `DEPLOY_HOST` | `123.45.67.89` | 你的服务器 IP |
| `DEPLOY_USER` | `root` | SSH 登录用户名 |
| `DEPLOY_PATH` | `/home/www/aihot` | 网站目录 |
| `DEPLOY_SSH_KEY` | （base64 编码的私钥） | 执行 `cat ~/.ssh/gitee_deploy \| base64 -w0` 得到的**一行字符串** |

> ⚠️ `DEPLOY_SSH_KEY` 是 base64 编码后的**一行字符串**，不是原始私钥。用 `base64 -w0` 生成。

### 4.2 启用流水线

Gitee 仓库页面 → **流水线** (DevOps/Pipelines) → 应该能看到 `.gitee-ci.yml` 已自动识别。

点击 **手动运行** 测试一次：

1. 点击「运行」按钮
2. 等待 3 个任务依次完成（约 1-2 分钟）
3. 绿色 ✅ = 成功

### 4.3 验证部署

```bash
# 在服务器上确认文件已同步
ls /home/www/aihot/
# 应该看到: index.html  data/

# 浏览器访问
curl http://你的服务器IP/
# 应该返回 HTML 内容
```

浏览器打开 `http://你的服务器IP` 就能看到 AI 热点雷达页面了。

---

## 🎉 完成！

后续每天凌晨 00:30，Gitee 流水线会自动：
1. 拉取代码
2. 采集三平台 AI 热点数据
3. LLM 分析 + 评分
4. 生成新页面
5. SSH 同步到你的服务器

**整个过程全自动，无需任何人工操作。**

---

## 🔧 可选增强

### 绑定自己的域名

```bash
# 域名 DNS 添加 A 记录指向服务器 IP
# 然后修改 Nginx 配置中的 server_name

sed -i 's/server_name .*/server_name aihot.yourdomain.com;/' /etc/nginx/sites-available/aihot
nginx -t && systemctl reload nginx
```

### 开启 HTTPS（Let's Encrypt 免费证书）

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d aihot.yourdomain.com
# 按提示操作，选择自动重定向 HTTP → HTTPS
```

### 启用 API 代理（在线查询功能）

```bash
# 在服务器上启动代理服务
cd /home/www/aihot
REDFOX_API_KEY=ak_your_key nohup python3 src/api_proxy.py --port 5173 &

# 或配置 systemd 自动启动
cat > /etc/systemd/system/aihot-api.service << 'SERVICE'
[Unit]
Description=AI Hot Radar API Proxy
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/www/aihot
Environment=REDFOX_API_KEY=ak_your_key
ExecStart=/usr/bin/python3 src/api_proxy.py --port 5173
Restart=on-failure

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable --now aihot-api
```

---

## ❓ 常见问题

**Q: 流水线执行失败？**
到 Gitee 流水线页面点击失败的构建 → 查看日志 → 根据错误信息排查。

**Q: 某平台 0 条数据导致构建失败？**
这是正常的——某天某个平台确实没有 AI 热点数据时，临时手动触发重新跑一次即可。

**Q: 想换 LLM 模型？**
修改 Gitee 环境变量 `LLM_BASE_URL` 和 `LLM_MODEL`，支持任意 OpenAI 兼容接口。

**Q: 没有服务器？**
- 最低配云服务器（1核1G）月费约 ¥30-50
- 或者用 GitHub Actions + GitHub Pages（`.github/workflows/daily-aihot.yml` 已配置好）

**Q: API 调用超额了？**
- 红狐数据：登录 redfox.hk 充值，按量付费
- DeepSeek：登录 platform.deepseek.com 充值，非常便宜
