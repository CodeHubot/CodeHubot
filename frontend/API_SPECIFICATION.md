# 前端 API 调用规范

## 📋 目录

1. [后端响应格式标准](#后端响应格式标准)
2. [前端请求配置](#前端请求配置)
3. [API调用示例](#api调用示例)
4. [最佳实践](#最佳实践)
5. [常见问题](#常见问题)

---

## 🎯 后端响应格式标准

### ⚠️ 重要说明

**所有后端接口必须使用统一的 `success_response` 函数返回数据，禁止直接返回字典！**

```python
# ❌ 错误示例 - 直接返回字典
@router.get("/api/xxx")
def get_data():
    return {
        "success": True,
        "data": {...}
    }

# ✅ 正确示例 - 使用 success_response
from ...core.response import success_response

@router.get("/api/xxx")
def get_data():
    return success_response(data={...})
```

### 统一响应格式

**所有API接口必须返回以下统一格式：**

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    // 具体数据内容
  }
}
```

### ⚠️ 避免双层嵌套

**常见错误：直接返回字典导致双层嵌套**

如果后端接口直接返回：
```python
return {
    "success": True,
    "data": {"items": [...]}
}
```

会被全局响应包装器再包装一层，形成：
```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "success": true,
    "data": {
      "items": [...]
    }
  }
}
```

这会导致前端需要多层解析：`response.data.data.data.items`

**正确做法：**
```python
from ...core.response import success_response

return success_response(data={
    "items": [...],
    "total": 100
})
```

最终返回：
```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "items": [...],
    "total": 100
  }
}
```

前端只需解析：`response.data.items`

### 状态码规范

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 200 | 成功 | 操作成功 |
| 400 | 请求错误 | 参数验证失败 |
| 401 | 未授权 | 未登录或token过期 |
| 403 | 禁止访问 | 无权限 |
| 404 | 资源不存在 | 请求的资源不存在 |
| 500 | 服务器错误 | 服务器内部错误 |

### 列表响应格式

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

### 详情响应格式

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "id": 1,
    "name": "示例",
    ...
  }
}
```

### 操作响应格式（创建/更新/删除）

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "id": 1,
    "uuid": "xxx-xxx-xxx"
  }
}
```

### 错误响应格式

```json
{
  "code": 400,
  "message": "参数错误",
  "data": null
}
```

---

## ⚙️ 前端请求配置

### 1. 统一请求工具 (`src/utils/request.js`)

已配置的功能：
- ✅ 自动添加认证令牌
- ✅ 统一处理响应格式（兼容两种格式）
- ✅ 统一错误处理和提示
- ✅ 401自动跳转登录
- ✅ 请求超时配置

### 2. API辅助工具 (`src/utils/apiHelper.js`)

提供的工具函数：
- `handleListResponse()` - 处理列表响应
- `handleDetailResponse()` - 处理详情响应
- `handleOperationResponse()` - 处理操作响应
- `buildQueryParams()` - 构建查询参数
- `buildPaginationParams()` - 构建分页参数
- `formatDateTime()` - 格式化日期时间
- `debounce()` - 防抖
- `throttle()` - 节流
- `deepClone()` - 深拷贝

---

## 📝 API调用示例

### 方式一：使用封装的request方法（推荐）

```vue
<script setup>
import { ref, reactive, onMounted } from 'vue'
import { get, post, put, del } from '@/utils/request'
import { handleListResponse, handleDetailResponse, buildPaginationParams } from '@/utils/apiHelper'
import { ElMessage } from 'element-plus'

// ============ 列表查询示例 ============
const loading = ref(false)
const dataList = ref([])
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const loadList = async () => {
  try {
    loading.value = true
    
    // 构建分页参数
    const params = buildPaginationParams(
      pagination.page,
      pagination.pageSize,
      {
        search: 'keyword',  // 其他筛选条件
        status: 'active'
      }
    )
    
    // 发送请求
    const response = await get('/pbl/admin/courses/templates', params)
    
    // 处理响应
    const { items, total } = handleListResponse(response)
    dataList.value = items
    pagination.total = total
    
  } catch (error) {
    // 错误已经在拦截器中处理，这里可以做额外处理
    console.error('加载失败:', error)
  } finally {
    loading.value = false
  }
}

// ============ 详情查询示例 ============
const detail = ref(null)

const loadDetail = async (uuid) => {
  try {
    loading.value = true
    
    const response = await get(`/pbl/admin/courses/templates/${uuid}/full-detail`)
    
    // 处理响应
    const data = handleDetailResponse(response)
    if (data) {
      detail.value = data
    }
    
  } catch (error) {
    console.error('加载详情失败:', error)
  } finally {
    loading.value = false
  }
}

// ============ 创建示例 ============
const handleCreate = async (formData) => {
  try {
    const response = await post('/pbl/admin/courses/templates', formData)
    
    if (response.success) {
      ElMessage.success('创建成功')
      loadList() // 刷新列表
    }
    
  } catch (error) {
    console.error('创建失败:', error)
  }
}

