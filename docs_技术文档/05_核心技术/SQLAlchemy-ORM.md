# SQLAlchemy ORM 数据库操作

## 概述

SQLAlchemy 是 Python 最流行的 ORM (Object-Relational Mapping) 框架，它将数据库表映射为 Python 类，让我们可以使用面向对象的方式操作数据库。本文档适合教学使用。

## ORM 是什么？

### 传统 SQL vs ORM

```python
# ❌ 传统 SQL 方式
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
row = cursor.fetchone()
user = {
    'id': row[0],
    'name': row[1],
    'email': row[2]
}

# ✅ ORM 方式
user = db.query(User).filter(User.id == user_id).first()
# 直接访问属性
print(user.name, user.email)
```

### ORM 的优势

```
┌─────────────────────────────────────────────────────────┐
│                    ORM 优势                              │
├─────────────────────────────────────────────────────────┤
│  1. 代码更简洁 📝                                       │
│     - 不需要手写 SQL                                    │
│     - 自动处理数据类型转换                              │
│                                                         │
│  2. 数据库无关 🔄                                       │
│     - 代码可以在 MySQL/PostgreSQL/SQLite 间切换        │
│     - 只需修改连接字符串                                │
│                                                         │
│  3. 类型安全 ✅                                         │
│     - IDE 自动补全                                      │
│     - 编译时发现错误                                    │
│                                                         │
│  4. 防止 SQL 注入 🛡️                                   │
│     - 自动参数化查询                                    │
│     - 内置安全机制                                      │
└─────────────────────────────────────────────────────────┘
```

## 基础概念

### 1. 定义模型（Model）

```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    """用户模型"""
    __tablename__ = 'core_users'  # 表名
    
    # 字段定义
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        """对象的字符串表示"""
        return f"<User(id={self.id}, username='{self.username}')>"
```

### 2. 字段类型

```python
from sqlalchemy import (
    Integer,    # 整数
    String,     # 字符串
    Text,       # 长文本
    Boolean,    # 布尔值
    DateTime,   # 日期时间
    Date,       # 日期
    Time,       # 时间
    Float,      # 浮点数
    Decimal,    # 高精度小数
    JSON,       # JSON 数据
    Enum        # 枚举
)

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)          # 字符串（限长）
    description = Column(Text)                          # 长文本
    price = Column(Decimal(10, 2))                      # 价格（10位数，2位小数）
    stock = Column(Integer, default=0)                  # 库存
    is_available = Column(Boolean, default=True)        # 是否可用
    metadata = Column(JSON)                             # JSON 数据
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 3. 字段约束

```python
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, 
                primary_key=True,      # 主键
                autoincrement=True)    # 自动递增
    
    username = Column(String(50),
                     unique=True,       # 唯一约束
                     nullable=False,    # 非空
                     index=True)        # 创建索引
    
    email = Column(String(100),
                  unique=True,
                  nullable=False)
    
    age = Column(Integer,
                default=18,             # 默认值
                server_default='18')    # 数据库层面默认值
    
    status = Column(String(20),
                   comment='用户状态')   # 字段注释
```

### 4. 关系定义

#### 一对多关系

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Teacher(Base):
    """教师（一）"""
    __tablename__ = 'teachers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    
    # 定义关系（一对多）
    courses = relationship('Course', back_populates='teacher')

class Course(Base):
    """课程（多）"""
    __tablename__ = 'courses'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    teacher_id = Column(Integer, ForeignKey('teachers.id'))  # 外键
    
    # 反向关系
    teacher = relationship('Teacher', back_populates='courses')

# 使用
teacher = db.query(Teacher).first()
print(teacher.courses)  # 访问教师的所有课程

course = db.query(Course).first()
print(course.teacher)   # 访问课程的教师
```

#### 多对多关系

