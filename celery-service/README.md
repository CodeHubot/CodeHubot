# AIOT Celery 独立服务

## 📖 简介

Celery Worker 和 Flower 监控面板已从主backend中分离出来，作为独立服务运行。

**服务包含：**
- ✅ **Celery Worker** - 异步任务处理
- ✅ **Flower** - 任务监控面板

**架构优势：**
- ✅ 不影响主backend的HTTP请求性能
- ✅ 可独立扩展Worker数量
- ✅ 专注于异步任务处理
- ✅ Flower监控更稳定

## 🏗️ 架构

```
Backend (8000)
    ↓ 提交任务
Redis (6379) - 消息队列
    ↓ 拉取任务
Celery Worker (本服务) - 处理任务
    ↓ 更新结果
MySQL数据库
    ↑ 监控任务
Flower (5555) - 监控面板
```

**主backend：**
- 提交向量化任务到队列
- 不再运行Celery Worker

**Celery服务（本服务）：**
- Worker处理向量化任务
- Flower提供监控界面

## 📦 安装部署

### 1. 安装依赖

```bash
cd celery-service
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp env.example .env
nano .env
```

配置内容：
```env
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=aiot_admin
DB_USER=root
DB_PASSWORD=your_password

# API密钥（向量化需要）
DASHSCOPE_API_KEY=sk-your-api-key-here

# Flower监控
FLOWER_PORT=5555
FLOWER_BASIC_AUTH=admin:password
```

### 3. 启动服务

#### 方式A：前台启动（推荐测试）

```bash
# 启动Worker
bash start_worker.sh

# 另开终端启动Flower
bash start_flower.sh
```

#### 方式B：后台启动

```bash
# 启动Worker（后台）
nohup bash start_worker.sh > logs/worker.log 2>&1 &

# 启动Flower（后台）
nohup bash start_flower.sh > logs/flower.log 2>&1 &
```

#### 方式C：systemd服务（生产推荐）

**创建 Celery Worker 服务：**

`/etc/systemd/system/celery-worker.service`:
```ini
[Unit]
Description=AIOT Celery Worker
After=network.target redis.service mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/celery-service
EnvironmentFile=/path/to/celery-service/.env
Environment="PYTHONPATH=/path/to/celery-service:/path/to/backend"
ExecStart=/usr/bin/bash /path/to/celery-service/start_worker.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**创建 Flower 服务：**

`/etc/systemd/system/celery-flower.service`:
```ini
[Unit]
Description=AIOT Celery Flower
After=network.target redis.service celery-worker.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/celery-service
EnvironmentFile=/path/to/celery-service/.env
Environment="PYTHONPATH=/path/to/celery-service:/path/to/backend"
ExecStart=/usr/bin/bash /path/to/celery-service/start_flower.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**启动服务：**
```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-worker celery-flower
sudo systemctl start celery-worker celery-flower
sudo systemctl status celery-worker celery-flower
```

### 4. 验证服务

#### 检查Worker

```bash
# 查看Worker日志
tail -f logs/celery_worker.log

# 应该看到：
# [INFO/MainProcess] Connected to redis://localhost:6379//
# [INFO/MainProcess] mingle: all alone
# [INFO/MainProcess] celery@hostname ready.
```

#### 访问Flower

打开浏览器访问：`http://localhost:5555/flower`

- 用户名：`admin`
- 密码：`password`（从.env配置）

应该看到：
- ✅ Worker列表
- ✅ 任务统计
- ✅ 任务历史

## 🔧 功能特性

### 支持的任务

| 任务名称 | 说明 | 示例 |
|---------|------|------|
| `embed_document` | 文档向量化 | 将文档切分并生成向量 |

### 任务配置

```python
# 任务配置
max_retries=3           # 最多重试3次
default_retry_delay=60  # 重试延迟60秒
task_time_limit=3600    # 任务超时1小时
```

### Worker配置

```bash
# 并发数：4个worker进程
--concurrency=4

# 每个worker最多处理50个任务后重启
--max-tasks-per-child=50

# 事件循环池：eventlet（支持异步）
--pool=eventlet
```

## 📊 监控和管理

### Flower监控面板

访问：`http://localhost:5555/flower`

