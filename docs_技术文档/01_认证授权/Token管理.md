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

### 前端自动刷新机制

**文件位置**: `frontend/src/utils/request.js`

#### 1. 刷新状态管理

```javascript
// 是否正在刷新 token
let isRefreshing = false

// 失败的请求队列
let failedRequestsQueue = []

/**
 * 处理失败的请求队列
 */
function processFailedRequestsQueue(error = null) {
  failedRequestsQueue.forEach(callback => {
    callback(error)
  })
  failedRequestsQueue = []
}
```

#### 2. Token 刷新函数

```javascript
/**
 * 刷新 access token
 * @returns {Promise<string>} 新的 access token
 */
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token')
  
  if (!refreshToken) {
    throw new Error('No refresh token available')
  }

  try {
    // 使用原始 axios 发送刷新请求，避免触发拦截器
    const response = await axios.post('/api/auth/refresh', {
      refresh_token: refreshToken
    })

    const { access_token, refresh_token: newRefreshToken } = response.data.data

    // 更新 token
    localStorage.setItem('access_token', access_token)
    if (newRefreshToken) {
      localStorage.setItem('refresh_token', newRefreshToken)
    }

    console.log('✅ Token 刷新成功')
    return access_token
  } catch (error) {
    console.error('❌ Token 刷新失败:', error)
    throw error
  }
}
```

#### 3. 响应拦截器 - 自动刷新与队列管理

```javascript
// 响应拦截器 - 处理 401 错误并自动刷新 Token
request.interceptors.response.use(
  response => response.data,
  async error => {
    const originalRequest = error.config
    
    // 处理 401 错误：尝试刷新 token
    if (error.response?.status === 401 && !originalRequest._retry) {
      
      // 如果正在刷新 token，将请求加入队列
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedRequestsQueue.push((error) => {
            if (error) {
              reject(error)
            } else {
              // 使用新的 token 重试请求
              const token = localStorage.getItem('access_token')
              if (token) {
                originalRequest.headers.Authorization = `Bearer ${token}`
              }
              resolve(request(originalRequest))
            }
          })
        })
      }

      // 标记正在重试
      originalRequest._retry = true
      isRefreshing = true

      try {
        // 尝试刷新 token
        const newAccessToken = await refreshToken()
        
        // 更新原始请求的 token
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        
        // 处理队列中的请求
        processFailedRequestsQueue(null)
        
        // 重试原始请求
        return request(originalRequest)
        
      } catch (refreshError) {
        // token 刷新失败，清除所有 token 并跳转登录页
        console.error('Token 刷新失败，需要重新登录')
        
        // 处理队列中的请求（都失败）
        processFailedRequestsQueue(refreshError)
        
        // 清除所有 token
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        
        // 跳转到统一登录页
        router.push('/login')
        
        ElMessage.error('登录已过期，请重新登录')
        
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    
    return Promise.reject(error)
  }
)
```

#### 4. 并发请求处理

当多个请求同时遇到 401 错误时：

```javascript
// 第 1 个请求触发刷新
Request A (401) → 开始刷新 Token → isRefreshing = true

// 后续请求加入队列
Request B (401) → 加入队列，等待刷新完成
Request C (401) → 加入队列，等待刷新完成
Request D (401) → 加入队列，等待刷新完成

// 刷新成功后，批量重试
刷新成功 → 
  Request A 重试 ✅
  Request B 重试 ✅
  Request C 重试 ✅
  Request D 重试 ✅
```

#### 5. 完整工作流程

```
用户请求 API
  ↓
请求拦截器添加 Authorization: Bearer <access_token>
  ↓
发送请求
  ↓
收到 401 响应（Token 过期）
  ↓
检查 isRefreshing 状态
  ↓
├─ isRefreshing = true （正在刷新）
│   ↓
│   将请求加入队列 failedRequestsQueue
│   ↓
│   等待刷新完成
│   ↓
│   刷新完成后自动重试
│
└─ isRefreshing = false （未在刷新）
    ↓
    标记 isRefreshing = true
    ↓
    调用 POST /api/auth/refresh
    ↓
    ├─ 刷新成功
    │   ↓
    │   更新 localStorage 中的 access_token 和 refresh_token
    │   ↓
    │   使用新 token 重试原始请求
    │   ↓
    │   调用 processFailedRequestsQueue(null)
    │   ↓
    │   批量重试队列中的所有请求
    │   ↓
    │   标记 isRefreshing = false
    │
    └─ 刷新失败
        ↓
        清除所有 token (access_token + refresh_token)
        ↓
        调用 processFailedRequestsQueue(error)
        ↓
        拒绝队列中的所有请求
        ↓
        跳转到登录页 (/login)
        ↓
        显示错误提示
        ↓
        标记 isRefreshing = false
```

