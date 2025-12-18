# Token 管理

## 概述

CodeHubot 平台使用 JWT (JSON Web Token) 作为身份认证和授权的核心机制。JWT 是一种开放标准 (RFC 7519)，用于在各方之间安全地传输信息。

## JWT 基础

### 什么是 JWT？

JWT 是一个由三部分组成的字符串，用点 (`.`) 分隔：

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c

├─ Header (头部)
├─ Payload (载荷)
└─ Signature (签名)
```

### JWT 结构解析

#### 1. Header（头部）

包含 Token 类型和加密算法：

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

#### 2. Payload（载荷）

包含声明（Claims），即实际传递的数据：

```json
{
  "sub": "12345",           // Subject: 用户ID
  "type": "access",         // 自定义: Token类型
  "role": "admin",          // 自定义: 用户角色
  "exp": 1735401600,        // Expiration: 过期时间
  "iat": 1735315200         // Issued At: 签发时间
}
```

#### 3. Signature（签名）

使用密钥对 Header 和 Payload 进行签名，防止篡改：

```
HMACSHA256(
  base64UrlEncode(header) + "." +
  base64UrlEncode(payload),
  secret_key
)
```

## Token 类型

### Access Token（访问令牌）

用于访问受保护的资源，**有效期较短**。

#### 配置

```python
# backend/app/core/config.py
class Settings:
    access_token_expire_minutes: int = 60 * 24  # 24小时
    algorithm: str = "HS256"
    secret_key: str  # 从环境变量读取
```

#### 生成

**文件位置**: `backend/app/core/security.py`

```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建 access token"""
    to_encode = data.copy()
    
    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    # 添加必要字段
    if "type" not in to_encode:
        to_encode["type"] = "access"
    to_encode["exp"] = expire
    
    # 编码生成 JWT
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=settings.algorithm
    )
    
    return encoded_jwt
```

#### 使用场景

- ✅ API 请求认证
- ✅ 用户身份验证
- ✅ 权限检查

### Refresh Token（刷新令牌）

用于获取新的 Access Token，**有效期较长**。

#### 配置

```python
class Settings:
    refresh_token_expire_minutes: int = 60 * 24 * 7  # 7天
```

#### 生成

```python
def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建 refresh token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.refresh_token_expire_minutes
        )
    
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=settings.algorithm
    )
    
    return encoded_jwt
```

#### 使用场景

- ✅ 刷新 Access Token
- ✅ 保持用户登录状态
- ❌ 不能直接用于 API 访问

### Password Reset Token（密码重置令牌）

用于密码重置流程，**有效期很短**。

#### 配置

```python
# backend/app/core/constants.py
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = 30  # 30分钟
```

#### 生成

```python
# 生成密码重置 Token
reset_token = create_access_token(
    data={
        "sub": str(user.id),
        "type": "password_reset"
    },
    expires_delta=timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
)
```

#### 验证

```python
# 验证密码重置 Token
payload = verify_token(reset_token, token_type="password_reset")
```

## Token 验证

### 验证流程

```
1. 从请求头提取 Token
   ↓
2. 解码 JWT
   ↓
3. 验证签名
   ↓
4. 检查过期时间
   ↓
5. 验证 Token 类型
   ↓
6. 提取用户信息
   ↓
7. 查询数据库验证用户
   ↓
8. 检查用户状态
   ↓
9. 返回用户对象
```

### 验证实现

**文件位置**: `backend/app/core/security.py`

```python
def verify_token(token: str, token_type: Optional[str] = "access") -> dict:
    """验证 token
    
    Args:
        token: JWT token
        token_type: token类型（access、refresh、password_reset）
        
    Returns:
        dict: token payload
        
    Raises:
        HTTPException: token无效或类型不匹配
    """
    try:
        # 解码 JWT
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        
        # 验证 Token 类型
        if token_type is not None:
            payload_type = payload.get("type")
            if payload_type != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"无效的token类型，期望: {token_type}，实际: {payload_type}"
                )
        
        return payload
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据"
        )
```

### FastAPI 依赖注入验证

**文件位置**: `backend/app/core/deps.py`

```python
from fastapi.security import OAuth2PasswordBearer

# OAuth2 密码流
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户"""
    
    # 1. 验证 Token
    payload = verify_token(token, token_type="access")
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="无效的认证凭据")
    
    # 2. 查询用户
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    # 3. 检查用户状态
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")
    
    return user
