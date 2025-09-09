FROM python:3.11

ENV DEPLOY 1

WORKDIR /app

COPY requirements.txt .

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple uwsgi

COPY . .

EXPOSE 80

RUN apt-get update && apt-get install -y mariadb-client

CMD ["sh","./start.sh"]
