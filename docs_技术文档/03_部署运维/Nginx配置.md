# Nginx 配置详解

## 概述

Nginx 是 CodeHubot 项目中用于前端静态文件服务和反向代理的核心组件。本文档详细介绍 Nginx 的配置、优化和最佳实践，适合教学和实际部署使用。

## 为什么使用 Nginx？

### Nginx vs Apache

| 特性 | Nginx | Apache |
|------|-------|--------|
| **架构** | 事件驱动 | 进程驱动 |
| **并发性能** | 高（几万并发） | 中等（几百并发） |
| **内存占用** | 低 | 较高 |
| **静态文件** | 优秀 | 良好 |
| **反向代理** | 优秀 | 良好 |
| **配置复杂度** | 简单 | 复杂 |

### Nginx 的优势

```
✅ 高并发、低内存
✅ 静态文件服务优秀
✅ 反向代理性能好
✅ 负载均衡支持
✅ HTTP/2、SSL/TLS 支持
✅ 配置简单易懂
```

## CodeHubot 项目中的 Nginx 配置

### 前端配置文件

**文件位置**: `frontend/nginx.conf`

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss 
               application/json application/javascript;

    # SPA 路由支持
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API 代理
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 错误页面
    error_page 404 /index.html;
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

## 配置详解

### 1. 基础配置

```nginx
server {
    # 监听端口
    listen 80;
    listen [::]:80;  # IPv6
    
    # 服务器名称
    server_name example.com www.example.com;
    
    # 根目录
    root /usr/share/nginx/html;
    
    # 默认首页
    index index.html index.htm;
    
    # 字符集
    charset utf-8;
    
    # 访问日志
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;
}
```

### 2. SPA 单页应用支持

```nginx
# Vue/React 等 SPA 应用路由支持
location / {
    # 尝试访问文件，不存在则返回 index.html
    try_files $uri $uri/ /index.html;
    
    # 禁用缓存（HTML 文件）
    add_header Cache-Control "no-cache, no-store, must-revalidate";
    add_header Pragma "no-cache";
    add_header Expires "0";
}
```

**说明**：
- `try_files $uri $uri/ /index.html`：先尝试访问文件，不存在则交给前端路由处理
- 禁用缓存：确保用户始终获取最新的 HTML

### 3. 静态资源缓存

```nginx
# CSS/JS 文件（1年缓存）
location ~* \.(css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    access_log off;
}

# 图片文件（1年缓存）
location ~* \.(jpg|jpeg|png|gif|ico|svg|webp)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    access_log off;
}

# 字体文件（1年缓存）
location ~* \.(woff|woff2|ttf|eot|otf)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    access_log off;
}

# 媒体文件（1年缓存）
location ~* \.(mp4|mp3|webm|ogg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    access_log off;
}
```

**缓存策略**：
- `expires 1y`：缓存1年
- `Cache-Control "public, immutable"`：公开缓存，内容不变
- `access_log off`：关闭访问日志，减少 I/O

### 4. Gzip 压缩

```nginx
# 启用 Gzip 压缩
gzip on;

# 压缩级别（1-9，推荐6）
gzip_comp_level 6;

# 最小压缩文件大小
gzip_min_length 1024;

# 压缩类型
gzip_types 
    text/plain 
    text/css 
    text/xml 
    text/javascript 
    application/json 
    application/javascript 
    application/xml+rss 
    application/x-javascript 
    image/svg+xml;

# 为代理请求启用压缩
gzip_vary on;

# 禁用 IE6 的 Gzip
gzip_disable "msie6";

# 压缩代理请求
gzip_proxied any;
```

**压缩效果**：
- JS/CSS 文件可压缩 60-80%
- JSON 数据可压缩 70-90%
- HTML 文件可压缩 50-70%

### 5. 反向代理

