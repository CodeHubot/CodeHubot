# Celery 异步任务详解

## 概述

Celery 是一个基于分布式消息传递的异步任务队列/作业队列，用于处理耗时的后台任务。在 CodeHubot 项目中，Celery 用于处理文档向量化、邮件发送等耗时操作。本文档适合教学使用。

## 为什么需要异步任务？

### 同步处理的问题

```python
# ❌ 同步处理（阻塞）
@app.post("/documents")
async def upload_document(file: UploadFile):
    # 保存文件
    save_file(file)
    
    # 向量化处理（耗时3-5分钟）
    vectorize_document(file)  # ⚠️ 用户需要等待3-5分钟
    
    return {"message": "上传成功"}
```

### 异步处理的优势

```python
# ✅ 异步处理（非阻塞）
@app.post("/documents")
async def upload_document(file: UploadFile):
    # 保存文件
    save_file(file)
    
    # 提交异步任务
    vectorize_task.delay(file.filename)  # 立即返回
    
    return {"message": "上传成功，正在处理中"}
```

**优势**：
- ✅ 用户体验好：立即响应，不需要等待
- ✅ 资源利用高：可以并发处理多个任务
- ✅ 系统可靠：任务失败可以重试
- ✅ 易于扩展：增加 Worker 即可提升处理能力

## Celery 架构

```
┌─────────────────────────────────────────────────────────┐
│                    Celery 架构                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Web 应用 (FastAPI)                                     │
│       │                                                 │
│       │ 1. 发送任务                                     │
│       ↓                                                 │
│  ┌──────────────┐                                       │
│  │ Message Broker │  (Redis/RabbitMQ)                  │
│  │  消息队列      │                                     │
│  └──────┬───────┘                                       │
│         │ 2. 存储任务                                   │
│         │                                               │
│  ┌──────┴───────┐                                       │
│  │ Celery Worker │  (可多个)                           │
│  │  任务执行器   │                                     │
│  └──────┬───────┘                                       │
│         │ 3. 执行任务                                   │
│         │                                               │
│  ┌──────┴───────┐                                       │
│  │ Result Backend │  (Redis/数据库)                    │
│  │  结果存储      │                                     │
│  └──────────────┘                                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 核心组件

1. **Producer（生产者）**：发送任务的应用（FastAPI）
2. **Broker（消息代理）**：存储任务的队列（Redis）
3. **Worker（工作者）**：执行任务的进程
4. **Backend（结果后端）**：存储任务结果（Redis）

## 安装和配置

### 1. 安装 Celery

```bash
pip install celery
pip install redis  # 使用 Redis 作为 Broker
```

### 2. 创建 Celery 应用

**文件位置**: `service/celery-service/celery_app.py`

```python
from celery import Celery
from kombu import Exchange, Queue

# 创建 Celery 应用
app = Celery(
    'codehubot',
    broker='redis://localhost:6379/0',      # 消息队列
    backend='redis://localhost:6379/1'      # 结果存储
)

# 配置
app.conf.update(
    # 任务序列化
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # 时区
    timezone='Asia/Shanghai',
    enable_utc=True,
    
    # 任务结果过期时间（秒）
    result_expires=3600,
    
    # 任务超时时间
    task_soft_time_limit=300,    # 5分钟软限制
    task_time_limit=360,          # 6分钟硬限制
    
    # Worker 配置
    worker_prefetch_multiplier=4,  # 预取任务数
    worker_max_tasks_per_child=1000,  # Worker 处理1000个任务后重启
    
    # 任务路由
    task_routes={
        'tasks.embedding.*': {'queue': 'embedding'},
        'tasks.email.*': {'queue': 'email'},
    },
    
    # 定义队列
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('embedding', Exchange('embedding'), routing_key='embedding'),
        Queue('email', Exchange('email'), routing_key='email'),
    ),
)

# 自动发现任务
app.autodiscover_tasks(['tasks'])
```

## 定义任务

### 1. 基本任务

```python
from celery_app import app
import time

@app.task
def add(x, y):
    """加法任务"""
    return x + y

@app.task
def send_email(to: str, subject: str, body: str):
    """发送邮件任务"""
    time.sleep(2)  # 模拟发送邮件
    print(f"邮件已发送到 {to}")
    return {"status": "success", "to": to}

