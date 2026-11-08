#!/bin/bash
# 启动报价 API 服务

# 环境变量
export QUOTE_API_HOST=${QUOTE_API_HOST:-0.0.0.0}
export QUOTE_API_PORT=${QUOTE_API_PORT:-8000}
export DATABASE_PATH=${DATABASE_PATH:-/var/lib/sourcing/sourcing_mvp.db}
export ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-*}

# 创建数据库目录
mkdir -p "$(dirname "$DATABASE_PATH")"

# 初始化数据库
echo "Initializing database..."
cd "$(dirname "$0")/.."
python -m sourcing_mvp.init_data

# 启动服务
echo "Starting Quote API on ${QUOTE_API_HOST}:${QUOTE_API_PORT}..."
exec uvicorn sourcing_mvp.quote_api:app \
    --host "$QUOTE_API_HOST" \
    --port "$QUOTE_API_PORT" \
    --log-level info
