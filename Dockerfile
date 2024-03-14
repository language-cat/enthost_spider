FROM python:3.10-alpine as ent_spider_base

RUN set -eux && sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories
RUN apk update
RUN apk add --no-cache python3 python3-dev
RUN mkdir -p ~/.pip
RUN echo "[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple" | tee ~/.pip/pip.conf
RUN pip install --upgrade pip -i https://pypi.mirrors.ustc.edu.cn/simple
COPY requirements.txt /tmp/requirements

RUN pip install -i https://pypi.mirrors.ustc.edu.cn/simple -r /tmp/requirements

FROM ent_spider_base

COPY . /app/enthost_spider
WORKDIR /app/enthost_spider
ENTRYPOINT scrapyd

EXPOSE 5000
EXPOSE 6800




