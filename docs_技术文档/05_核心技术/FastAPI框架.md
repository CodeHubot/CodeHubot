# FastAPI Web 框架深度解析

## 概述

FastAPI 是一个现代、快速（高性能）的 Web 框架，用于构建 API。本文档深入讲解 FastAPI 的核心概念和在 CodeHubot 项目中的实际应用，适合教学使用。

## 为什么选择 FastAPI？

### 核心优势

```
┌─────────────────────────────────────────────────────────┐
│                   FastAPI 核心优势                       │
├─────────────────────────────────────────────────────────┤
│  1. 高性能 ⚡                                           │
│     - 基于 Starlette 和 Pydantic                       │
│     - 性能媲美 NodeJS 和 Go                             │
│     - 支持异步 async/await                              │
│                                                         │
│  2. 开发效率高 🚀                                       │
│     - 自动生成交互式 API 文档                           │
│     - 类型提示，减少 bug                                │
│     - 代码简洁，易于维护                                │
│                                                         │
│  3. 易于学习 📚                                         │
│     - 基于 Python 标准类型提示                          │
│     - 文档完善，示例丰富                                │
│     - 符合直觉的 API 设计                               │
│                                                         │
│  4. 生产就绪 ✅                                         │
│     - 内置数据验证                                      │
│     - 安全性和认证支持                                  │
│     - 依赖注入系统                                      │
└─────────────────────────────────────────────────────────┘
```

### 与其他框架对比

| 特性 | FastAPI | Flask | Django |
|------|---------|-------|--------|
| **性能** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **异步支持** | ✅ 原生支持 | ⚠️ 需额外配置 | ⚠️ 3.1+ 支持 |
| **自动文档** | ✅ Swagger/ReDoc | ❌ 需手动 | ⚠️ 需插件 |
| **类型检查** | ✅ 强类型 | ❌ 弱类型 | ⚠️ 部分支持 |
| **学习曲线** | 🟢 平缓 | 🟢 平缓 | 🔴 陡峭 |
| **适用场景** | API 服务 | 小型 Web | 全栈应用 |

## FastAPI 基础概念

### 1. 路由和端点

#### 基本路由

```python
from fastapi import FastAPI

app = FastAPI()

# GET 请求
@app.get("/")
async def root():
    """根路径"""
    return {"message": "Hello World"}

# POST 请求
@app.post("/items")
async def create_item(item: dict):
    """创建项目"""
    return {"item": item}

# PUT 请求
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: dict):
    """更新项目"""
    return {"item_id": item_id, "item": item}

# DELETE 请求
@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """删除项目"""
    return {"message": f"Item {item_id} deleted"}
```

#### 路径参数

```python
# 基本路径参数
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """获取用户 - user_id 会自动转换为 int 类型"""
    return {"user_id": user_id}

# 枚举路径参数
from enum import Enum

class ModelType(str, Enum):
    gpt = "gpt"
    claude = "claude"
    deepseek = "deepseek"

@app.get("/models/{model_type}")
async def get_model(model_type: ModelType):
    """获取模型信息 - 只接受枚举值"""
    return {"model": model_type.value}

# 路径参数 + 类型验证
from pydantic import Field

@app.get("/devices/{device_id}")
async def get_device(
    device_id: int = Field(..., ge=1, description="设备ID，必须大于0")
):
    """获取设备 - 带验证"""
    return {"device_id": device_id}
```

#### 查询参数

```python
from typing import Optional

# 可选查询参数
@app.get("/items")
async def list_items(
    skip: int = 0,           # 默认值为 0
    limit: int = 10,         # 默认值为 10
    keyword: Optional[str] = None  # 可选参数
):
    """列出项目 - 带分页和搜索"""
    return {
        "skip": skip,
        "limit": limit,
        "keyword": keyword
    }

# 必需查询参数
@app.get("/search")
async def search(q: str):
    """搜索 - q 参数必需"""
    return {"query": q}

# 查询参数验证
from pydantic import Field

@app.get("/users")
async def list_users(
    page: int = Field(1, ge=1, description="页码，从1开始"),
    size: int = Field(20, ge=1, le=100, description="每页数量，1-100"),
    status: Optional[str] = Field(None, regex="^(active|inactive)$")
):
    """列出用户 - 带验证"""
    return {"page": page, "size": size, "status": status}
```

### 2. 请求体 (Request Body)

#### 使用 Pydantic 模型

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# 定义数据模型
class UserCreate(BaseModel):
    """用户创建模型"""
    email: EmailStr = Field(..., description="用户邮箱")
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    age: Optional[int] = Field(None, ge=0, le=150)
    
    class Config:
        # JSON 示例（在 API 文档中显示）
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "john_doe",
                "password": "password123",
                "age": 25
            }
        }