@app.task
def process_data(data: dict):
    """处理数据任务"""
    time.sleep(5)  # 模拟耗时处理
    result = {
        "processed": True,
        "count": len(data)
    }
    return result
```

### 2. 带参数的任务

```python
@app.task(
    name='tasks.embedding.vectorize',  # 任务名称
    bind=True,                         # 绑定任务实例
    max_retries=3,                     # 最大重试次数
    default_retry_delay=60             # 重试延迟（秒）
)
def vectorize_document(self, document_id: int):
    """文档向量化任务"""
    try:
        # 获取文档
        document = get_document(document_id)
        
        # 向量化处理
        embeddings = generate_embeddings(document.content)
        
        # 保存到数据库
        save_embeddings(document_id, embeddings)
        
        return {
            "success": True,
            "document_id": document_id,
            "embeddings_count": len(embeddings)
        }
    
    except Exception as exc:
        # 重试
        raise self.retry(exc=exc, countdown=60)
```

### 3. 进度跟踪

```python
from celery import Task

class CallbackTask(Task):
    """支持进度回调的任务基类"""
    def on_success(self, retval, task_id, args, kwargs):
        """任务成功时回调"""
        print(f"任务 {task_id} 成功完成")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败时回调"""
        print(f"任务 {task_id} 失败: {exc}")

@app.task(
    base=CallbackTask,
    bind=True
)
def long_running_task(self, total_steps: int):
    """长时间运行的任务（带进度）"""
    for i in range(total_steps):
        # 更新进度
        self.update_state(
            state='PROGRESS',
            meta={
                'current': i + 1,
                'total': total_steps,
                'percent': int((i + 1) / total_steps * 100)
            }
        )
        
        # 模拟处理
        time.sleep(1)
    
    return {'status': 'completed', 'result': total_steps}
```

## 调用任务

### 1. 异步调用

```python
# delay() - 简单调用
result = add.delay(4, 4)

# apply_async() - 高级调用
result = add.apply_async(
    args=[4, 4],              # 位置参数
    kwargs={'x': 4, 'y': 4},  # 关键字参数
    countdown=10,              # 延迟10秒执行
    expires=300,               # 5分钟后过期
    retry=True,                # 允许重试
    retry_policy={
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    }
)
```

### 2. 获取结果

```python
# 发送任务
result = add.delay(4, 4)

# 任务 ID
print(result.id)  # '550e8400-e29b-41d4-a716-446655440000'

# 任务状态
print(result.state)  # 'PENDING', 'STARTED', 'SUCCESS', 'FAILURE'

# 等待结果（阻塞）
value = result.get(timeout=10)
print(value)  # 8

# 检查是否完成
if result.ready():
    print("任务已完成")

# 检查是否成功
if result.successful():
    print("任务成功")

# 获取结果（不阻塞）
if result.ready():
    value = result.result
    print(value)
```

### 3. 在 FastAPI 中使用

```python
from fastapi import FastAPI, BackgroundTasks
from celery.result import AsyncResult

app = FastAPI()

@app.post("/documents/{document_id}/vectorize")
async def vectorize_document_endpoint(document_id: int):
    """触发文档向量化"""
    # 发送异步任务
    task = vectorize_document.delay(document_id)
    
    return {
        "message": "向量化任务已提交",
        "task_id": task.id,
        "status_url": f"/tasks/{task.id}"
    }

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """查询任务状态"""
    task = AsyncResult(task_id, app=celery_app)
    
    if task.state == 'PENDING':
        response = {
            "state": task.state,
            "status": "任务等待中"
        }
    elif task.state == 'PROGRESS':
        response = {
            "state": task.state,
            "current": task.info.get('current', 0),
            "total": task.info.get('total', 1),
            "percent": task.info.get('percent', 0),
            "status": "处理中"
        }
    elif task.state == 'SUCCESS':
        response = {
            "state": task.state,
            "result": task.result,
            "status": "已完成"
        }
    elif task.state == 'FAILURE':
        response = {
            "state": task.state,
            "error": str(task.info),
            "status": "失败"
        }
    else:
        response = {
            "state": task.state,
            "status": task.state
        }
    
    return response
```

## 定时任务

### 1. 使用 Celery Beat

```python
from celery.schedules import crontab

# 配置定时任务
app.conf.beat_schedule = {
    # 每天凌晨3点执行
    'cleanup-expired-tokens': {
        'task': 'tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=3, minute=0),
    },
    
    # 每小时执行
    'update-device-status': {
        'task': 'tasks.update_device_status',
        'schedule': crontab(minute=0),  # 每小时的第0分钟
    },
    
    # 每30分钟执行
    'sync-data': {
        'task': 'tasks.sync_data',
        'schedule': 1800.0,  # 秒
    },
    
    # 每周一上午10点执行
    'weekly-report': {
        'task': 'tasks.generate_weekly_report',
        'schedule': crontab(hour=10, minute=0, day_of_week=1),
    },
}
```

### 2. 定义定时任务

```python
@app.task
def cleanup_expired_tokens():
    """清理过期的 Token"""
    from datetime import datetime
    
    expired_count = redis_client.scan_iter("token:*")
    count = 0
    
    for key in expired_count:
        ttl = redis_client.ttl(key)
        if ttl < 0:  # 已过期但未删除
            redis_client.delete(key)
            count += 1
    
    return {"deleted": count}

@app.task
def update_device_status():
    """更新设备在线状态"""
    from app.models.device import Device
    from datetime import datetime, timedelta
    
    # 5分钟内无心跳视为离线
    threshold = datetime.utcnow() - timedelta(minutes=5)
    
    Device.query.filter(
        Device.last_seen < threshold,
        Device.online == True
    ).update({'online': False})
    
    db.commit()
    return {"updated": "success"}
```

## 任务链和工作流

### 1. 任务链（Chain）

```python
from celery import chain

# 串行执行任务
workflow = chain(
    task1.s(arg1),
    task2.s(),
    task3.s()
)
result = workflow()

# 示例：处理文档流程
process_workflow = chain(
    download_document.s(url),      # 1. 下载文档
    extract_text.s(),               # 2. 提取文本
    vectorize.s(),                  # 3. 向量化
    save_to_db.s()                  # 4. 保存到数据库
)
result = process_workflow()
```

### 2. 任务组（Group）

```python
from celery import group

# 并行执行任务
job = group(
    task1.s(1),
    task2.s(2),
    task3.s(3)
)
result = job()

# 示例：批量处理
batch_job = group([
    vectorize_document.s(doc_id)
    for doc_id in document_ids
])
result = batch_job()
```

### 3. 复杂工作流

```python
from celery import chain, group, chord

# Chord：先并行执行，再汇总结果
workflow = chord([
    task1.s(1),
    task2.s(2),
    task3.s(3)
])(summarize.s())  # 汇总结果

# 示例：批量处理后汇总
batch_process = chord([
    process_item.s(item_id)
    for item_id in item_ids
])(generate_report.s())  # 所有处理完成后生成报告
```

## CodeHubot 项目实践

### 文档向量化任务

```python
# tasks/embedding_tasks.py
from celery_app import app
from app.services.embedding_service import EmbeddingService
from app.models.document import Document
from app.core.database import SessionLocal

@app.task(bind=True, max_retries=3)
def vectorize_document_task(self, document_id: int):
    """文档向量化异步任务"""
    db = SessionLocal()
    
    try:
        # 获取文档
        document = db.query(Document).filter(
            Document.id == document_id
        ).first()
        
        if not document:
            return {"error": "文档不存在"}
        
        # 更新状态
        document.embedding_status = 'processing'
        db.commit()
        
        # 向量化
        embedding_service = EmbeddingService()
        chunks = embedding_service.chunk_document(document.content)
        
        total = len(chunks)
        for i, chunk in enumerate(chunks):
            # 生成向量
            vector = embedding_service.generate_embedding(chunk)
            
            # 保存
            embedding_service.save_embedding(
                document_id=document_id,
                chunk_text=chunk,
                embedding=vector
            )
            
            # 更新进度
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': i + 1,
                    'total': total,
                    'percent': int((i + 1) / total * 100)
                }
            )
        
        # 更新状态为完成
        document.embedding_status = 'completed'
        document.chunk_count = total
        db.commit()
        
        return {
            "success": True,
            "document_id": document_id,
            "chunks": total
        }
    
    except Exception as exc:
        # 更新状态为失败
        if document:
            document.embedding_status = 'failed'
            db.commit()
        
        # 重试
        raise self.retry(exc=exc, countdown=60)
    
    finally:
        db.close()
```

## 启动 Worker

### 1. 启动命令

```bash
# 基本启动
celery -A celery_app worker --loglevel=info

# 指定队列
celery -A celery_app worker --loglevel=info -Q embedding,email

# 指定并发数
celery -A celery_app worker --loglevel=info --concurrency=4

# 使用 gevent 池（适合 I/O 密集型）
celery -A celery_app worker --loglevel=info --pool=gevent --concurrency=100
```

### 2. 启动 Beat（定时任务调度器）

```bash
# 启动 Beat
celery -A celery_app beat --loglevel=info

# 同时启动 Worker 和 Beat
celery -A celery_app worker --beat --loglevel=info
```

### 3. 启动脚本

**文件位置**: `service/celery-service/start_celery.sh`

```bash
#!/bin/bash

# 启动 Celery Worker
celery -A celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=1000 \
    --pidfile=/var/run/celery/worker.pid \
    --logfile=/var/log/celery/worker.log \
    &

# 启动 Celery Beat
celery -A celery_app beat \
    --loglevel=info \
    --pidfile=/var/run/celery/beat.pid \
    --logfile=/var/log/celery/beat.log \
    &

echo "Celery started"
```

## 监控和管理

### 1. Flower（Web 监控）

```bash
# 安装
pip install flower

# 启动 Flower
celery -A celery_app flower --port=5555

# 访问
# http://localhost:5555
```

Flower 功能：
- ✅ 实时监控任务状态
- ✅ 查看任务历史
- ✅ Worker 状态监控
- ✅ 任务统计图表

### 2. 命令行工具

```bash
# 查看活跃任务
celery -A celery_app inspect active

# 查看已注册的任务
celery -A celery_app inspect registered

# 查看统计信息
celery -A celery_app inspect stats

# 撤销任务
celery -A celery_app revoke <task_id>

# 清空队列
celery -A celery_app purge
```

## 最佳实践

### 1. 任务设计

```python
# ✅ 任务应该是幂等的（多次执行结果相同）
@app.task
def update_user_status(user_id, status):
    user = User.query.get(user_id)
    if user:
        user.status = status
        db.commit()

# ✅ 任务应该是原子的（不可分割）
@app.task
def process_order(order_id):
    with transaction():
        # 所有操作要么全成功，要么全失败
        pass

# ❌ 避免任务过大
@app.task
def process_all_users():  # 不好
    users = User.query.all()  # 可能有几百万用户
    for user in users:
        process_user(user)

# ✅ 分批处理
@app.task
def process_users_batch(offset, limit):
    users = User.query.offset(offset).limit(limit).all()
    for user in users:
        process_user(user)
```

### 2. 错误处理

```python
@app.task(bind=True, max_retries=3, default_retry_delay=60)
def fragile_task(self, data):
    try:
        # 可能失败的操作
        risky_operation(data)
    except TemporaryError as exc:
        # 临时错误，重试
        raise self.retry(exc=exc)
    except PermanentError:
        # 永久错误，不重试
        logger.error("永久错误，停止重试")
        return {"error": "permanent_failure"}
```

### 3. 资源管理

```python
@app.task
def process_data(data_id):
    db = SessionLocal()
    try:
        # 使用数据库
        data = db.query(Data).get(data_id)
        process(data)
        db.commit()
    finally:
        # 确保关闭连接
        db.close()
```

## 教学要点总结

### 核心概念
1. **异步任务队列**：解耦耗时操作
2. **Broker**：消息队列（Redis）
3. **Worker**：任务执行器
4. **Result Backend**：结果存储

### 常用场景
- 📧 发送邮件
- 📄 文档处理
- 🔢 数据分析
- 🔄 定时任务
- 📊 报表生成

### 最佳实践
- ✅ 任务幂等性
- ✅ 错误重试
- ✅ 进度跟踪
- ✅ 资源管理
- ✅ 监控告警

## 相关文档

- [Redis缓存](./Redis缓存.md) - Celery 使用 Redis 作为 Broker
- [FastAPI框架](./FastAPI框架.md) - 在 FastAPI 中集成 Celery
- [后端架构](../02_系统架构/后端架构.md) - 异步任务在系统中的角色