```

### 在路由中使用

```python
from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/devices")
async def get_devices(
    current_user: User = Depends(get_current_user),  # 自动验证Token
    db: Session = Depends(get_db)
):
    """获取设备列表（需要认证）"""
    devices = db.query(Device).filter(
        Device.user_id == current_user.id
    ).all()
    
    return {"devices": devices}
```

## Token 刷新机制

### 为什么需要刷新？

- **安全性**: Access Token 短期有效，即使泄露影响也较小
- **用户体验**: Refresh Token 长期有效，避免频繁登录
- **灵活性**: 可以单独撤销 Refresh Token

### 刷新流程

```
客户端                    服务器
  |                          |
  |--请求 API--------------->|
  |                          |--验证 access_token
  |<-401 Token过期-----------|
  |                          |
  |--POST /auth/refresh----->|
  |  {refresh_token}         |
  |                          |--验证 refresh_token
  |                          |--生成新的 access_token
  |                          |
  |<-返回新 token------------|
  |  {access_token}          |
  |                          |
  |--重试原请求------------->|
  |  (使用新token)           |
  |<-请求成功----------------|
```

### 后端实现

```python
@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """刷新 access token"""
    
    # 1. 验证 refresh_token
    payload = verify_token(refresh_token, token_type="refresh")
    user_id = payload.get("sub")
    
    # 2. 查询用户
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="无效的刷新令牌")
    
    # 3. 生成新的 access_token
    new_access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    
    return {"access_token": new_access_token, "token_type": "bearer"}
```

### 前端自动刷新

**文件位置**: `frontend/src/utils/request.js`

```javascript
// 响应拦截器 - 自动刷新Token
request.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config
    
    // Token过期且未重试过
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        // 获取 refresh_token
        const refreshToken = localStorage.getItem('admin_refresh_token')
        
        // 请求刷新
        const response = await axios.post('/api/auth/refresh', {
          refresh_token: refreshToken
        })
        
        // 保存新 token
        const newAccessToken = response.data.access_token
        localStorage.setItem('admin_access_token', newAccessToken)
        
        // 更新请求头
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        
        // 重试原请求
        return request(originalRequest)
      } catch (refreshError) {
        // 刷新失败，跳转登录
        localStorage.clear()
        router.push('/admin/login')
        return Promise.reject(refreshError)
      }
    }
    
    return Promise.reject(error)
  }
)
```

## Token 存储

### 前端存储方案对比

| 存储方式 | 优点 | 缺点 | 推荐场景 |
|---------|------|------|---------|
| **localStorage** | 持久化、API简单 | 易受XSS攻击 | 低敏感度应用 ✅ |
| **sessionStorage** | 会话级、相对安全 | 关闭页面失效 | 短期会话 |
| **Cookie (HttpOnly)** | 防XSS攻击 | 需后端配合、有CSRF风险 | 高安全要求 |
| **Memory (变量)** | 最安全 | 刷新页面失效 | 单页应用 |

### 当前实现

CodeHubot 使用 **localStorage** 存储 Token：

```javascript
// 存储
localStorage.setItem('admin_access_token', accessToken)
localStorage.setItem('admin_refresh_token', refreshToken)

// 读取
const token = localStorage.getItem('admin_access_token')

// 清除
localStorage.removeItem('admin_access_token')
localStorage.removeItem('admin_refresh_token')
```

### 安全建议

1. **生产环境必须使用 HTTPS**
2. 避免在 URL 中传递 Token
3. 定期刷新 Token
4. 实施 XSS 防护（CSP、输入验证）
5. 考虑使用 HttpOnly Cookie（防XSS）

## Token 撤销

### 无状态 Token 的挑战

JWT 是无状态的，服务器不保存 Token。这带来一个问题：**如何撤销已发布的 Token？**

### 解决方案

#### 方案1：Token黑名单（推荐）

使用 Redis 存储已撤销的 Token：

```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def revoke_token(token: str):
    """撤销 Token"""
    # 解析 Token 获取过期时间
    payload = jwt.decode(token, options={"verify_signature": False})
    exp = payload.get("exp")
    
    # 计算剩余有效期
    ttl = exp - int(datetime.utcnow().timestamp())
    
    if ttl > 0:
        # 加入黑名单，过期后自动删除
        redis_client.setex(f"blacklist:{token}", ttl, "1")

