#!/bin/bash
set -e

# ============================================
# 旅图 (Lv) - 一键部署脚本
# ============================================

DOMAIN="lv.zdfamory.com"
API_DOMAIN="api.lv.zdfamory.com"
EMAIL=""  # Let's Encrypt 通知邮箱，请填写

echo "========================================="
echo "  旅图 (Lv) 部署脚本"
echo "  前端: https://${DOMAIN}"
echo "  后端: https://${API_DOMAIN}"
echo "========================================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
    echo "Docker 安装完成"
fi

# 检查 Docker Compose
if ! docker compose version &> /dev/null; then
    echo "安装 Docker Compose 插件..."
    apt-get update && apt-get install -y docker-compose-plugin
fi

# 检查 .env.production
if [ ! -f .env.production ]; then
    echo "错误: .env.production 不存在"
    exit 1
fi

# 检查关键配置
if grep -q "change_me_in_production" .env.production; then
    echo "警告: .env.production 中仍有默认密码，建议修改！"
    read -p "继续部署？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 创建 certbot 目录
mkdir -p certbot/conf certbot/www

# ---- 第 1 步: 先用 HTTP 获取 SSL 证书 ----
echo ""
echo "[1/4] 获取 SSL 证书..."

# 临时 nginx 配置（仅 HTTP，用于 certbot 验证）
cat > /tmp/nginx-cert.conf <<'EOF'
server {
    listen 80;
    server_name lv.zdfamory.com api.lv.zdfamory.com;
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
}
EOF

# 启动临时 nginx
docker run -d --name certbot-nginx \
    -p 80:80 \
    -v /tmp/nginx-cert.conf:/etc/nginx/conf.d/default.conf:ro \
    -v $(pwd)/certbot/www:/var/www/certbot:ro \
    nginx:1.27-alpine

sleep 3

# 申请证书
if [ -n "$EMAIL" ]; then
    docker run --rm \
        -v $(pwd)/certbot/conf:/etc/letsencrypt \
        -v $(pwd)/certbot/www:/var/www/certbot \
        certbot/certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        -d ${DOMAIN} \
        -d ${API_DOMAIN} \
        --email ${EMAIL} \
        --agree-tos \
        --no-eff-email
else
    docker run --rm \
        -v $(pwd)/certbot/conf:/etc/letsencrypt \
        -v $(pwd)/certbot/www:/var/www/certbot \
        certbot/certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        -d ${DOMAIN} \
        -d ${API_DOMAIN} \
        --register-unsafely-without-email \
        --agree-tos \
        --no-eff-email
fi

# 停止临时 nginx
docker rm -f certbot-nginx

if [ ! -d "certbot/conf/live/${DOMAIN}" ]; then
    echo "SSL 证书获取失败！请检查 DNS 是否已解析到本服务器"
    echo "运行: ping ${DOMAIN}  确认解析到本机 IP"
    exit 1
fi

echo "SSL 证书获取成功！"

# ---- 第 2 步: 构建并启动所有服务 ----
echo ""
echo "[2/4] 构建 Docker 镜像..."
docker compose -f docker-compose.prod.yml build

echo ""
echo "[3/4] 启动服务..."
docker compose -f docker-compose.prod.yml up -d

# ---- 第 3 步: 等待服务就绪 ----
echo ""
echo "[4/4] 等待服务启动..."
sleep 10

# 健康检查
RETRIES=0
MAX_RETRIES=30
until curl -sf http://localhost:8000/api/v1/health/live > /dev/null 2>&1; do
    RETRIES=$((RETRIES+1))
    if [ $RETRIES -ge $MAX_RETRIES ]; then
        echo "后端启动超时，请检查日志: docker compose -f docker-compose.prod.yml logs backend"
        exit 1
    fi
    sleep 2
done

echo ""
echo "========================================="
echo "  部署成功！"
echo ""
echo "  前端: https://${DOMAIN}"
echo "  后端: https://${API_DOMAIN}"
echo "  健康检查: https://${API_DOMAIN}/api/v1/health/live"
echo ""
echo "  常用命令:"
echo "  查看日志: docker compose -f docker-compose.prod.yml logs -f"
echo "  重启服务: docker compose -f docker-compose.prod.yml restart"
echo "  停止服务: docker compose -f docker-compose.prod.yml down"
echo "========================================="

# 设置证书自动续期 cron
(crontab -l 2>/dev/null; echo "0 3 * * * docker run --rm -v $(pwd)/certbot/conf:/etc/letsencrypt -v $(pwd)/certbot/www:/var/www/certbot certbot/certbot renew --quiet && docker compose -f $(pwd)/docker-compose.prod.yml restart nginx") | sort -u | crontab -

echo "SSL 证书自动续期已配置（每天凌晨 3 点检查）"
