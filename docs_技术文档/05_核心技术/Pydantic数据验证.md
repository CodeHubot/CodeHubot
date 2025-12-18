# Pydantic 数据验证详解

## 概述

Pydantic 是一个使用 Python 类型注解进行数据验证的库。在 FastAPI 中，Pydantic 负责请求数据的验证、序列化和文档生成。本文档适合教学使用。

## 为什么需要数据验证？

### 没有验证的问题

```python
# ❌ 没有验证
@app.post("/users")
def create_user(data: dict):
    # 可能收到任何数据
    username = data.get('username')  # 可能不存在
    age = data.get('age')            # 可能不是数字
    email = data.get('email')        # 可能格式错误
    
    # 需要手动验证
    if not username:
        raise HTTPException(400, "用户名不能为空")
    if not isinstance(age, int) or age < 0:
        raise HTTPException(400, "年龄必须是正整数")
    # ... 更多验证代码
```

### 使用 Pydantic 验证

```python
from pydantic import BaseModel, EmailStr, Field

# ✅ 使用 Pydantic
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    age: int = Field(..., ge=0, le=150)
    email: EmailStr

@app.post("/users")
def create_user(user: UserCreate):
    # 数据已经验证完成，直接使用
    print(user.username)  # 保证存在且符合要求
    print(user.age)       # 保证是 0-150 的整数
    print(user.email)     # 保证是有效邮箱格式
```

## 基础模型

### 1. 定义模型

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    """用户模型"""
    id: int                    # 必需字段
    username: str             # 必需字段
    email: Optional[str] = None  # 可选字段
    age: int = 18             # 带默认值
    created_at: datetime = datetime.utcnow()  # 默认当前时间
```

### 2. 创建实例

```python
# 方式1：关键字参数
user = User(
    id=1,
    username='alice',
    email='alice@example.com',
    age=25
)

# 方式2：字典解包
data = {
    'id': 1,
    'username': 'alice',
    'email': 'alice@example.com',
    'age': 25
}
user = User(**data)

# 方式3：从 JSON
json_data = '{"id": 1, "username": "alice", "email": "alice@example.com"}'
user = User.parse_raw(json_data)
```

### 3. 访问数据

```python
user = User(id=1, username='alice')

# 访问属性
print(user.id)         # 1
print(user.username)   # 'alice'

# 转换为字典
data = user.dict()
print(data)  # {'id': 1, 'username': 'alice', 'email': None, ...}

# 转换为 JSON
json_str = user.json()
print(json_str)  # '{"id":1,"username":"alice",...}'

# 排除某些字段
data = user.dict(exclude={'created_at'})

# 只包含某些字段
data = user.dict(include={'id', 'username'})

# 排除未设置的字段
data = user.dict(exclude_unset=True)
```

## 字段验证

### 1. 基本类型

```python
from pydantic import BaseModel

class Item(BaseModel):
    # 基本类型
    name: str           # 字符串
    price: float        # 浮点数
    quantity: int       # 整数
    is_available: bool  # 布尔值
```

### 2. 复杂类型

```python
from typing import List, Dict, Set, Tuple, Optional, Union
from datetime import datetime, date

class ComplexModel(BaseModel):
    # 列表
    tags: List[str]                    # 字符串列表
    numbers: List[int]                 # 整数列表
    
    # 字典
    metadata: Dict[str, str]           # 键值都是字符串
    scores: Dict[str, int]             # 字符串键，整数值
    
    # 集合
    categories: Set[str]               # 字符串集合（去重）
    
    # 元组
    coordinates: Tuple[float, float]   # 固定长度元组
    
    # 可选类型
    nickname: Optional[str] = None     # 可以是 str 或 None
    
    # 联合类型
    identifier: Union[int, str]        # 可以是 int 或 str
    
    # 日期时间
    created_at: datetime
    birth_date: date

