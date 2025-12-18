# Redis 缓存

## 概述

Redis 是一个开源的内存数据结构存储系统,可以用作数据库、缓存和消息代理。CodeHubot 平台使用 Redis 实现缓存、会话存储和异步任务队列。

## Redis 在系统中的应用

### 应用场景

```
┌─────────────────────────────────────────────────────────┐
│                     Redis 应用场景                       │
├─────────────────────────────────────────────────────────┤
│  1. 缓存层                                              │
│     ├── 用户信息缓存                                    │
│     ├── 设备状态缓存                                    │
│     ├── API 响应缓存                                    │
│     └── 数据库查询结果缓存                              │
│                                                         │
│  2. 会话存储                                            │
│     ├── 用户登录会话                                    │
│     ├── Token 黑名单                                    │
│     └── 临时权限                                        │
│                                                         │
│  3. 消息队列                                            │
│     ├── Celery 任务队列                                 │
│     ├── 异步任务结果                                    │
│     └── 事件通知队列                                    │
│                                                         │
│  4. 计数器和限流                                        │
│     ├── API 调用次数统计                                │
│     ├── 访问频率限制                                    │
│     └── 实时在线用户数                                  │
│                                                         │
│  5. 分布式锁                                            │
│     ├── 防止并发操作                                    │
│     ├── 资源互斥访问                                    │
│     └── 任务去重                                        │
└─────────────────────────────────────────────────────────┘
```

## Docker 部署

### docker-compose 配置

```yaml
redis:
  image: redis:7-alpine
  container_name: codehubot-redis
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  networks:
    - aiot-network
  command: redis-server --appendonly yes --requirepass your-password
  healthcheck:
    test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
    interval: 10s
    timeout: 3s
    retries: 5
  restart: unless-stopped
```

### Redis 配置文件

可选创建 `redis.conf`:

```conf
# 绑定地址
bind 0.0.0.0

# 端口
port 6379

# 密码认证
requirepass your-strong-password

# 持久化配置
appendonly yes
appendfilename "appendonly.aof"

# RDB 快照
save 900 1      # 900秒内至少1个key变化
save 300 10     # 300秒内至少10个key变化
save 60 10000   # 60秒内至少10000个key变化

# 最大内存
maxmemory 2gb

# 内存淘汰策略
maxmemory-policy allkeys-lru

# 日志
loglevel notice
logfile ""
```

## Python 客户端

### 安装

```bash
pip install redis
```

### 基本连接

```python
import redis
from app.core.config import settings

# 创建 Redis 连接池
redis_pool = redis.ConnectionPool(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password,
    db=0,
    decode_responses=True  # 自动解码为字符串
)

# 获取 Redis 客户端
redis_client = redis.Redis(connection_pool=redis_pool)

# 测试连接
redis_client.ping()  # 返回 True
```

## 缓存应用

### 1. 用户信息缓存

```python
import json
from datetime import timedelta

class UserCache:
    """用户缓存管理"""
    
    @staticmethod
    def get_user_cache_key(user_id: int) -> str:
        """生成缓存键"""
        return f"user:{user_id}"
    
    @staticmethod
    def set_user(user_id: int, user_data: dict, expire: int = 3600):
        """缓存用户信息"""
        key = UserCache.get_user_cache_key(user_id)
        redis_client.setex(
            key,
            expire,
            json.dumps(user_data)
        )
    
    @staticmethod
    def get_user(user_id: int) -> dict:
        """获取缓存的用户信息"""
        key = UserCache.get_user_cache_key(user_id)
        data = redis_client.get(key)
        return json.loads(data) if data else None
    
    @staticmethod
    def delete_user(user_id: int):
        """删除用户缓存"""
        key = UserCache.get_user_cache_key(user_id)
        redis_client.delete(key)

# 使用示例
# 设置缓存
UserCache.set_user(123, {"name": "Alice", "email": "alice@example.com"})

# 获取缓存
user = UserCache.get_user(123)

# 删除缓存
UserCache.delete_user(123)
```

### 2. 装饰器缓存

```python
import functools
import hashlib
import json

def cache_result(expire: int = 300):
    """缓存函数结果的装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"cache:{func.__name__}:{hashlib.md5(str((args, kwargs)).encode()).hexdigest()}"
            
            # 尝试从缓存获取
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            redis_client.setex(
                cache_key,
                expire,
                json.dumps(result)
            )
            
            return result
        return wrapper
    return decorator

# 使用示例
@cache_result(expire=600)
def get_devices(user_id: int):
    """获取用户设备列表（会被缓存10分钟）"""
    devices = db.query(Device).filter(Device.user_id == user_id).all()
    return [device.to_dict() for device in devices]
```

### 3. 查询缓存模式

```python
def get_device_with_cache(device_id: int):
    """获取设备（优先从缓存）"""
    cache_key = f"device:{device_id}"
    
    # 1. 尝试从缓存获取
    cached = redis_client.get(cache_key)
    if cached:
        logger.info(f"✅ 缓存命中: {cache_key}")
        return json.loads(cached)
    
    # 2. 缓存未命中，查询数据库
    logger.info(f"❌ 缓存未命中: {cache_key}")
    device = db.query(Device).filter(Device.id == device_id).first()
    
    if device:
        # 3. 存入缓存
        redis_client.setex(
            cache_key,
            3600,  # 1小时
            json.dumps(device.to_dict())
        )
    
    return device.to_dict() if device else None
```

## 会话存储

### Token 黑名单

