#!/bin/bash

# 1. 拉取最新代码
echo "正在拉取最新代码..."
git pull

if [ $? -ne 0 ]; then
    echo "错误: git pull 失败"
    exit 1
fi

# 2. 构建前端镜像
echo "正在构建前端镜像..."
docker-compose -f docker/docker-compose.prod.yml build frontend

if [ $? -ne 0 ]; then
    echo "错误: 前端镜像构建失败"
    exit 1
fi

# 3. 启动服务
echo "正在启动服务..."
docker-compose -f docker/docker-compose.prod.yml up -d

if [ $? -ne 0 ]; then
    echo "错误: 服务启动失败"
    exit 1
fi

echo "部署完成！"

