#!/bin/bash
set -e

# 從 DATABASE_URL 解析連線資訊（支援外部 DB 與本地 container）
DB_HOST=$(python3 -c "from urllib.parse import urlparse; u=urlparse('${DATABASE_URL}'); print(u.hostname)")
DB_PORT=$(python3 -c "from urllib.parse import urlparse; u=urlparse('${DATABASE_URL}'); print(u.port or 3306)")
DB_USER=$(python3 -c "from urllib.parse import urlparse; u=urlparse('${DATABASE_URL}'); print(u.username or '')")
DB_PASS=$(python3 -c "from urllib.parse import urlparse; u=urlparse('${DATABASE_URL}'); print(u.password or '')")
DB_NAME=$(python3 -c "from urllib.parse import urlparse; u=urlparse('${DATABASE_URL}'); print(u.path.lstrip('/'))")

echo "等待資料庫就緒（${DB_HOST}:${DB_PORT}）..."
until python3 -c "
import asyncio, aiomysql
async def check():
    conn = await aiomysql.connect(
        host='${DB_HOST}', port=${DB_PORT},
        user='${DB_USER}', password='${DB_PASS}',
        db='${DB_NAME}'
    )
    conn.close()
asyncio.run(check())
" 2>/dev/null; do
    echo "資料庫尚未就緒，等待中..."
    sleep 2
done
echo "資料庫已就緒"

echo "執行資料庫 migration..."
alembic upgrade head

echo "檢查初始管理員帳號..."
python -m backend.scripts.seed_admin

echo "啟動 ShotCut API..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