```nginx
# 代理后端 API
location /api {
    # 代理目标
    proxy_pass http://backend:8000;
    
    # 基础头部
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # 超时设置
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    
    # 缓冲设置
    proxy_buffering on;
    proxy_buffer_size 4k;
    proxy_buffers 8 4k;
    proxy_busy_buffers_size 8k;
}

# 去掉前缀的代理
location /api/ {
    # 去掉 /api 前缀
    rewrite ^/api/(.*)$ /$1 break;
    proxy_pass http://backend:8000;
    
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### 6. WebSocket 支持

```nginx
location /ws {
    proxy_pass http://backend:8000;
    
    # WebSocket 必需配置
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    
    # 基础头部
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    
    # 超时设置（WebSocket 需要长连接）
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}
```

### 7. SSL/HTTPS 配置

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;
    
    # SSL 证书
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # SSL 协议版本
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # SSL 加密套件
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    
    # SSL 会话缓存
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # HSTS（强制 HTTPS）
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    # 其他配置...
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name example.com;
    return 301 https://$server_name$request_uri;
}
```

### 8. 负载均衡

```nginx
# 定义后端服务器组
upstream backend_servers {
    # 负载均衡策略（默认轮询）
    # ip_hash;           # 根据客户端 IP 哈希
    # least_conn;        # 最少连接数
    
    server backend1:8000 weight=3;  # 权重3
    server backend2:8000 weight=2;  # 权重2
    server backend3:8000 backup;    # 备份服务器
}

server {
    listen 80;
    
    location /api {
        proxy_pass http://backend_servers;
        proxy_set_header Host $host;
    }
}
```

**负载均衡策略**：
- **轮询（默认）**：按顺序分配
- **ip_hash**：同一客户端固定分配到同一服务器
- **least_conn**：分配到连接数最少的服务器
- **weight**：权重，值越大分配越多

### 9. 跨域配置（CORS）

```nginx
location /api {
    # 允许的来源
    add_header Access-Control-Allow-Origin *;
    # 或指定域名
    # add_header Access-Control-Allow-Origin https://example.com;
    
    # 允许的方法
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
    
    # 允许的头部
    add_header Access-Control-Allow-Headers "Authorization, Content-Type";
    
    # 允许携带凭证
    add_header Access-Control-Allow-Credentials true;
    
    # 预检请求缓存时间
    add_header Access-Control-Max-Age 3600;
    
    # OPTIONS 请求直接返回
    if ($request_method = 'OPTIONS') {
        return 204;
    }
    
    proxy_pass http://backend:8000;
}
```

### 10. 安全配置

```nginx
server {
    # 隐藏 Nginx 版本号
    server_tokens off;
    
    # 防止点击劫持
    add_header X-Frame-Options "SAMEORIGIN" always;
    
    # XSS 保护
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # CSP 内容安全策略
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;
    
    # 限制请求体大小
    client_max_body_size 10M;
    
    # 限制请求频率
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    
    location /api {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://backend:8000;
    }
}
```

## 性能优化

### 1. Worker 进程配置

```nginx
# nginx.conf
user nginx;

# Worker 进程数（通常等于 CPU 核心数）
worker_processes auto;

# 每个 Worker 最大连接数
events {
    worker_connections 1024;
    use epoll;  # Linux 使用 epoll
}
```

### 2. 缓存配置

```nginx
# 代理缓存
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;

location /api/data {
    proxy_cache api_cache;
    proxy_cache_valid 200 10m;
    proxy_cache_key $uri$is_args$args;
    proxy_cache_bypass $http_cache_control;
    
    add_header X-Cache-Status $upstream_cache_status;
    
    proxy_pass http://backend:8000;
}
```

### 3. 连接优化

```nginx
http {
    # 保持连接
    keepalive_timeout 65;
    keepalive_requests 100;
    
    # 客户端超时
    client_body_timeout 12;
    client_header_timeout 12;
    send_timeout 10;
    
    # 缓冲区大小
    client_body_buffer_size 16k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 8k;
}
```