#### 6. 安全优势

| 特性 | 说明 |
|-----|------|
| ✅ **无感刷新** | 用户无需手动重新登录，Token 自动更新 |
| ✅ **并发安全** | 避免多个请求同时刷新，只刷新一次 |
| ✅ **队列机制** | 刷新期间的请求自动排队，刷新后批量重试 |
| ✅ **优雅降级** | 刷新失败时才清除 Token 并跳转登录 |
| ✅ **统一管理** | 所有 API 请求自动享受此机制 |
| ✅ **请求重试** | 401 错误的请求在刷新后自动重试 |

## Token 存储

### 前端存储方案对比

| 存储方式 | 优点 | 缺点 | 推荐场景 |
|---------|------|------|---------|
| **localStorage** | 持久化、API简单 | 易受XSS攻击 | 低敏感度应用 ✅ |
| **sessionStorage** | 会话级、相对安全 | 关闭页面失效 | 短期会话 |
| **Cookie (HttpOnly)** | 防XSS攻击 | 需后端配合、有CSRF风险 | 高安全要求 |
| **Memory (变量)** | 最安全 | 刷新页面失效 | 单页应用 |

### 🔒 当前实现：安全的 localStorage 存储

CodeHubot 采用**最小化存储原则**，只在 localStorage 存储必要的 Token：

```javascript
// ✅ 只存储 Token（必需）
localStorage.setItem('access_token', accessToken)
localStorage.setItem('refresh_token', refreshToken)

// ❌ 禁止存储用户信息（不安全）
// localStorage.setItem('userInfo', JSON.stringify(user))  // 危险！
```

### 📋 localStorage 存储规范

#### ✅ **允许存储的内容**

1. **access_token** - 访问令牌（必需）
2. **refresh_token** - 刷新令牌（必需）

```javascript
// frontend/src/shared/utils/auth.js
export function setToken(token) {
  localStorage.setItem('access_token', token)
}

export function setRefreshToken(token) {
  localStorage.setItem('refresh_token', token)
}
```

#### ❌ **禁止存储的内容**

1. **用户信息** - 包含敏感数据（邮箱、手机号等）
2. **API密钥** - 第三方服务密钥
3. **密码** - 任何形式的密码

```javascript
// ❌ 错误示例：不要存储用户信息
localStorage.setItem('userInfo', JSON.stringify({
  id: 123,
  username: "张三",
  email: "zhangsan@example.com",  // 敏感信息
  phone: "13800138000",            // 敏感信息
  role: "admin"                    // 可被篡改
}))
```

### 🔐 用户信息的正确存储方式

用户信息应该：
1. **存储在内存中**（Pinia Store）
2. **页面刷新后从后端重新获取**

```javascript
// frontend/src/stores/auth.js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getToken, setToken, setRefreshToken } from '@shared/utils/auth'
import { getUserInfo as fetchUserInfo } from '@shared/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // ✅ 用户信息只存储在内存中
  const userInfo = ref(null)
  
  /**
   * 设置登录信息
   */
  function setAuth(authData) {
    // 只保存 token 到 localStorage
    setToken(authData.access_token)
    setRefreshToken(authData.refresh_token)
    
    // 用户信息只保存在内存（关闭浏览器后自动清除）
    userInfo.value = authData.user
  }
  
  /**
   * 初始化（页面刷新后从后端重新获取用户信息）
   */
  async function init() {
    const token = getToken()
    if (token) {
      try {
        // 从后端获取最新用户信息
        const response = await fetchUserInfo()
        userInfo.value = response.user
      } catch (error) {
        // 获取失败则清除 token
        logout()
      }
    }
  }
  
  return { userInfo, setAuth, init }
})
```

### 🛡️ 安全优势

| 存储方式 | access_token | refresh_token | userInfo |
|---------|--------------|---------------|----------|
| **localStorage** | ✅ | ✅ | ❌ **已移除** |
| **Pinia Store (内存)** | ✅ | - | ✅ |
| **后端 API** | - | - | ✅ 页面刷新时获取 |

**优势：**
1. 🔒 **最小化敏感信息** - localStorage 只存储 Token
2. 🔒 **防止信息泄露** - 用户信息无法通过浏览器工具直接读取
3. 🔒 **防止信息篡改** - 无法通过控制台修改用户角色
4. 🔒 **数据实时性** - 页面刷新后从后端获取最新信息
5. 🔒 **自动清理** - 关闭浏览器后用户信息自动清除

### 安全建议

1. **生产环境必须使用 HTTPS**
2. 避免在 URL 中传递 Token
3. 定期刷新 Token（自动刷新机制）
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
