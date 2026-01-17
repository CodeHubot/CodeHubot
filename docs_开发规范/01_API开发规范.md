# API 开发规范

> 本文档定义了 CodeHubot 项目的 API 开发规范，包括后端 API 设计和前端调用规范。

## 📋 目录

- [后端 API 规范](#后端-api-规范)
- [前端 API 调用规范](#前端-api-调用规范)
- [请求参数规范](#请求参数规范)
- [响应格式规范](#响应格式规范)
- [错误处理规范](#错误处理规范)
- [最佳实践](#最佳实践)

---

## 🎯 后端 API 规范

### 1. 统一响应格式

**所有后端接口必须使用统一的 `success_response` 函数返回数据，禁止直接返回字典！**

#### ❌ 错误示例 - 直接返回字典

```python
@router.get("/api/xxx")
def get_data():
    return {
        "success": True,
        "data": {...}
    }
```

#### ✅ 正确示例 - 使用 success_response

```python
from app.core.response import success_response

@router.get("/api/xxx")
def get_data():
    return success_response(data={...})
```

### 2. 标准响应格式

所有 API 接口必须返回以下统一格式：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    // 具体数据内容
  }
}
```

**字段说明：**
- `code`: 状态码（200表示成功，其他值表示失败）
- `message`: 响应消息（人类可读的提示信息）
- `data`: 响应数据（可以是对象、数组或null）

### 3. 避免双层嵌套

**禁止**在 `data` 字段中再次嵌套 `data` 字段：

#### ❌ 错误示例

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "data": {...},      // ❌ 双层嵌套
    "total": 100
  }
}
```

#### ✅ 正确示例

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "items": [...],     // ✅ 直接放数据
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

### 4. API 路由规范

#### RESTful 风格

```python
# 资源操作
GET    /api/{module}/resources          # 获取列表
POST   /api/{module}/resources          # 创建资源
GET    /api/{module}/resources/{uuid}   # 获取详情（使用UUID）
PUT    /api/{module}/resources/{uuid}   # 更新资源
DELETE /api/{module}/resources/{uuid}   # 删除资源

# 资源的子操作
POST   /api/{module}/resources/{uuid}/actions  # 对资源执行操作
GET    /api/{module}/resources/{uuid}/stats    # 获取资源统计
```

#### 路径参数使用 UUID

```python
# ✅ 推荐使用 UUID
@router.get("/courses/{course_uuid}")
def get_course(course_uuid: str, db: Session = Depends(get_db)):
    pass

# ❌ 避免使用数字 ID
@router.get("/courses/{course_id}")  # 不推荐
```

#### 版本控制（可选）

```python
# 如果需要 API 版本控制
/api/v1/courses
/api/v2/courses
```

### 5. 请求方法规范

| 方法 | 用途 | 是否幂等 | 示例 |
|------|------|----------|------|
| GET | 获取资源 | 是 | 获取课程列表 |
| POST | 创建资源 | 否 | 创建新课程 |
| PUT | 完整更新资源 | 是 | 更新课程全部信息 |
| PATCH | 部分更新资源 | 否 | 更新课程部分字段 |
| DELETE | 删除资源 | 是 | 删除课程 |

### 6. 依赖注入规范

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user, get_current_admin

@router.get("/protected-resource")
def get_protected_resource(
    db: Session = Depends(get_db),           # 数据库会话
    current_user = Depends(get_current_user) # 当前用户
):
    pass

# 管理员接口
@router.post("/admin-only")
def admin_only_action(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)  # 管理员权限
):
    pass
```

### 7. 查询参数规范

```python
from fastapi import Query
from typing import Optional

@router.get("/resources")
def list_resources(
    # 分页参数（必备）
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    
    # 筛选参数
    status: Optional[str] = Query(None, description="状态筛选"),
    category: Optional[str] = Query(None, description="类别筛选"),
    
    # 搜索参数
    search: Optional[str] = Query(None, description="搜索关键词"),
    
    # 排序参数
    order_by: Optional[str] = Query("created_at", description="排序字段"),
    order: Optional[str] = Query("desc", description="排序方向: asc/desc"),
    
    db: Session = Depends(get_db)
):
    pass
```

### 8. 分页响应格式

```python
# 分页数据必须包含以下字段
return success_response(data={
    "items": [...],          # 数据列表
    "total": 100,            # 总记录数
    "page": 1,               # 当前页码
    "page_size": 20,         # 每页数量
    "total_pages": 5         # 总页数（可选）
})
```

### 9. 日期时间格式

```python
from datetime import datetime
from app.utils.timezone import get_beijing_time_naive

# 创建时间戳
created_at = get_beijing_time_naive()

# 返回时转换为 ISO 8601 格式字符串
response_data = {
    "created_at": created_at.isoformat() if created_at else None
}
```

---

## 🌐 前端 API 调用规范

### 1. 统一请求工具

所有 API 调用必须使用统一的 `request` 工具：

```javascript
// ✅ 正确示例
import request from '@/utils/request'

export function getCourses(params) {
  return request({
    url: '/api/courses',
    method: 'get',
    params  // GET 请求使用 params
  })
}

export function createCourse(data) {
  return request({
    url: '/api/courses',
    method: 'post',
    data    // POST/PUT 请求使用 data
  })
}
```

### 2. API 文件组织

按模块组织 API 文件：

```
frontend/src/modules/{module}/api/
├── index.js          # 主 API（或导出文件）
├── courses.js        # 课程相关 API
├── users.js          # 用户相关 API
└── resources.js      # 资源相关 API
```

### 3. API 函数命名规范

```javascript
// 命名格式: {动作}{资源名}
export function getCourses() {}        // 获取列表
export function getCourseDetail() {}   // 获取详情
export function createCourse() {}      // 创建
export function updateCourse() {}      // 更新
export function deleteCourse() {}      // 删除

// 特殊操作
export function publishCourse() {}     // 发布课程
export function copyCourse() {}        // 复制课程
```

### 4. 请求参数处理

```javascript
export function getCourses(params) {
  return request({
    url: '/api/courses',
    method: 'get',
    params: {
      page: params.page || 1,
      page_size: params.pageSize || 20,
      search: params.search || undefined,  // 空值传 undefined
      status: params.status || undefined
    }
  })
}
```

### 5. 响应数据处理

```javascript
// 组件中调用 API
import { getAgents } from '@/modules/ai/api/agents'

async function loadCourses() {
  try {
    loading.value = true
    
    // 直接解构 data（request 工具已经提取了 response.data）
    const data = await getCourses({ page: 1, pageSize: 20 })
    
    // 使用响应数据
    courses.value = data.items
    total.value = data.total
    
  } catch (error) {
    // 错误已经在 request 工具中统一处理
    console.error('加载课程失败:', error)
  } finally {
    loading.value = false
  }
}
```

### 6. 错误处理

```javascript
// request 工具已经统一处理错误，组件中只需要捕获
try {
  const data = await createCourse(formData)
  ElMessage.success('创建成功')
  // 执行后续操作
} catch (error) {
  // 错误提示已经在 request 中显示
  // 这里可以执行额外的错误处理逻辑
  console.error('创建失败', error)
}
```

---

## 📝 请求参数规范

### 1. Pydantic Schema 验证

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class CourseCreate(BaseModel):
    """创建课程的请求模型"""
    
    # 必填字段
    title: str = Field(..., min_length=1, max_length=200, description="课程标题")
    description: Optional[str] = Field(None, max_length=2000, description="课程描述")
    
    # 枚举验证
    status: str = Field("draft", description="状态")
    
    # 自定义验证器
    @validator('status')
    def validate_status(cls, v):
        allowed_values = ['draft', 'published', 'archived']
        if v not in allowed_values:
            raise ValueError(f'状态必须是: {", ".join(allowed_values)}')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Python 基础课程",
                "description": "适合零基础学员",
                "status": "draft"
            }
        }

# 在路由中使用
@router.post("/courses")
def create_course(
    course: CourseCreate,  # FastAPI 自动验证
    db: Session = Depends(get_db)
):
    # 验证通过后的数据可以直接使用
    pass
```

### 2. 常用验证规则

```python
from pydantic import Field, EmailStr, HttpUrl, validator
from typing import Optional, List

class UserCreate(BaseModel):
    # 字符串长度
    username: str = Field(..., min_length=3, max_length=20)
    
    # 邮箱验证
    email: EmailStr
    
    # URL 验证
    website: Optional[HttpUrl] = None
    
    # 数值范围
    age: int = Field(..., ge=0, le=150)
    
    # 列表
    tags: List[str] = Field(default_factory=list)
    
    # 正则表达式
    phone: str = Field(..., pattern=r'^1[3-9]\d{9}$')
```

---

## 📤 响应格式规范

### 1. 成功响应

```python
from app.core.response import success_response

# 返回单个对象
return success_response(
    data=course_dict,
    message="获取成功"
)

# 返回列表（带分页）
return success_response(
    data={
        "items": course_list,
        "total": total_count,
        "page": page,
        "page_size": page_size
    }
)

# 返回空数据（成功但无数据）
return success_response(
    data=None,
    message="删除成功"
)
```

### 2. 错误响应

```python
from fastapi import HTTPException

# 参数错误
raise HTTPException(status_code=400, detail="参数验证失败")

# 未认证
raise HTTPException(status_code=401, detail="未登录或token已过期")

# 无权限
raise HTTPException(status_code=403, detail="无权访问该资源")

# 资源不存在
raise HTTPException(status_code=404, detail="课程不存在")

# 服务器错误
raise HTTPException(status_code=500, detail="服务器内部错误")
```

### 3. 业务错误响应

```python
from app.core.response import error_response

# 业务逻辑错误（返回 200，但 code 不是 200）
return error_response(
    code=4001,
    message="课程名称已存在",
    status_code=400
)
```

---

## ⚠️ 错误处理规范

### 1. 异常捕获

```python
@router.post("/courses")
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    try:
        # 业务逻辑
        new_course = Course(**course.dict())
        db.add(new_course)
        db.commit()
        db.refresh(new_course)
        
        return success_response(data=new_course.to_dict())
        
    except IntegrityError as e:
        # 数据库约束错误
        db.rollback()
        raise HTTPException(status_code=400, detail="数据已存在或违反约束")
        
    except Exception as e:
        # 其他错误
        db.rollback()
        logger.error(f"创建课程失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建失败")
```

### 2. 统一异常处理器

```python
# 在 main.py 中注册
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """统一处理 HTTP 异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None
        }
    )
```

---

## 💡 最佳实践

### 1. API 文档注释

```python
@router.get("/courses/{course_uuid}", summary="获取课程详情")
def get_course_detail(
    course_uuid: str,
    db: Session = Depends(get_db)
):
    """
    获取指定课程的详细信息
    
    Args:
        course_uuid: 课程的 UUID
        
    Returns:
        课程详细信息，包括单元、资源、任务等
        
    Raises:
        404: 课程不存在
        403: 无权访问
    """
    pass
```

### 2. 数据转换

```python
# 模型转字典方法
class Course(Base):
    def to_dict(self, include_relations=False):
        """转换为字典"""
        data = {
            "uuid": self.uuid,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        if include_relations:
            data["units"] = [unit.to_dict() for unit in self.units]
            
        return data
```

### 3. 权限检查

```python
def check_course_permission(course_uuid: str, user, db: Session):
    """检查用户是否有权限访问课程"""
    course = db.query(Course).filter(Course.uuid == course_uuid).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
        
    if course.school_id != user.school_id:
        raise HTTPException(status_code=403, detail="无权访问该课程")
        
    return course

@router.get("/courses/{course_uuid}")
def get_course(
    course_uuid: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    course = check_course_permission(course_uuid, current_user, db)
    return success_response(data=course.to_dict())
```

### 4. 批量操作

```python
from typing import List

class BatchDeleteRequest(BaseModel):
    uuids: List[str] = Field(..., min_items=1, max_items=100)

@router.post("/courses/batch-delete")
def batch_delete_courses(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db)
):
    """批量删除课程"""
    deleted_count = db.query(Course).filter(
        Course.uuid.in_(request.uuids)
    ).delete(synchronize_session=False)
    
    db.commit()
    
    return success_response(
        data={"deleted_count": deleted_count},
        message=f"成功删除 {deleted_count} 个课程"
    )
```

---

## 📚 参考资源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Pydantic 文档](https://pydantic-docs.helpmanual.io/)
- [RESTful API 设计指南](https://restfulapi.net/)
- 项目现有文档: `frontend/API_SPECIFICATION.md`

---

**记住**: 统一的 API 规范是前后端协作的基础，严格遵守规范可以大幅减少沟通成本和调试时间！