# 使用
model = ComplexModel(
    tags=['python', 'fastapi'],
    numbers=[1, 2, 3],
    metadata={'key': 'value'},
    scores={'math': 90, 'english': 85},
    categories={'tech', 'education'},
    coordinates=(39.9, 116.4),
    identifier=123,  # 可以是整数
    # identifier='abc',  # 也可以是字符串
    created_at=datetime.now(),
    birth_date=date(2000, 1, 1)
)
```

### 3. Field 高级验证

```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    # 字符串长度
    username: str = Field(
        ...,                        # 必需（等同于 required=True）
        min_length=3,               # 最小长度
        max_length=50,              # 最大长度
        description="用户名",        # 描述（在 API 文档显示）
        example="john_doe"          # 示例值
    )
    
    # 数值范围
    age: int = Field(
        ...,
        ge=0,                       # 大于等于 (>=)
        le=150,                     # 小于等于 (<=)
        description="年龄（0-150）"
    )
    
    # 正则表达式
    phone: str = Field(
        ...,
        regex=r'^1[3-9]\d{9}$',     # 中国手机号
        example="13800138000"
    )
    
    # 邮箱验证
    email: EmailStr = Field(        # EmailStr 自动验证邮箱格式
        ...,
        description="邮箱地址",
        example="user@example.com"
    )
    
    # 可选字段
    nickname: Optional[str] = Field(
        None,                       # 默认值
        max_length=50
    )
    
    # 列表元素数量
    tags: List[str] = Field(
        default_factory=list,       # 默认空列表
        min_items=0,                # 最少元素数
        max_items=10                # 最多元素数
    )
    
    # 小数精度
    from decimal import Decimal
    balance: Decimal = Field(
        default=Decimal('0.00'),
        max_digits=10,              # 最大位数
        decimal_places=2            # 小数位数
    )
```

### 4. 自定义验证器

```python
from pydantic import BaseModel, validator, root_validator

class User(BaseModel):
    username: str
    password: str
    password_confirm: str
    age: int
    
    @validator('username')
    def username_alphanumeric(cls, v):
        """用户名必须是字母数字"""
        if not v.isalnum():
            raise ValueError('用户名只能包含字母和数字')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        """密码强度验证"""
        if len(v) < 8:
            raise ValueError('密码至少8个字符')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含大写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含数字')
        return v
    
    @validator('age')
    def age_positive(cls, v):
        """年龄必须为正数"""
        if v < 0:
            raise ValueError('年龄必须大于0')
        return v
    
    @root_validator
    def check_passwords_match(cls, values):
        """检查两次密码是否一致"""
        password = values.get('password')
        password_confirm = values.get('password_confirm')
        
        if password != password_confirm:
            raise ValueError('两次密码不一致')
        
        return values

# 使用
try:
    user = User(
        username='alice123',
        password='Pass1234',
        password_confirm='Pass1234',
        age=25
    )
except ValueError as e:
    print(e)  # 验证错误信息
```

## 嵌套模型

### 1. 基本嵌套

```python
class Address(BaseModel):
    """地址模型"""
    street: str
    city: str
    country: str = "China"

class User(BaseModel):
    """用户模型"""
    name: str
    email: EmailStr
    address: Address  # 嵌套模型

# 使用
user = User(
    name='Alice',
    email='alice@example.com',
    address={
        'street': '中关村大街1号',
        'city': '北京'
    }
)

print(user.address.city)  # 北京
```

### 2. 嵌套列表

```python
class Course(BaseModel):
    """课程模型"""
    title: str
    credits: int

class Student(BaseModel):
    """学生模型"""
    name: str
    courses: List[Course]  # 课程列表

# 使用
student = Student(
    name='Bob',
    courses=[
        {'title': 'Python', 'credits': 3},
        {'title': 'Database', 'credits': 4}
    ]
)

for course in student.courses:
    print(f"{course.title}: {course.credits}学分")
```

## 配置选项

### 1. Config 类

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    email: str
    password_hash: str
    
    class Config:
        # ORM 模式（支持从 ORM 对象创建）
        orm_mode = True
        
        # 字段别名
        fields = {
            'password_hash': {'exclude': True}  # 排除敏感字段
        }
        
        # JSON 示例（在 API 文档中显示）
        schema_extra = {
            "example": {
                "id": 1,
                "username": "alice",
                "email": "alice@example.com"
            }
        }
        
        # 允许任意类型
        arbitrary_types_allowed = True
        
        # 使用枚举值
        use_enum_values = True
```

### 2. ORM 模式

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserModel(Base):
    """SQLAlchemy ORM 模型"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)

class UserSchema(BaseModel):
    """Pydantic 模型"""
    id: int
    username: str
    email: str
    
    class Config:
        orm_mode = True  # 启用 ORM 模式

# 从 ORM 对象创建 Pydantic 对象
db_user = session.query(UserModel).first()
pydantic_user = UserSchema.from_orm(db_user)

print(pydantic_user.username)
```

## FastAPI 集成

### 1. 请求模型

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field

app = FastAPI()

class UserCreate(BaseModel):
    """创建用户请求模型"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    age: int = Field(..., ge=0, le=150)

@app.post("/users")
async def create_user(user: UserCreate):
    """
    创建用户
    
    FastAPI 会自动：
    1. 验证请求数据
    2. 转换为 UserCreate 对象
    3. 生成 API 文档
    """
    # 数据已验证，可以直接使用
    return {
        "message": "用户创建成功",
        "user": user.dict()
    }
```

### 2. 响应模型

```python
from datetime import datetime

