FROM python:3.8-slim

WORKDIR /app

# 使用国内镜像源加速（阿里云）
# Python 3.8使用Debian 11，有sources.list文件
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null || true
RUN sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null || true

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    bash \
    && rm -rf /var/lib/apt/lists/*

# 配置pip国内镜像源（阿里云）
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set install.trusted-host mirrors.aliyun.com

# 先只复制requirements.txt文件（利用Docker缓存层）
# 如果依赖文件没变，可以复用缓存，避免重复下载
COPY backend/requirements.txt /app/backend/requirements.txt
COPY service/celery-service/requirements.txt /app/celery-service/requirements.txt

# 安装Python依赖（这一步会被缓存，只要requirements.txt没变）
RUN pip install --no-cache-dir -r /app/backend/requirements.txt && \
    pip install --no-cache-dir -r /app/celery-service/requirements.txt

# 再复制代码（代码变化频繁，但不影响依赖安装的缓存）
COPY backend /app/backend
COPY service/celery-service /app/celery-service

# 设置工作目录为celery-service
WORKDIR /app/celery-service

# 创建日志目录
RUN mkdir -p /app/celery-service/logs

# 设置环境变量
ENV PYTHONPATH="/app/celery-service:/app/backend:$PYTHONPATH"

# Worker入口（直接使用Python脚本启动）
CMD ["python", "worker.py"]