```python
from sqlalchemy import Table

# 关联表（中间表）
student_course = Table(
    'student_course',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id')),
    Column('course_id', Integer, ForeignKey('courses.id'))
)

class Student(Base):
    """学生"""
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    
    # 多对多关系
    courses = relationship('Course',
                          secondary=student_course,
                          back_populates='students')

class Course(Base):
    """课程"""
    __tablename__ = 'courses'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    
    # 反向关系
    students = relationship('Student',
                           secondary=student_course,
                           back_populates='courses')

# 使用
student = db.query(Student).first()
print(student.courses)  # 学生的所有课程

course = db.query(Course).first()
print(course.students)  # 课程的所有学生
```

## 数据库连接

### 1. 创建引擎

```python
from sqlalchemy import create_engine

# MySQL 连接
engine = create_engine(
    'mysql+pymysql://user:password@localhost:3306/database',
    echo=True,              # 打印 SQL 语句（开发时用）
    pool_size=10,           # 连接池大小
    max_overflow=20,        # 最大溢出连接数
    pool_pre_ping=True,     # 连接前检查是否有效
    pool_recycle=3600       # 连接回收时间（秒）
)

# SQLite 连接（用于测试）
engine = create_engine('sqlite:///test.db')

# PostgreSQL 连接
engine = create_engine('postgresql://user:password@localhost/database')
```

### 2. 创建会话

```python
from sqlalchemy.orm import sessionmaker, Session

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 获取会话
def get_db():
    """依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 使用会话
db = SessionLocal()
try:
    # 执行数据库操作
    users = db.query(User).all()
finally:
    db.close()
```

## CRUD 操作

### 1. Create - 创建

```python
# 创建单个对象
user = User(
    username='alice',
    email='alice@example.com',
    password_hash='hashed_password'
)

db.add(user)
db.commit()
db.refresh(user)  # 刷新对象，获取自动生成的 ID

print(f"创建用户，ID: {user.id}")

# 批量创建
users = [
    User(username='bob', email='bob@example.com', password_hash='xxx'),
    User(username='charlie', email='charlie@example.com', password_hash='xxx')
]

db.add_all(users)
db.commit()

# 使用 bulk_insert_mappings（更快）
db.bulk_insert_mappings(User, [
    {'username': 'user1', 'email': 'user1@example.com'},
    {'username': 'user2', 'email': 'user2@example.com'}
])
db.commit()
```

### 2. Read - 查询

#### 基本查询

```python
# 查询所有
users = db.query(User).all()

# 查询第一个
user = db.query(User).first()

# 根据主键查询
user = db.query(User).get(1)  # ID = 1

# 查询指定字段
results = db.query(User.id, User.username).all()

# 计数
count = db.query(User).count()
```

#### 条件查询

```python
from sqlalchemy import and_, or_, not_

# 单条件
users = db.query(User).filter(User.username == 'alice').all()

# 多条件（AND）
users = db.query(User).filter(
    User.age > 18,
    User.is_active == True
).all()

# 或者使用 and_
users = db.query(User).filter(
    and_(User.age > 18, User.is_active == True)
).all()

# OR 条件
users = db.query(User).filter(
    or_(User.role == 'admin', User.role == 'teacher')
).all()

# NOT 条件
users = db.query(User).filter(
    not_(User.is_active)
).all()

# LIKE 模糊查询
users = db.query(User).filter(User.username.like('%alice%')).all()

# IN 查询
users = db.query(User).filter(User.role.in_(['admin', 'teacher'])).all()

# BETWEEN
users = db.query(User).filter(User.age.between(18, 30)).all()

# IS NULL
users = db.query(User).filter(User.email == None).all()
# IS NOT NULL
users = db.query(User).filter(User.email != None).all()
```

#### 排序和分页

```python
# 排序
users = db.query(User).order_by(User.created_at.desc()).all()  # 降序
users = db.query(User).order_by(User.age.asc()).all()          # 升序

# 多字段排序
users = db.query(User).order_by(
    User.role.desc(),
    User.created_at.asc()
).all()

# 分页
page = 1
page_size = 20
users = db.query(User)\
    .offset((page - 1) * page_size)\
    .limit(page_size)\
    .all()

# 或者
users = db.query(User).slice(0, 20).all()  # 前 20 条
```

