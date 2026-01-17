# 用户管理API改进说明

## 修改日期
2026-01-16

## 改进内容

### 1. 所有用户删除操作改为软删除

#### 问题描述
原有的用户删除操作中，`/api/users/{user_id}` 接口使用的是硬删除（`db.delete(user)`），这会导致数据永久丢失，不利于数据审计和恢复。

#### 解决方案
- 将 `users.py` 中的 `delete_user` 接口改为软删除
- 使用 `deleted_at` 字段标记删除时间
- 同时将 `is_active` 设置为 `False`

#### 影响的文件
- `backend/app/api/users.py`
- `backend/app/api/user_management.py`（已经是软删除，确认无误）

#### 代码改动
```python
# 原代码（硬删除）
db.delete(user)
db.commit()

# 新代码（软删除）
user.deleted_at = get_beijing_time_naive()
user.is_active = False
db.commit()
```

### 2. 管理员不能删除自己

#### 问题描述
需要明确提示"管理员不能删除自己"，防止管理员误操作删除自己的账户。

#### 解决方案
- 在删除用户前检查是否是当前登录用户
- 如果是，返回明确的错误提示："管理员不能删除自己"

#### 影响的文件
- `backend/app/api/users.py`
- `backend/app/api/user_management.py`

#### 代码改动
```python
# 管理员不能删除自己
if user.id == current_user.id:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="管理员不能删除自己的账户"
    )
```

### 3. API接口使用UUID代替ID

#### 问题描述
原有接口使用数据库自增ID作为路径参数，这会暴露系统的内部数据结构，不够安全。

#### 解决方案
- 将所有用户管理相关的API路径参数从 `user_id` (int) 改为 `user_uuid` (str)
- 查询时使用 `User.uuid` 字段进行匹配

#### 影响的接口

**users.py:**
1. `PUT /api/users/{user_uuid}` - 更新用户信息
2. `DELETE /api/users/{user_uuid}` - 删除用户
3. `PUT /api/users/{user_uuid}/toggle-status` - 切换用户状态
4. `POST /api/users/{user_uuid}/reset-password` - 重置密码

**user_management.py:**
1. `POST /api/user-management/users/{user_uuid}/assign-role` - 分配角色
2. `PUT /api/user-management/users/{user_uuid}` - 更新用户信息
3. `DELETE /api/user-management/users/{user_uuid}` - 删除用户

#### 代码改动示例
```python
# 原代码
@router.delete("/users/{user_id}")
async def delete_user(user_id: int, ...):
    user = db.query(User).filter(User.id == user_id).first()

# 新代码
@router.delete("/users/{user_uuid}")
async def delete_user(user_uuid: str, ...):
    user = db.query(User).filter(User.uuid == user_uuid).first()
```

### 4. 查询时过滤已删除用户

#### 改进内容
- 在用户列表查询中添加 `User.deleted_at.is_(None)` 过滤条件
- 在所有用户查询操作中都添加此过滤条件
- 确保软删除的用户不会出现在查询结果中

#### 代码改动
```python
# 用户列表查询
query = db.query(User).filter(User.deleted_at.is_(None))

# 单个用户查询
user = db.query(User).filter(
    User.uuid == user_uuid,
    User.deleted_at.is_(None)
).first()
```

## API调用示例

### 删除用户（软删除）

**请求:**
```bash
DELETE /api/users/{user_uuid}
Authorization: Bearer {token}
```

**成功响应:**
```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

**错误响应（删除自己）:**
```json
{
  "detail": "管理员不能删除自己的账户"
}
```

### 更新用户信息

**请求:**
```bash
PUT /api/users/{user_uuid}
Authorization: Bearer {token}
Content-Type: application/json

{
  "username": "new_username",
  "is_active": true
}
```

**成功响应:**
```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": 1,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "username": "new_username",
    "email": "user@example.com",
    "is_active": true,
    ...
  }
}
```

## 前端调整建议

### 1. 更新API调用
前端需要将所有用户管理相关的API调用从使用 `id` 改为使用 `uuid`：

```javascript
// 原代码
await api.delete(`/api/users/${user.id}`)

// 新代码
await api.delete(`/api/users/${user.uuid}`)
```

### 2. 删除按钮权限控制
在用户列表中，当用户是自己时，应该禁用或隐藏删除按钮：

```javascript
// 示例
<button 
  :disabled="user.uuid === currentUser.uuid"
  @click="deleteUser(user.uuid)"
>
  删除
</button>
```

### 3. 删除确认提示
删除用户时应该有明确的确认提示：

```javascript
if (user.uuid === currentUser.uuid) {
  ElMessage.error('不能删除自己的账户')
  return
}

ElMessageBox.confirm(
  `确定要删除用户 ${user.username} 吗？删除后可以从回收站恢复。`,
  '确认删除',
  { type: 'warning' }
).then(() => {
  // 执行删除
})
```

## 数据库注意事项

### User 表字段说明
- `id`: 数据库主键，仅供内部使用
- `uuid`: 对外唯一标识符，用于API调用
- `deleted_at`: 软删除时间戳，为NULL表示未删除
- `is_active`: 用户激活状态

### 恢复已删除用户
如需恢复已删除的用户，可以执行以下SQL：

```sql
-- 恢复用户
UPDATE core_users 
SET deleted_at = NULL, is_active = TRUE 
WHERE uuid = '550e8400-e29b-41d4-a716-446655440000';
```

## 测试建议

### 测试场景

1. **测试软删除功能**
   - 删除用户后，检查数据库中 `deleted_at` 字段是否有值
   - 删除用户后，用户列表中不应再显示该用户

2. **测试管理员删除自己**
   - 管理员尝试删除自己，应该返回错误提示
   - 错误提示应该是："管理员不能删除自己的账户"

3. **测试UUID接口**
   - 使用正确的UUID调用API，应该成功
   - 使用错误的UUID调用API，应该返回404
   - 使用已删除用户的UUID调用API，应该返回404

4. **测试权限控制**
   - 平台管理员应该可以删除所有用户（除了自己）
   - 学校管理员只能删除本校用户（除了自己）
   - 普通用户不应该有删除权限

## 向后兼容性

### 不兼容的变更
⚠️ **这是一个破坏性变更**，所有使用这些API的前端代码都需要更新：

1. 路径参数从 `user_id` 改为 `user_uuid`
2. 参数类型从 `int` 改为 `string`
3. 所有调用这些接口的代码都需要使用 `uuid` 而不是 `id`

### 迁移步骤
1. 确保数据库中所有用户都有有效的 `uuid` 值
2. 更新后端代码
3. 更新前端代码
4. 进行完整的测试
5. 部署上线

## 相关文档
- [用户管理权限体系](../01_认证授权/权限管理体系.md)
- [API开发规范](../../docs_开发规范/01_API开发规范.md)
- [数据库规范](../../docs_开发规范/03_数据库规范.md)