## Docker 中使用 Nginx

### Dockerfile

```dockerfile
FROM nginx:alpine

# 复制配置文件
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制静态文件
COPY dist/ /usr/share/nginx/html/

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget -q --spider http://localhost/ || exit 1
```

### docker-compose.yml

```yaml
services:
  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./frontend/nginx.conf:/etc/nginx/conf.d/default.conf
      - ./frontend/dist:/usr/share/nginx/html
    networks:
      - app-network
    depends_on:
      - backend
    restart: unless-stopped
```

## 常见问题

### 1. 404 Not Found

```nginx
# ❌ 错误配置
location / {
    root /usr/share/nginx/html;
}

# ✅ 正确配置
location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;  # SPA 必需
}
```

### 2. 跨域问题

```nginx
# 方案1: Nginx 添加 CORS 头部
add_header Access-Control-Allow-Origin *;

# 方案2: 使用反向代理（推荐）
location /api {
    proxy_pass http://backend:8000;
}
```

### 3. WebSocket 连接失败

```nginx
# ✅ 必须添加这两个头部
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

### 4. 文件上传大小限制

```nginx
# 默认 1M，需要增加
client_max_body_size 100M;
```

### 5. 502 Bad Gateway

**可能原因**：
- 后端服务未启动
- 后端服务地址错误
- 后端响应超时

**解决方案**：
```nginx
# 增加超时时间
proxy_connect_timeout 300s;
proxy_send_timeout 300s;
proxy_read_timeout 300s;

# 检查后端地址
proxy_pass http://backend:8000;  # Docker 中使用服务名
```

## 日志管理

### 1. 访问日志格式

```nginx
http {
    # 自定义日志格式
    log_format main '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" '
                    '$request_time';
    
    access_log /var/log/nginx/access.log main;
}
```

### 2. 查看日志

```bash
# 实时查看访问日志
tail -f /var/log/nginx/access.log

# 实时查看错误日志
tail -f /var/log/nginx/error.log

# Docker 容器日志
docker logs -f frontend
```

### 3. 日志轮转

```nginx
# /etc/logrotate.d/nginx
/var/log/nginx/*.log {
    daily                # 每天轮转
    missingok           # 日志丢失不报错
    rotate 7            # 保留7天
    compress            # 压缩旧日志
    delaycompress       # 延迟压缩
    notifempty          # 空文件不轮转
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

## 测试和调试

### 1. 测试配置文件

```bash
# 测试配置语法
nginx -t

# 重新加载配置（不停机）
nginx -s reload

# 停止服务
nginx -s stop

# 优雅停止
nginx -s quit
```

### 2. 调试技巧

```nginx
# 开启调试日志
error_log /var/log/nginx/error.log debug;

# 查看请求处理过程
location / {
    add_header X-Debug-URI $uri;
    add_header X-Debug-Args $args;
    # ...
}
```

## 教学要点总结

### 核心概念
1. **静态文件服务**: root、index、try_files
2. **反向代理**: proxy_pass、proxy_set_header
3. **负载均衡**: upstream、权重、策略
4. **缓存优化**: expires、Cache-Control、gzip
5. **安全配置**: SSL/TLS、CORS、请求限制

### 常用场景
- ✅ SPA 单页应用部署
- ✅ 前后端分离架构
- ✅ 静态资源优化
- ✅ API 反向代理
- ✅ WebSocket 支持
- ✅ HTTPS 加密传输

### 最佳实践
- ✅ 静态资源设置长缓存
- ✅ HTML 文件禁用缓存
- ✅ 启用 Gzip 压缩
- ✅ 配置健康检查
- ✅ 日志轮转管理

## 相关文档

- [Docker容器化部署](./Docker容器化部署.md) - Nginx 容器化部署
- [前端架构](../02_系统架构/前端架构.md) - 前端项目结构
- [常见问题排查](../04_开发调试/常见问题排查.md) - 部署问题排查
