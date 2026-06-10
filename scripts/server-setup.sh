#!/bin/bash
# =============================================
# AI 热点雷达 - 服务器一键部署脚本
# 在服务器上以 root 执行: bash server-setup.sh
# =============================================
set -e

# ===== 配置区（按需修改）=====
DOMAIN="${1:-_}"                       # 域名，如 aihot.yourdomain.com（或留空用 IP）
SITE_DIR="/home/www/aihot"             # 网站文件目录
NGINX_CONF="/etc/nginx/sites-available/aihot"

echo "========================================"
echo "  AI 热点雷达 - 服务器环境安装"
echo "========================================"

# ----- 1. 检测系统 -----
if [ -f /etc/debian_version ]; then
    PKG_MGR="apt"
elif [ -f /etc/redhat-release ]; then
    PKG_MGR="yum"
else
    echo "❌ 未识别的系统，请手动安装 Nginx"
    exit 1
fi
echo "[1/6] 系统: $PKG_MGR"

# ----- 2. 安装 Nginx -----
echo "[2/6] 安装 Nginx..."
if ! command -v nginx &>/dev/null; then
    $PKG_MGR update -y -q
    $PKG_MGR install nginx -y -q
    systemctl enable nginx
fi
systemctl start nginx
echo "  ✅ Nginx $(nginx -v 2>&1 | cut -d'/' -f2)"

# ----- 3. 创建目录 -----
echo "[3/6] 创建站点目录..."
mkdir -p "$SITE_DIR"

# 复制初始页面（如果有 dist/ 的话）
if [ -f "./dist/index.html" ]; then
    cp -r ./dist/* "$SITE_DIR/"
    echo "  ✅ 初始文件已复制"
else
    echo "  ⚠️ 无 dist/ 目录，等待 CI 首次部署"
fi

# ----- 4. 配置 Nginx -----
echo "[4/6] 配置 Nginx..."
cat > "$NGINX_CONF" << NGINX
server {
    listen 80;
    server_name ${DOMAIN};

    root ${SITE_DIR};
    index index.html;

    access_log /var/log/nginx/aihot_access.log;
    error_log /var/log/nginx/aihot_error.log;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Gzip 压缩
    gzip on;
    gzip_types text/html text/css application/javascript application/json image/svg+xml;
    gzip_min_length 256;
    gzip_comp_level 5;

    # SPA 回退
    location / {
        try_files \$uri \$uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }

    # JSON 数据不缓存
    location /data/ {
        expires -1;
        add_header Cache-Control "no-cache, must-revalidate";
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:5173/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 30s;
    }

    # 公众号封面图防盗链代理
    location /wechat-img/ {
        proxy_pass https://mmbiz.qpic.cn/;
        proxy_set_header Host mmbiz.qpic.cn;
        proxy_set_header Referer "https://mp.weixin.qq.com/";
        proxy_cache_valid 200 1d;
        proxy_cache_key "\$uri";
    }
}
NGINX

# 启用站点
if [ -d /etc/nginx/sites-enabled ]; then
    ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/aihot
    rm -f /etc/nginx/sites-enabled/default
elif [ -d /etc/nginx/conf.d ]; then
    ln -sf "$NGINX_CONF" /etc/nginx/conf.d/aihot.conf
fi

nginx -t && systemctl reload nginx
echo "  ✅ Nginx 配置完成"

# ----- 5. 配置 SSH 密钥（给 Gitee 部署用）-----
echo "[5/6] 生成 SSH 部署密钥..."
if [ ! -f ~/.ssh/gitee_deploy ]; then
    ssh-keygen -t ed25519 -f ~/.ssh/gitee_deploy -N "" -C "gitee-aihot-deploy" -q
    cat ~/.ssh/gitee_deploy.pub >> ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
fi

# 生成 base64 编码（CI 环境变量用）
ENCODED_KEY=$(base64 -w0 ~/.ssh/gitee_deploy 2>/dev/null || base64 ~/.ssh/gitee_deploy | tr -d '\n')

echo ""
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║  📋 复制下面这行，填入 Gitee 环境变量          ║"
echo "  ║     变量名: DEPLOY_SSH_KEY                   ║"
echo "  ╚══════════════════════════════════════════════╝"
echo ""
echo "$ENCODED_KEY"
echo ""
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║  ⬆️ 复制上面这行 base64 字符串 ⬆️              ║"
echo "  ║     是一整行，不含换行                         ║"
echo "  ╚══════════════════════════════════════════════╝"
echo "  ╚══════════════════════════════════════════════╝"

# ----- 6. 检查 Python（API 代理用）-----
echo "[6/6] 检查 Python 环境..."
if command -v python3 &>/dev/null; then
    echo "  ✅ Python $(python3 --version)"
else
    echo "  ⚠️ Python3 未安装（在线查询功能需要）。安装: $PKG_MGR install python3 -y"
fi

# ===== 完成 =====
echo ""
echo "========================================"
echo "  ✅ 服务器环境安装完成！"
echo "========================================"
echo ""
echo "  📁 站点目录: $SITE_DIR"
echo "  📝 Nginx 配置: $NGINX_CONF"
echo ""
echo "  下一步:"
echo "  1. 复制上面的私钥 → Gitee 环境变量 DEPLOY_SSH_KEY"
echo "  2. 在 Gitee 配置其余 6 个环境变量"
echo "  3. 运行 Gitee 流水线 → 部署成功"
echo ""