def is_token_revoked(token: str) -> bool:
    """检查 Token 是否已撤销"""
    return redis_client.exists(f"blacklist:{token}") > 0

# 验证时检查黑名单
def verify_token_with_blacklist(token: str):
    if is_token_revoked(token):
        raise HTTPException(status_code=401, detail="Token已被撤销")
    
    return verify_token(token)
```

#### 方案2：版本号机制

在数据库中为每个用户维护 Token 版本号：

```python
# 用户表增加字段
class User(Base):
    token_version: int = Column(Integer, default=1)

# 生成 Token 时包含版本号
def create_access_token_with_version(user: User):
    return create_access_token(
        data={
            "sub": str(user.id),
            "version": user.token_version
        }
    )

# 验证时检查版本号
def verify_token_version(token: str, user: User):
    payload = verify_token(token)
    token_version = payload.get("version", 0)
    
    if token_version != user.token_version:
        raise HTTPException(status_code=401, detail="Token版本已过期")

# 撤销所有 Token（递增版本号）
def revoke_all_user_tokens(user: User, db: Session):
    user.token_version += 1
    db.commit()
```

#### 方案3：短期 Token + 频繁刷新

- Access Token 有效期设为 15 分钟
- 使用 Refresh Token 自动刷新
- 撤销时只需禁用用户账户

## Token 安全最佳实践

### 1. 密钥管理

```python
# ❌ 错误：硬编码密钥
SECRET_KEY = "my-secret-key"

# ✅ 正确：从环境变量读取
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str  # 从 .env 文件读取
    
    class Config:
        env_file = ".env"
```

### 2. 算法选择

```python
# ✅ 推荐：HS256（对称加密，简单高效）
algorithm = "HS256"

# ⚠️ 可选：RS256（非对称加密，更安全但复杂）
# 需要公钥/私钥对
```

### 3. 过期时间设置

```python
# ✅ 合理的过期时间
access_token_expire = timedelta(hours=24)       # 1天
refresh_token_expire = timedelta(days=7)        # 7天
password_reset_expire = timedelta(minutes=30)   # 30分钟

# ❌ 避免过长
access_token_expire = timedelta(days=365)  # 太长
```

### 4. Payload 大小

```python
# ✅ 保持 Payload 精简
payload = {
    "sub": "12345",      # 用户ID
    "role": "admin",     # 角色
    "exp": 1735401600    # 过期时间
}

# ❌ 避免存储大量数据
payload = {
    "user": {...},       # 完整用户对象
    "permissions": [...] # 大量权限列表
}
```

### 5. HTTPS 传输

```nginx
# 生产环境强制 HTTPS
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # 将 HTTP 重定向到 HTTPS
    if ($scheme != "https") {
        return 301 https://$server_name$request_uri;
    }
}
```

## 常见问题

### 1. Token 被盗用怎么办？

**防护措施**：
- 使用 HTTPS 防止中间人攻击
- 设置短期 Access Token
- 实施 IP 白名单（可选）
- 异常登录检测

**应急处理**：
- 立即撤销 Token（黑名单/版本号）
- 强制用户重新登录
- 调查安全漏洞

### 2. 如何在多个服务间共享 Token？

**方案**：使用相同的密钥和算法

```python
# 所有微服务使用相同配置
SECRET_KEY = "same-secret-key-for-all-services"
ALGORITHM = "HS256"

# Token 在所有服务间通用
```

### 3. Token 过期时间如何平衡安全和体验？

**推荐配置**：
- **Web 应用**: Access Token 24小时 + Refresh Token 7天
- **移动应用**: Access Token 1小时 + Refresh Token 30天
- **高安全场景**: Access Token 15分钟 + Refresh Token 1天

## 相关文档

- [登录登出机制](./登录登出机制.md) - 完整登录流程
- [权限管理体系](./权限管理体系.md) - 基于Token的权限控制
- [安全规范](../../docs_开发规范/09_安全规范.md) - 安全开发规范