# 使用模型
@app.post("/users")
async def create_user(user: UserCreate):
    """
    创建用户
    
    - **email**: 用户邮箱（必填，格式验证）
    - **username**: 用户名（必填，3-50字符）
    - **password**: 密码（必填，至少6字符）
    - **age**: 年龄（可选，0-150）
    """
    # FastAPI 会自动验证数据
    # 如果验证失败，返回 422 错误
    return {
        "message": "用户创建成功",
        "user": user.dict()
    }
```

#### 嵌套模型

```python
from typing import List

class Address(BaseModel):
    """地址模型"""
    street: str
    city: str
    country: str = "China"

class User(BaseModel):
    """用户模型"""
    name: str
    email: EmailStr
    addresses: List[Address]  # 地址列表
    tags: List[str] = []      # 标签列表

@app.post("/users/nested")
async def create_user_with_addresses(user: User):
    """创建用户（带嵌套数据）"""
    return user
```

### 3. 响应模型

#### 定义响应格式

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

# 响应模型
class UserResponse(BaseModel):
    """用户响应模型（不包含密码）"""
    id: int
    email: str
    username: str
    created_at: datetime
    
    class Config:
        orm_mode = True  # 支持从 ORM 对象转换

# 使用响应模型
@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    """创建用户 - 返回的数据自动过滤掉 password"""
    # ... 创建用户逻辑
    return user_obj  # FastAPI 自动转换为 UserResponse

# 统一响应格式
T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    """统一响应格式"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[T] = None

@app.get("/devices/{device_id}", response_model=StandardResponse[UserResponse])
async def get_device(device_id: int):
    """获取设备 - 统一格式"""
    return {
        "success": True,
        "message": "获取成功",
        "data": device_obj
    }
```

### 4. 依赖注入 (Dependency Injection)

#### 基本依赖

```python
from fastapi import Depends

# 定义依赖
def get_current_user_id(user_id: int = Header(...)):
    """从请求头获取用户ID"""
    return user_id

# 使用依赖
@app.get("/profile")
async def get_profile(user_id: int = Depends(get_current_user_id)):
    """获取用户资料"""
    return {"user_id": user_id}
```

#### 数据库会话依赖

```python
from sqlalchemy.orm import Session
from app.core.database import SessionLocal

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 使用数据库依赖
@app.get("/users")
async def list_users(db: Session = Depends(get_db)):
    """列出用户"""
    users = db.query(User).all()
    return users
```

#### 认证依赖

```python
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取当前登录用户"""
    # 验证 token
    user = verify_token_and_get_user(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败"
        )
    return user

# 使用认证依赖
@app.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息（需要登录）"""
    return current_user
```

#### 依赖链

```python
# 依赖可以层层嵌套
def verify_permissions(
    current_user: User = Depends(get_current_user)
):
    """验证权限"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="权限不足")
    return current_user

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(verify_permissions)  # 依赖链
):
    """删除用户（仅管理员）"""
    return {"message": "用户已删除"}
```

### 5. 中间件

#### 自定义中间件

```python
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 自定义计时中间件
class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

app.add_middleware(TimingMiddleware)

# 日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"请求: {request.method} {request.url}")
    
    response = await call_next(request)
    
    logger.info(f"响应: {response.status_code}")
    return response
```

### 6. 异常处理

#### 自定义异常处理器

```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# 处理 HTTP 异常
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """统一处理 HTTP 异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error_code": exc.status_code
        }
    )

# 处理验证错误
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """统一处理数据验证错误"""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "数据验证失败",
            "errors": exc.errors()
        }
    )

# 自定义异常
class BusinessException(Exception):
    """业务异常"""
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code

@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    """处理业务异常"""
    return JSONResponse(
        status_code=exc.code,
        content={
            "success": False,
            "message": exc.message
        }
    )

# 使用自定义异常
@app.get("/items/{item_id}")
async def get_item(item_id: int):
    if item_id not in items:
        raise BusinessException(f"商品 {item_id} 不存在", code=404)
    return items[item_id]
```

## 进阶特性

### 1. 后台任务

```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    """发送邮件（耗时操作）"""
    time.sleep(3)  # 模拟耗时
    logger.info(f"邮件已发送到 {email}")

@app.post("/send-notification")
async def send_notification(
    email: str,
    background_tasks: BackgroundTasks
):
    """发送通知（异步）"""
    # 添加后台任务
    background_tasks.add_task(send_email, email, "Hello!")
    
    # 立即返回（不等待邮件发送完成）
    return {"message": "通知将在后台发送"}
```

### 2. 文件上传

```python
from fastapi import File, UploadFile
from typing import List

# 单文件上传
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件"""
    contents = await file.read()
    
    # 保存文件
    with open(f"uploads/{file.filename}", "wb") as f:
        f.write(contents)
    
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents)
    }

# 多文件上传
@app.post("/upload/multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """上传多个文件"""
    return [
        {
            "filename": file.filename,
            "content_type": file.content_type
        }
        for file in files
    ]
```