// ============ 更新示例 ============
const handleUpdate = async (uuid, formData) => {
  try {
    const response = await put(`/pbl/admin/courses/templates/${uuid}`, formData)
    
    if (response.success) {
      ElMessage.success('更新成功')
      loadDetail(uuid) // 刷新详情
    }
    
  } catch (error) {
    console.error('更新失败:', error)
  }
}

// ============ 删除示例 ============
const handleDelete = async (uuid) => {
  try {
    const response = await del(`/pbl/admin/courses/templates/${uuid}`)
    
    if (response.success) {
      ElMessage.success('删除成功')
      loadList() // 刷新列表
    }
    
  } catch (error) {
    console.error('删除失败:', error)
  }
}

// 初始化
onMounted(() => {
  loadList()
})
</script>
```

### 方式二：使用原始axios（不推荐，仅特殊场景）

```javascript
import axios from 'axios'

const response = await axios.get('/api/xxx', {
  headers: {
    Authorization: `Bearer ${token}`
  }
})

// 手动处理响应格式
if (response.data && (response.data.success || response.data.code === 200)) {
  const data = response.data.data
  // 处理数据
}
```

---

## 🎯 最佳实践

### 1. 统一使用封装的request方法

❌ **不推荐：**
```javascript
import axios from 'axios'

const response = await axios.get('/api/xxx')
if (response.data.success || response.data.code === 200) {
  // ...
}
```

✅ **推荐：**
```javascript
import { get } from '@/utils/request'

const response = await get('/xxx')
// response已经统一处理，直接使用
if (response.success) {
  const data = response.data
}
```

### 2. 使用辅助函数处理数据

❌ **不推荐：**
```javascript
const response = await get('/xxx/list')
dataList.value = response.data.items || response.data.list || []
pagination.total = response.data.total || 0
```

✅ **推荐：**
```javascript
import { handleListResponse } from '@/utils/apiHelper'

const response = await get('/xxx/list')
const { items, total } = handleListResponse(response)
dataList.value = items
pagination.total = total
```

### 3. 构建查询参数时过滤空值

❌ **不推荐：**
```javascript
const params = {
  page: 1,
  page_size: 20,
  search: filters.search,      // 可能是空字符串
  status: filters.status,      // 可能是null
  category: filters.category   // 可能是undefined
}
```

✅ **推荐：**
```javascript
import { buildPaginationParams } from '@/utils/apiHelper'

const params = buildPaginationParams(1, 20, {
  search: filters.search,
  status: filters.status,
  category: filters.category
})
// 自动过滤空值
```

### 4. 错误处理

❌ **不推荐：**
```javascript
try {
  const response = await get('/xxx')
  // 没有任何错误提示
} catch (error) {
  // 不处理错误
}
```

✅ **推荐：**
```javascript
try {
  const response = await get('/xxx')
  // 处理成功逻辑
} catch (error) {
  // 拦截器已经显示错误提示
  // 这里只需记录或做额外处理
  console.error('操作失败:', error)
  // 可选：额外的错误处理逻辑
}
```

### 5. Loading状态管理

✅ **推荐：**
```javascript
const loading = ref(false)

const loadData = async () => {
  try {
    loading.value = true
    const response = await get('/xxx')
    // 处理数据
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false  // 确保loading状态正确
  }
}
```

### 6. 文件上传

```javascript
import { upload } from '@/utils/request'

const handleUpload = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const response = await upload('/upload', formData, (percent) => {
      console.log('上传进度:', percent)
    })
    
    if (response.success) {
      ElMessage.success('上传成功')
    }
  } catch (error) {
    console.error('上传失败:', error)
  }
}
```

### 7. 文件下载

```javascript
import { download } from '@/utils/request'

const handleDownload = async () => {
  try {
    await download('/export', 'template.xlsx', {
      type: 'template'
    })
  } catch (error) {
    console.error('下载失败:', error)
  }
}
```

---

## ❓ 常见问题

### Q1: 为什么我的请求没有自动带token?

**A:** 确保你使用的是封装后的request方法：
```javascript
// ❌ 错误：直接使用axios
import axios from 'axios'

// ✅ 正确：使用封装的request
import { get, post } from '@/utils/request'
```

### Q2: 响应数据格式不一致怎么办？

**A:** 使用 `handleListResponse` 或 `handleDetailResponse` 辅助函数，它们会自动处理不同的数据格式。

### Q3: 如何处理特殊的API响应？

**A:** 可以直接访问 `response.data`：
```javascript
const response = await get('/xxx')
if (response.success) {
  // 标准字段
  const data = response.data
  
  // 原始响应（如果需要）
  const originalRes = response.originalResponse
}
```

### Q4: 401错误后会自动跳转登录吗？

**A:** 是的，拦截器已经配置了401自动跳转到 `/login` 并清除token。

### Q5: 如何禁用错误提示？

**A:** 在请求配置中添加 `skipErrorMessage: true`（需要在拦截器中扩展支持）。

### Q6: 为什么会出现双层嵌套的响应格式？

**A:** 这是因为后端接口**直接返回字典**而不是使用 `success_response` 函数。

**错误示例（后端）：**
```python
@router.get("/api/xxx")
def get_data():
    return {"success": True, "data": {...}}  # ❌ 错误
