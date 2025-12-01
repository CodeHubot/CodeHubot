FROM python:3.11-slim

WORKDIR /app

# 设置构建参数，支持使用国内镜像源加速
ARG USE_CHINA_MIRROR=false
ARG PIP_INDEX_URL=""
ARG PIP_TRUSTED_HOST=""

# 使用国内镜像源加速（默认使用阿里云）
# Debian 12使用新的sources格式
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null || true
RUN sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null || true

# 配置pip国内镜像源（默认使用阿里云）
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set install.trusted-host mirrors.aliyun.com

# 安装系统依赖（优化：使用 no-install-recommends 减少下载量，合并清理操作）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制依赖文件（先复制依赖文件，利用 Docker 缓存层）
COPY requirements.txt .

# 安装Python依赖（先升级 pip，然后安装依赖）
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