### 3. WebSocket

```python
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点"""
    await websocket.accept()
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            # 发送消息
            await websocket.send_text(f"收到: {data}")
    except:
        await websocket.close()
```

### 4. 启动和关闭事件

```python
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("🚀 应用启动")
    # 初始化数据库连接池
    # 初始化 Redis
    # 加载配置

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("🛑 应用关闭")
    # 关闭数据库连接
    # 清理资源
```

### 5. 路由器 (APIRouter)

```python
from fastapi import APIRouter

# 创建路由器
router = APIRouter(
    prefix="/users",
    tags=["用户管理"],
    responses={404: {"description": "未找到"}}
)

# 在路由器上定义路由
@router.get("/")
async def list_users():
    """列出用户"""
    return []

@router.post("/")
async def create_user(user: UserCreate):
    """创建用户"""
    return user

# 在主应用中包含路由器
app.include_router(router)

# 还可以包含多个路由器
app.include_router(devices_router, prefix="/api")
app.include_router(courses_router, prefix="/api")
```

## CodeHubot 项目实践

### 项目结构

```
backend/
├── main.py                      # 应用入口
├── app/
│   ├── api/                     # API 路由
│   │   ├── __init__.py          # 路由注册
│   │   ├── auth.py              # 认证相关
│   │   └── devices.py           # 设备管理
│   ├── core/                    # 核心模块
│   │   ├── config.py            # 配置
│   │   ├── security.py          # 安全
│   │   ├── deps.py              # 依赖注入
│   │   └── database.py          # 数据库
│   ├── models/                  # ORM 模型
│   ├── schemas/                 # Pydantic 模型
│   └── services/                # 业务逻辑
```

### main.py 完整示例

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("🚀 启动 CodeHubot 平台")
    # 初始化管理员账号
    from app.core.init_admin import init_admin_on_startup
    init_admin_on_startup()
    
    yield
    
    # 关闭时
    logger.info("🛑 关闭 CodeHubot 平台")

app = FastAPI(
    title="CodeHubot API",
    description="AI-IoT 智能教学平台",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
from app.api import api_router
app.include_router(api_router, prefix="/api")

# 根路径
@app.get("/")
async def root():
    """欢迎页面"""
    return {
        "message": "Welcome to CodeHubot API",
        "docs": "/docs",
        "version": "1.0.0"
    }

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}
```

## 最佳实践

### 1. 项目组织

```python
# ✅ 好的做法：按功能模块组织
app/
├── api/
│   ├── v1/
│   │   ├── users.py
│   │   ├── devices.py
│   │   └── courses.py
│   └── v2/
│       └── users.py

# ❌ 不好的做法：全部放在一个文件
# main.py (2000+ 行代码)
```

### 2. 依赖注入

```python
# ✅ 使用依赖注入
@app.get("/users")
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pass

# ❌ 直接访问全局变量
@app.get("/users")
async def list_users():
    db = global_db_session  # 不推荐
```

### 3. 类型注解

```python
# ✅ 完整的类型注解
@app.get("/items/{item_id}")
async def get_item(
    item_id: int,
    q: Optional[str] = None
) -> Dict[str, Any]:
    pass

# ❌ 缺少类型注解
@app.get("/items/{item_id}")
async def get_item(item_id, q=None):
    pass
```

## 常见问题

### 1. 同步 vs 异步

```python
# 异步函数（推荐用于 I/O 操作）
@app.get("/async")
async def async_endpoint():
    result = await some_async_function()
    return result

# 同步函数（用于 CPU 密集型操作）
@app.get("/sync")
def sync_endpoint():
    result = some_sync_function()
    return result
```

### 2. 数据验证

```python
from pydantic import validator

class UserCreate(BaseModel):
    username: str
    age: int
    
    @validator('username')
    def username_must_be_alphanumeric(cls, v):
        """自定义验证器"""
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v
    
    @validator('age')
    def age_must_be_positive(cls, v):
        """年龄必须为正数"""
        if v < 0:
            raise ValueError('年龄必须大于0')
        return v
```

## 教学要点总结

### 核心概念
1. **路由和端点**：定义 API 接口
2. **请求体**：使用 Pydantic 进行数据验证
3. **响应模型**：控制返回数据格式
4. **依赖注入**：管理共享资源和认证
5. **中间件**：处理横切关注点

### 实践技巧
- ✅ 使用类型注解
- ✅ 合理组织项目结构
- ✅ 利用自动文档
- ✅ 编写单元测试
- ✅ 异步处理 I/O 操作

## 相关文档

- [SQLAlchemy ORM](./SQLAlchemy-ORM.md) - 数据库操作
- [Pydantic数据验证](./Pydantic数据验证.md) - 数据模型
- [API开发规范](../../docs_开发规范/01_API开发规范.md) - API 规范
- [后端架构](../02_系统架构/后端架构.md) - 项目架构
