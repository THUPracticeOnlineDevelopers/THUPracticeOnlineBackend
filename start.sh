#!/bin/sh
# 安装 Redis
apt-get update && apt-get install -y redis-server

# 启动 Redis 服务器
redis-server --daemonize yes --bind 127.0.0.1 --port 6379

# 等待 Redis 就绪
until redis-cli -h 127.0.0.1 -p 6379 ping; do
  echo "Waiting for Redis to be ready..."
  sleep 1
done

#设置环境变量，用于选择不同的数据库
export DJANGO_ENV=production

# python3 manage.py makemigrations users
# python3 manage.py makemigrations detachments
# python3 manage.py makemigrations notices
# python3 manage.py makemigrations connection_lists
# python3 manage.py makemigrations files
# python3 manage.py makemigrations approvals
# python3 manage.py makemigrations handbooks

python3 manage.py migrate
python3 manage.py collectstatic --noinput

DJANGO_SUPERUSER_USERNAME=fantastic_604B \
DJANGO_SUPERUSER_EMAIL=THUPracticeOnline@163.com \
DJANGO_SUPERUSER_PASSWORD=Admin_THUPracticeOnline \
python3 manage.py createsuperuser --noinput

python3 clear.py

uwsgi --ini uwsgi.ini
