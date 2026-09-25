#!/usr/bin/env bash
# 一键部署/更新 NAS 端服务（群晖 Docker）
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "❌ 未找到 .env，请先执行："
  echo "   cp server/.env.example .env && 编辑填写 API_TOKEN"
  exit 1
fi

echo "🔍 构建并启动 tv-renamer-api ..."
docker compose up -d --build

echo ""
echo "✅ 部署完成："
echo "   服务地址   http://<NAS-IP>:$(grep -E '^PORT=' .env | cut -d= -f2 || echo 8123)"
echo "   健康检查   curl -H \"Authorization: Bearer <token>\" http://<NAS-IP>:8123/api/health"
echo "   查看日志   docker compose logs -f tv-renamer-api"