```python
def revoke_token(token: str, expire_time: int):
    """将 Token 加入黑名单"""
    key = f"token:blacklist:{token}"
    redis_client.setex(key, expire_time, "1")

def is_token_revoked(token: str) -> bool:
    """检查 Token 是否被撤销"""
    key = f"token:blacklist:{token}"
    return redis_client.exists(key) > 0

# 使用示例
# 撤销 Token
revoke_token("eyJhbGci...", 86400)  # 24小时后自动删除

# 验证 Token
if is_token_revoked(token):
    raise HTTPException(status_code=401, detail="Token已被撤销")
```

### 用户会话

```python
def create_session(user_id: int, session_data: dict, expire: int = 86400):
    """创建用户会话"""
    session_id = str(uuid.uuid4())
    key = f"session:{session_id}"
    
    redis_client.setex(
        key,
        expire,
        json.dumps({**session_data, "user_id": user_id})
    )
    
    return session_id

def get_session(session_id: str) -> dict:
    """获取会话信息"""
    key = f"session:{session_id}"
    data = redis_client.get(key)
    return json.loads(data) if data else None

def delete_session(session_id: str):
    """删除会话"""
    key = f"session:{session_id}"
    redis_client.delete(key)
```

## 计数器和限流

### API 调用限流

```python
from fastapi import HTTPException, Request

def rate_limit(key: str, max_requests: int = 100, window: int = 60):
    """限流装饰器
    
    Args:
        key: 限流键（如用户ID、IP地址）
        max_requests: 最大请求数
        window: 时间窗口（秒）
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # 获取客户端标识
            client_id = key if key else request.client.host
            rate_key = f"rate_limit:{client_id}:{func.__name__}"
            
            # 获取当前计数
            count = redis_client.get(rate_key)
            
            if count and int(count) >= max_requests:
                raise HTTPException(
                    status_code=429,
                    detail=f"请求过于频繁，请{window}秒后重试"
                )
            
            # 增加计数
            pipe = redis_client.pipeline()
            pipe.incr(rate_key)
            pipe.expire(rate_key, window)
            pipe.execute()
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@router.post("/api/data")
@rate_limit(key="user_123", max_requests=10, window=60)
async def create_data(request: Request):
    """创建数据（每分钟最多10次）"""
    return {"message": "成功"}
```

### 实时统计

```python
def increment_api_calls(endpoint: str):
    """增加 API 调用次数"""
    key = f"stats:api:{endpoint}:{datetime.now().strftime('%Y%m%d')}"
    redis_client.incr(key)
    redis_client.expire(key, 86400 * 7)  # 保留7天

def get_api_stats(endpoint: str, days: int = 7):
    """获取 API 调用统计"""
    stats = {}
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
        key = f"stats:api:{endpoint}:{date}"
        count = redis_client.get(key)
        stats[date] = int(count) if count else 0
    return stats
```

## 分布式锁

### 实现分布式锁

```python
import time
import uuid

class RedisLock:
    """Redis 分布式锁"""
    
    def __init__(self, key: str, expire: int = 30):
        self.key = f"lock:{key}"
        self.expire = expire
        self.identifier = str(uuid.uuid4())
    
    def acquire(self, timeout: int = 10) -> bool:
        """获取锁"""
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            # 尝试获取锁
            if redis_client.set(self.key, self.identifier, nx=True, ex=self.expire):
                return True
            
            # 等待一小段时间再重试
            time.sleep(0.1)
        
        return False
    
    def release(self):
        """释放锁"""
        # 使用 Lua 脚本确保原子性
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        redis_client.eval(lua_script, 1, self.key, self.identifier)
    
    def __enter__(self):
        if not self.acquire():
            raise Exception("无法获取锁")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

# 使用示例
with RedisLock("device:123:update"):
    # 临界区代码
    update_device(123)
```

## Celery 任务队列

### Celery 配置

```python
from celery import Celery

app = Celery(
    'codehubot',
    broker='redis://localhost:6379/0',      # 任务队列
    backend='redis://localhost:6379/1'      # 结果存储
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
)
```

### 定义任务

```python
@app.task
def send_email(to: str, subject: str, body: str):
    """发送邮件任务"""
    # 执行发送邮件
    logger.info(f"发送邮件: {to}")
    return {"status": "success"}

# 调用任务
send_email.delay("user@example.com", "标题", "内容")
```

## 性能优化

### 1. 使用管道

```python
# ❌ 效率低（多次网络请求）
for i in range(1000):
    redis_client.set(f"key:{i}", i)

# ✅ 使用管道（一次网络请求）
pipe = redis_client.pipeline()
for i in range(1000):
    pipe.set(f"key:{i}", i)
pipe.execute()
```

### 2. 批量操作

```python
# 批量获取
keys = [f"user:{i}" for i in range(100)]
values = redis_client.mget(keys)

# 批量设置
mapping = {f"user:{i}": f"value_{i}" for i in range(100)}
redis_client.mset(mapping)
```

### 3. 合理设置过期时间

```python
# 设置过期时间，避免内存泄漏
redis_client.setex("temp_key", 300, "value")  # 5分钟后自动删除

# 或者使用 expire
redis_client.set("key", "value")
redis_client.expire("key", 300)
```

## 监控和维护

### 监控命令

```bash
# 查看 Redis 信息
redis-cli INFO

# 监控实时命令
redis-cli MONITOR

# 查看慢日志
redis-cli SLOWLOG GET 10

# 查看内存使用
redis-cli INFO memory

# 查看客户端连接
redis-cli CLIENT LIST
```

### 内存优化

```bash
# 查看键空间
redis-cli DBSIZE

# 查看大键
redis-cli --bigkeys

# 分析内存
redis-cli --memkeys
```

## 相关文档

- [Celery异步任务](./Celery异步任务.md) - 异步任务详解
- [整体架构设计](../02_系统架构/整体架构设计.md) - 系统架构
- [Docker容器化部署](../03_部署运维/Docker容器化部署.md) - Redis 容器部署