```

**正确示例（后端）：**
```python
from ...core.response import success_response

@router.get("/api/xxx")
def get_data():
    return success_response(data={...})  # ✅ 正确
```

**解决方案：**
1. 后端统一使用 `success_response` 函数
2. 前端已做兼容处理，可以自动识别双层嵌套格式

### Q7: 如何检查后端接口是否规范？

**A:** 检查以下几点：
1. ✅ 所有接口都导入了 `success_response`
2. ✅ 所有返回都使用 `success_response(data=...)` 或 `success_response(message=...)`
3. ❌ 没有直接返回字典 `return {"success": True, ...}`
4. ✅ 错误处理使用 `raise HTTPException` 或 `error_response`

**快速检查命令：**
```bash
# 查找可能有问题的文件
grep -r 'return {' backend/app/api/ | grep -v 'success_response'
```

---

## 📚 参考文件

- `src/utils/request.js` - 统一请求配置和拦截器
- `src/utils/apiHelper.js` - API调用辅助工具
- `src/utils/responseHandler.js` - 响应处理工具（已弃用，使用request.js）

---

## 🔄 迁移指南

### 旧代码迁移步骤

1. **替换axios导入**
   ```javascript
   // 旧代码
   import axios from 'axios'
   
   // 新代码
   import { get, post, put, del } from '@/utils/request'
   ```

2. **简化请求调用**
   ```javascript
   // 旧代码
   const response = await axios.get('/api/xxx', {
     headers: { Authorization: `Bearer ${token}` }
   })
   
   // 新代码
   const response = await get('/xxx')  // token自动添加
   ```

3. **使用辅助函数**
   ```javascript
   // 旧代码
   if (response.data && response.data.success) {
     dataList.value = response.data.data.items || []
   }
   
   // 新代码
   import { handleListResponse } from '@/utils/apiHelper'
   const { items } = handleListResponse(response)
   dataList.value = items
   ```

---

## ✅ 检查清单

### 前端检查清单

迁移完成后，请检查：

- [ ] 所有API调用都使用封装的request方法
- [ ] 不再直接使用 `axios`
- [ ] 不再手动添加 `Authorization` header
- [ ] 列表接口使用 `handleListResponse` 处理
- [ ] 详情接口使用 `handleDetailResponse` 处理
- [ ] 查询参数使用 `buildQueryParams` 构建
- [ ] 所有接口都有 try-catch 和 loading 状态
- [ ] 错误处理逻辑简化（拦截器已处理）

### 后端检查清单

确保后端接口规范：

- [ ] ✅ 所有接口文件都导入了 `success_response`
  ```python
  from ...core.response import success_response
  ```

- [ ] ✅ 所有正常返回都使用 `success_response`
  ```python
  return success_response(data={...}, message="操作成功")
  ```

- [ ] ❌ 没有直接返回字典
  ```python
  # 禁止这样做
  return {"success": True, "data": {...}}
  ```

- [ ] ✅ 列表接口返回标准格式
  ```python
  return success_response(data={
      "items": [...],
      "total": 100,
      "page": 1,
      "page_size": 20
  })
  ```

- [ ] ✅ 详情接口返回数据对象
  ```python
  return success_response(data={
      "id": 1,
      "name": "示例",
      ...
  })
  ```

- [ ] ✅ 操作接口（创建/更新/删除）有明确的消息
  ```python
  return success_response(
      data={"id": new_id},
      message="创建成功"
  )
  ```

- [ ] ✅ 错误处理使用异常或 error_response
  ```python
  # 方式1：使用 HTTPException
  if not found:
      raise HTTPException(status_code=404, detail="资源不存在")
  
  # 方式2：使用 error_response
  if not found:
      return error_response(message="资源不存在", code=404)
  ```

### 快速检查命令

```bash
# 检查是否有直接返回字典的情况
cd backend
grep -r 'return {' app/api/pbl/*.py | grep -v 'success_response' | grep -v 'error_response'

# 检查是否所有文件都导入了 success_response
grep -L 'from.*response import success_response' app/api/pbl/*.py
```

---

**最后更新时间**: 2025-12-18

**维护人员**: 开发团队

**版本**: v2.0

---

## 📝 更新日志

### v2.0 (2025-12-18)
- ✅ 添加了后端响应格式规范
- ✅ 明确禁止直接返回字典
- ✅ 添加了 success_response 使用指南
- ✅ 添加了后端开发规范
- ✅ 添加了代码检查工具
- ✅ 强调避免双层嵌套问题
- ✅ 添加了完整的错误处理规范

### v1.0 (2025-12-18)
- ✅ 初始版本
- ✅ 前端请求配置
- ✅ API调用示例
- ✅ 最佳实践指南