**功能：**
- ✅ 实时查看Worker状态
- ✅ 查看任务列表和状态
- ✅ 查看任务详情和日志
- ✅ 手动重试失败任务
- ✅ 查看任务统计图表

### 查看日志

```bash
# Worker日志
tail -f logs/celery_worker.log

# Flower日志
tail -f logs/flower.log

# 或systemd日志
sudo journalctl -u celery-worker -f
sudo journalctl -u celery-flower -f
```

### 停止服务

```bash
# 停止所有服务
bash stop_all.sh

# 或systemd
sudo systemctl stop celery-worker celery-flower
```

## 🧪 测试

### 测试Worker连接

```bash
# 进入Python环境
cd celery-service
python3

# 测试代码
>>> from celery_app import celery_app
>>> result = celery_app.control.inspect().active()
>>> print(result)
# 应该看到Worker列表
```

### 测试任务提交

在backend中提交任务：
```python
from app.core.celery_app import celery_app

# 提交向量化任务
result = celery_app.send_task('embed_document', args=[document_id])
print(f"任务ID: {result.id}")
```

在Flower中查看任务状态。

## ⚠️ 故障排除

### 问题1：Worker无法连接Redis

**错误：** `Error: [Errno 111] Connection refused`

**解决：**
```bash
# 检查Redis
sudo systemctl status redis

# 检查端口
netstat -tlnp | grep 6379

# 测试连接
redis-cli ping
```

### 问题2：Worker找不到backend模块

**错误：** `ModuleNotFoundError: No module named 'app'`

**解决：**
```bash
# 检查PYTHONPATH
echo $PYTHONPATH

# 手动设置
export PYTHONPATH="/path/to/celery-service:/path/to/backend:$PYTHONPATH"

# 或在启动脚本中设置
```

### 问题3：Flower无法访问

**错误：** 浏览器无法打开 `http://localhost:5555`

**解决：**
```bash
# 检查Flower进程
ps aux | grep flower

# 检查端口
netstat -tlnp | grep 5555

# 查看Flower日志
tail -f logs/flower.log
```

### 问题4：任务一直处于PENDING状态

**原因：** Worker未启动或未订阅队列

**解决：**
```bash
# 确认Worker运行
celery -A celery_app inspect active

# 查看队列
celery -A celery_app inspect registered

# 重启Worker
sudo systemctl restart celery-worker
```

## 📈 性能监控

### 关键指标

在Flower中监控：

1. **Worker状态**
   - 活跃/离线状态
   - 负载情况
   - 内存使用

2. **任务统计**
   - 成功/失败数量
   - 平均处理时间
   - 重试次数

3. **队列状态**
   - 待处理任务数
   - 处理速率
   - 延迟时间

## 🔄 扩展部署

### 增加Worker实例

```bash
# 启动多个Worker实例
celery -A celery_app worker --hostname=worker1@%h
celery -A celery_app worker --hostname=worker2@%h
celery -A celery_app worker --hostname=worker3@%h
```

### 负载均衡

Redis会自动将任务分发给可用的Worker。

## 📝 与Backend的对比

| 特性 | Backend集成 | 独立服务 |
|------|------------|----------|
| **HTTP性能** | 受影响 ⚠️ | 无影响 ✅ |
| **Worker扩展** | 困难 | 容易 ✅ |
| **独立重启** | 不可以 | 可以 ✅ |
| **监控稳定** | 一般 | 优秀 ✅ |
| **部署复杂度** | 简单 | 中等 |

## 🔗 相关服务

- **Backend**: 端口 8000
- **Redis**: 端口 6379
- **MySQL**: 端口 3306
- **Flower**: 端口 5555

---

## 📋 检查清单

- [ ] Redis已启动
- [ ] 环境变量已配置
- [ ] Worker已启动
- [ ] Flower已启动
- [ ] 可以访问Flower面板
- [ ] 任务可以正常执行

---

**服务正常运行标志：**
```
[INFO/MainProcess] Connected to redis://localhost:6379//
[INFO/MainProcess] celery@hostname ready.
🌸 Flower监控面板: http://localhost:5555/flower
```

有问题请查看日志或联系管理员！