#### 关联查询

```python
# JOIN 查询
results = db.query(Course, Teacher)\
    .join(Teacher)\
    .filter(Teacher.name == 'Alice')\
    .all()

# LEFT JOIN
results = db.query(Course)\
    .outerjoin(Teacher)\
    .filter(Teacher.name == 'Alice')\
    .all()

# 预加载关联对象（解决 N+1 问题）
from sqlalchemy.orm import joinedload

# 急加载（JOIN）
teachers = db.query(Teacher)\
    .options(joinedload(Teacher.courses))\
    .all()

# 懒加载（需要时再查询，默认行为）
teachers = db.query(Teacher).all()
for teacher in teachers:
    print(teacher.courses)  # 每次访问都查询数据库

# 立即加载（subquery）
from sqlalchemy.orm import subqueryload

teachers = db.query(Teacher)\
    .options(subqueryload(Teacher.courses))\
    .all()
```

### 3. Update - 更新

```python
# 方式1：查询后修改
user = db.query(User).filter(User.id == 1).first()
user.email = 'newemail@example.com'
user.age = 26
db.commit()

# 方式2：直接更新（效率更高）
db.query(User)\
    .filter(User.id == 1)\
    .update({'email': 'newemail@example.com', 'age': 26})
db.commit()

# 批量更新
db.query(User)\
    .filter(User.is_active == False)\
    .update({'status': 'inactive'})
db.commit()

# 使用表达式更新
db.query(User)\
    .filter(User.id == 1)\
    .update({'age': User.age + 1})  # age 自增 1
db.commit()
```

### 4. Delete - 删除

```python
# 方式1：查询后删除
user = db.query(User).filter(User.id == 1).first()
if user:
    db.delete(user)
    db.commit()

# 方式2：直接删除（效率更高）
db.query(User)\
    .filter(User.id == 1)\
    .delete()
db.commit()

# 批量删除
db.query(User)\
    .filter(User.is_active == False)\
    .delete()
db.commit()

# 软删除（推荐）
db.query(User)\
    .filter(User.id == 1)\
    .update({'deleted_at': datetime.utcnow()})
db.commit()
```

## 事务处理

### 1. 基本事务

```python
try:
    # 开始事务（自动开始）
    user = User(username='alice', email='alice@example.com')
    db.add(user)
    
    # 其他操作...
    
    # 提交事务
    db.commit()
except Exception as e:
    # 回滚事务
    db.rollback()
    raise e
```

### 2. 手动事务控制

```python
from sqlalchemy import event

# 开始事务
db.begin()

try:
    user = User(username='alice')
    db.add(user)
    
    device = Device(name='Device 1', user_id=user.id)
    db.add(device)
    
    # 提交
    db.commit()
except:
    # 回滚
    db.rollback()
    raise
```

### 3. 嵌套事务（保存点）

```python
try:
    db.begin()
    
    user = User(username='alice')
    db.add(user)
    
    # 创建保存点
    savepoint = db.begin_nested()
    try:
        risky_operation()
        db.commit()  # 提交保存点
    except:
        db.rollback()  # 回滚到保存点
    
    db.commit()  # 提交主事务
except:
    db.rollback()
```

## 高级查询

### 1. 子查询

```python
from sqlalchemy import func

# 子查询
subq = db.query(
    Course.teacher_id,
    func.count(Course.id).label('course_count')
).group_by(Course.teacher_id).subquery()

# 使用子查询
teachers = db.query(Teacher, subq.c.course_count)\
    .outerjoin(subq, Teacher.id == subq.c.teacher_id)\
    .all()
```

### 2. 聚合函数

