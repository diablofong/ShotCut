#!/bin/bash
set -e

echo "等待 MariaDB 就緒..."
until python -c "
import asyncio, aiomysql
async def check():
    conn = await aiomysql.connect(
        host='db', port=3306,
        user='${MYSQL_USER:-shotcut}',
        password='${MYSQL_PASSWORD:-shotcut_pass}',
        db='${MYSQL_DATABASE:-shotcut}'
    )
    conn.close()
asyncio.run(check())
" 2>/dev/null; do
    echo "MariaDB 尚未就緒，等待中..."
    sleep 2
done
echo "MariaDB 已就緒"

echo "執行資料庫 migration..."
alembic upgrade head

echo "檢查初始管理員帳號..."
python -m backend.scripts.seed_admin

echo "啟動 ShotCut API..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