class UserResponse(BaseModel):
    """用户响应模型（不包含密码）"""
    id: int
    username: str
    email: str
    created_at: datetime
    
    class Config:
        orm_mode = True

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """
    获取用户
    
    response_model 会：
    1. 自动过滤掉不在模型中的字段（如 password）
    2. 验证响应数据
    3. 生成响应文档
    """
    # 假设从数据库查询
    user = db.query(User).filter(User.id == user_id).first()
    
    # 返回整个对象，password 会被自动过滤
    return user
```

### 3. 统一响应格式

```python
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    """统一响应格式"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[T] = None
    error_code: Optional[str] = None

# 使用
@app.get("/users/{user_id}", response_model=StandardResponse[UserResponse])
async def get_user(user_id: int):
    user = get_user_from_db(user_id)
    
    return StandardResponse(
        success=True,
        message="获取成功",
        data=user
    )
```

## 实用技巧

### 1. 动态模型

```python
from pydantic import create_model

# 动态创建模型
DynamicModel = create_model(
    'DynamicModel',
    name=(str, ...),
    age=(int, Field(ge=0))
)

instance = DynamicModel(name='Alice', age=25)
```

### 2. 模型继承

```python
class BaseUser(BaseModel):
    """基础用户模型"""
    username: str
    email: EmailStr

class UserCreate(BaseUser):
    """创建用户（继承 + 添加字段）"""
    password: str

class UserUpdate(BaseUser):
    """更新用户（所有字段可选）"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
```

### 3. 部分更新

```python
class UserUpdate(BaseModel):
    """用户更新模型（所有字段可选）"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    age: Optional[int] = None

@app.patch("/users/{user_id}")
async def update_user(user_id: int, user_update: UserUpdate):
    """部分更新用户"""
    # 只更新提供的字段
    update_data = user_update.dict(exclude_unset=True)
    
    # 更新数据库
    db.query(User).filter(User.id == user_id).update(update_data)
    db.commit()
    
    return {"message": "更新成功"}
```

## CodeHubot 项目实践

### 用户相关模型

```python
# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    """创建用户"""
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    """用户登录"""
    email: str  # 可以是用户名或邮箱
    password: str

class UserResponse(UserBase):
    """用户响应（不包含密码）"""
    id: int
    uuid: str
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        orm_mode = True

class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
```

### 设备相关模型

```python
# backend/app/schemas/device.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DeviceBase(BaseModel):
    """设备基础模型"""
    name: str = Field(..., min_length=1, max_length=100)
    device_type: str = Field(..., regex='^(ESP32|Arduino|RaspberryPi)$')
    description: Optional[str] = Field(None, max_length=500)

class DeviceCreate(DeviceBase):
    """创建设备"""
    product_id: int = Field(..., gt=0)

class DeviceUpdate(BaseModel):
    """更新设备（所有字段可选）"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = None

class DeviceResponse(DeviceBase):
    """设备响应"""
    id: int
    uuid: str
    device_id: str
    status: str
    online: bool
    created_at: datetime
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "uuid": "550e8400-e29b-41d4-a716-446655440000",
                "name": "我的ESP32设备",
                "device_type": "ESP32",
                "status": "online"
            }
        }
```

## 最佳实践

### 1. 模型命名

```python
# ✅ 清晰的命名
class UserCreate  # 创建
class UserUpdate  # 更新
class UserResponse  # 响应
class UserInDB  # 数据库模型

# ❌ 不清晰的命名
class User1
class User2
class UserModel
```

### 2. 字段验证

```python
# ✅ 使用 Field 提供详细信息
class User(BaseModel):
    age: int = Field(..., ge=0, le=150, description="年龄", example=25)

# ❌ 缺少验证
class User(BaseModel):
    age: int
```

### 3. 文档示例

```python
# ✅ 提供示例
class User(BaseModel):
    name: str = Field(..., example="Alice")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Alice",
                "age": 25
            }
        }

# ❌ 没有示例
class User(BaseModel):
    name: str
```

## 教学要点总结

### 核心概念
1. **数据验证**：自动验证输入数据
2. **类型转换**：自动类型转换和解析
3. **文档生成**：自动生成 API 文档
4. **序列化**：对象 ↔ 字典 ↔ JSON

### 常用验证
- **类型验证**：int, str, bool, List, Dict
- **范围验证**：ge, le, min_length, max_length
- **格式验证**：regex, EmailStr
- **自定义验证**：@validator

### FastAPI 集成
- 请求体验证
- 响应数据过滤
- 自动文档生成
- 统一响应格式

## 相关文档

- [FastAPI框架](./FastAPI框架.md) - Web 框架
- [API开发规范](../../docs_开发规范/01_API开发规范.md) - API 规范
- [数据库规范](../../docs_开发规范/03_数据库规范.md) - 数据规范