```python
from sqlalchemy import func

# COUNT
count = db.query(func.count(User.id)).scalar()

# SUM
total = db.query(func.sum(Product.price)).scalar()

# AVG
average = db.query(func.avg(Product.price)).scalar()

# MAX / MIN
max_price = db.query(func.max(Product.price)).scalar()
min_price = db.query(func.min(Product.price)).scalar()

# GROUP BY
results = db.query(
    User.role,
    func.count(User.id).label('count')
).group_by(User.role).all()

# HAVING
results = db.query(
    User.role,
    func.count(User.id).label('count')
)\
.group_by(User.role)\
.having(func.count(User.id) > 5)\
.all()
```

### 3. 原始 SQL

```python
# 执行原始 SQL
from sqlalchemy import text

# 查询
result = db.execute(text("SELECT * FROM users WHERE age > :age"), {'age': 18})
users = result.fetchall()

# 更新
db.execute(text("UPDATE users SET status = :status WHERE id = :id"), 
          {'status': 'active', 'id': 1})
db.commit()
```

## CodeHubot 项目实践

### 用户模型

```python
# backend/app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

class User(Base):
    """用户模型"""
    __tablename__ = 'core_users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default='individual')
    school_id = Column(Integer, ForeignKey('core_schools.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    school = relationship('School', back_populates='users')
    devices = relationship('Device', back_populates='user')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
```

### 常用查询示例

```python
# backend/app/api/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user

router = APIRouter()

@router.get("/users")
async def list_users(
    page: int = 1,
    size: int = 20,
    keyword: str = None,
    role: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """列出用户（带搜索和分页）"""
    
    # 构建查询
    query = db.query(User)
    
    # 搜索
    if keyword:
        query = query.filter(
            or_(
                User.username.like(f'%{keyword}%'),
                User.email.like(f'%{keyword}%')
            )
        )
    
    # 角色筛选
    if role:
        query = query.filter(User.role == role)
    
    # 总数
    total = query.count()
    
    # 分页
    users = query\
        .offset((page - 1) * size)\
        .limit(size)\
        .all()
    
    return {
        'total': total,
        'page': page,
        'size': size,
        'data': [user.to_dict() for user in users]
    }
```

## 最佳实践

### 1. 使用上下文管理器

```python
# ✅ 自动关闭会话
with SessionLocal() as db:
    users = db.query(User).all()
    # 自动 commit 和 close

# ❌ 手动管理
db = SessionLocal()
users = db.query(User).all()
db.close()  # 容易忘记
```

### 2. 使用依赖注入

```python
# ✅ FastAPI 依赖注入
@app.get("/users")
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

# ❌ 全局会话
global_db = SessionLocal()

@app.get("/users")
def list_users():
    return global_db.query(User).all()
```

### 3. 避免 N+1 查询

```python
# ❌ N+1 问题
teachers = db.query(Teacher).all()
for teacher in teachers:
    print(teacher.courses)  # 每次循环都查询数据库

# ✅ 预加载
from sqlalchemy.orm import joinedload

teachers = db.query(Teacher)\
    .options(joinedload(Teacher.courses))\
    .all()
for teacher in teachers:
    print(teacher.courses)  # 不查询数据库
```

## 教学要点总结

### 核心概念
1. **ORM 映射**：类 ↔ 表，对象 ↔ 记录
2. **关系定义**：一对多、多对多
3. **CRUD 操作**：增删改查
4. **事务处理**：保证数据一致性
5. **查询优化**：避免 N+1，使用索引

### 常见陷阱
- ⚠️ 忘记 commit
- ⚠️ 忘记 close 会话
- ⚠️ N+1 查询问题
- ⚠️ 死锁和并发问题

## 相关文档

- [数据库设计](../02_系统架构/数据库设计.md) - 表结构设计
- [数据库规范](../../docs_开发规范/03_数据库规范.md) - 开发规范
- [FastAPI框架](./FastAPI框架.md) - Web 框架集成
