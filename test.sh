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

# python3 manage.py makemigrations users
# python3 manage.py makemigrations detachments
# python3 manage.py makemigrations notices
# python3 manage.py makemigrations connection_lists
# python3 manage.py makemigrations files
# python3 manage.py makemigrations approvals
# python3 manage.py makemigrations handbooks

python3 manage.py migrate

coverage run --source=THUPracticeOnline_backend,users,notices,detachments,utils,connection_lists,files,approvals,handbooks,logs,votes -m pytest --junit-xml=xunit-reports/xunit-result.xml
ret=$?
coverage xml -o coverage-reports/coverage.xml
coverage report
exit $ret
