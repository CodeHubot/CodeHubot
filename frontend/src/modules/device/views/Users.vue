<template>
  <div class="users-container">
    <div class="page-header">
      <h2>用户管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="handleAddUser">
          <el-icon><Plus /></el-icon>
          添加用户
        </el-button>
      </div>
    </div>

    <!-- 筛选条件 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-header">
        <div class="filter-title">
          <el-icon><Search /></el-icon>
          <span>筛选条件</span>
          <el-tag v-if="activeFilterCount > 0" size="small" type="primary" class="filter-count">
            {{ activeFilterCount }}
          </el-tag>
        </div>
        <el-button 
          link 
          type="primary" 
          @click="toggleFilterExpand"
          class="expand-btn"
        >
          {{ isFilterExpanded ? '收起' : '展开' }}
          <el-icon :class="{ 'rotate-180': isFilterExpanded }">
            <ArrowDown />
          </el-icon>
        </el-button>
      </div>
      
      <el-collapse-transition>
        <div v-show="isFilterExpanded" class="filter-content">
          <el-form :model="filterForm" label-width="80px" @keyup.enter="handleSearch">
            <el-row :gutter="20">
              <el-col :xs="24" :sm="12" :md="8" :lg="6">
                <el-form-item label="用户名">
                  <el-input 
                    v-model="filterForm.username" 
                    placeholder="请输入用户名" 
                    clearable 
                    @clear="handleSearch"
                  >
                    <template #prefix>
                      <el-icon><User /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </el-col>
              
              <el-col :xs="24" :sm="12" :md="8" :lg="6">
                <el-form-item label="邮箱">
                  <el-input 
                    v-model="filterForm.email" 
                    placeholder="请输入邮箱" 
                    clearable 
                    @clear="handleSearch"
                  >
                    <template #prefix>
                      <el-icon><Message /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </el-col>
              
              <el-col :xs="24" :sm="12" :md="8" :lg="6">
                <el-form-item label="角色">
                  <el-select 
                    v-model="filterForm.role" 
                    placeholder="请选择角色" 
                    clearable
                    @change="handleSearch"
                    style="width: 100%"
                  >
                    <el-option label="平台管理员" value="platform_admin">
                      <div class="option-item">
                        <el-tag type="danger" size="small">平台管理员</el-tag>
                      </div>
                    </el-option>
                    <el-option label="普通用户" value="individual">
                      <div class="option-item">
                        <el-tag type="primary" size="small">普通用户</el-tag>
                      </div>
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>
              
              <el-col :xs="24" :sm="12" :md="8" :lg="6">
                <el-form-item label="状态">
                  <el-select 
                    v-model="filterForm.is_active" 
                    placeholder="请选择状态" 
                    clearable
                    @change="handleSearch"
                    style="width: 100%"
                  >
                    <el-option label="启用" :value="true">
                      <div class="option-item">
                        <el-tag type="success" size="small">启用</el-tag>
                      </div>
                    </el-option>
                    <el-option label="禁用" :value="false">
                      <div class="option-item">
                        <el-tag type="info" size="small">禁用</el-tag>
                      </div>
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>
              
              <el-col :xs="24" :sm="12" :md="8" :lg="6">
                <el-form-item label="创建时间">
                  <el-date-picker
                    v-model="filterForm.created_date_range"
                    type="daterange"
                    range-separator="至"
                    start-placeholder="开始日期"
                    end-placeholder="结束日期"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    clearable
                    @change="handleSearch"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :xs="24" :sm="12" :md="8" :lg="6">
                <el-form-item label="最后登录">
                  <el-date-picker
                    v-model="filterForm.last_login_date_range"
                    type="daterange"
                    range-separator="至"
                    start-placeholder="开始日期"
                    end-placeholder="结束日期"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    clearable
                    @change="handleSearch"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row>
              <el-col :span="24">
                <el-form-item class="filter-actions">
                  <el-button type="primary" @click="handleSearch" :loading="loading">
                    <el-icon><Search /></el-icon>
                    查询
                  </el-button>
                  <el-button @click="resetFilter">
                    <el-icon><RefreshLeft /></el-icon>
                    重置
                  </el-button>
                  <el-button link type="info" @click="handleExport" v-if="users.length > 0">
                    <el-icon><Download /></el-icon>
                    导出数据
                  </el-button>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </el-collapse-transition>
    </el-card>

    <!-- 用户列表 -->
    <el-card class="users-card">
      <el-table :data="users" v-loading="loading" style="width: 100%">
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="role" label="角色">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.role)">{{ getRoleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态">
          <template #default="{ row }">
            <el-switch 
              v-model="row.is_active" 
              @change="handleToggleStatus(row)"
              :disabled="['platform_admin', 'super_admin'].includes(row.role)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录">
          <template #default="{ row }">
            {{ formatDateTime(row.last_login) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button size="small" @click="handleEditUser(row)">编辑</el-button>
            <el-button size="small" @click="handleResetPassword(row)">重置密码</el-button>
            <el-button 
              v-if="!['platform_admin', 'super_admin'].includes(row.role)" 
              size="small" 
              type="danger" 
              @click="handleDeleteUser(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑用户对话框 -->
    <el-dialog v-model="showCreateDialog" :title="editingUser ? '编辑用户' : '添加用户'" width="600px">
      <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="100px" autocomplete="off">
        <el-form-item label="用户名" prop="username">
          <el-input 
            v-model="userForm.username" 
            placeholder="请输入用户名" 
            :disabled="!!editingUser" 
            autocomplete="off"
            :name="`username-${Date.now()}`"
          />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input 
            v-model="userForm.email" 
            placeholder="请输入邮箱" 
            autocomplete="off"
            :name="`email-${Date.now()}`"
          />
        </el-form-item>
        <el-form-item v-if="!editingUser" label="密码" prop="password">
          <el-input 
            v-model="userForm.password" 
            type="password" 
            placeholder="请输入密码" 
            show-password 
            autocomplete="new-password"
            :name="`password-${Date.now()}`"
          />
          <div class="form-tip">密码需包含：至少8位，大小写字母、数字和特殊字符</div>
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select 
            v-model="userForm.role" 
            placeholder="请选择角色"
            autocomplete="off"
          >
            <el-option label="平台管理员" value="platform_admin" />
            <el-option label="普通用户" value="individual" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="handleSaveUser" :loading="saving">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="showPasswordDialog" title="重置密码" width="500px">
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px" autocomplete="off">
        <el-form-item label="新密码" prop="newPassword">
          <el-input 
            v-model="passwordForm.newPassword" 
            type="password" 
            placeholder="请输入新密码" 
            show-password 
            autocomplete="new-password"
            :name="`new-password-${Date.now()}`"
          />
          <div class="form-tip">密码需包含：至少8位，大小写字母、数字和特殊字符</div>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input 
            v-model="passwordForm.confirmPassword" 
            type="password" 
            placeholder="请再次输入密码" 
            show-password 
            autocomplete="new-password"
            :name="`confirm-password-${Date.now()}`"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showPasswordDialog = false">取消</el-button>
          <el-button type="primary" @click="handleConfirmResetPassword" :loading="resetting">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, 
  Search, 
  User, 
  Message, 
  RefreshLeft, 
  Download,
  ArrowDown 
} from '@element-plus/icons-vue'
import { getUserList, createUser, updateUser, deleteUser, toggleUserStatus, resetUserPassword } from '@/api/users'

const showCreateDialog = ref(false)
const showPasswordDialog = ref(false)
const userFormRef = ref()
const passwordFormRef = ref()
const editingUser = ref(null)
const resettingUser = ref(null)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const resetting = ref(false)
const isFilterExpanded = ref(true)

const filterForm = reactive({
  username: '',
  email: '',
  role: '',
  is_active: null,
  created_date_range: null,
  last_login_date_range: null
})

// 计算激活的筛选条件数量
const activeFilterCount = computed(() => {
  let count = 0
  if (filterForm.username) count++
  if (filterForm.email) count++
  if (filterForm.role) count++
  if (filterForm.is_active !== null) count++
  if (filterForm.created_date_range && filterForm.created_date_range.length === 2) count++
  if (filterForm.last_login_date_range && filterForm.last_login_date_range.length === 2) count++
  return count
})

// 切换筛选区展开/收起
const toggleFilterExpand = () => {
  isFilterExpanded.value = !isFilterExpanded.value
}

const users = ref([])

const userForm = reactive({
  username: '',
  email: '',
  password: '',
  role: 'individual'
})

const passwordForm = reactive({
  newPassword: '',
  confirmPassword: ''
})

const userRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少8位', trigger: 'blur' }
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

const passwordRules = {
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少8位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const getRoleLabel = (role) => {
  const labels = {
    platform_admin: '平台管理员',
    individual: '普通用户',
    // 兼容其他可能存在的角色
    team_admin: '学校管理员',
    teacher: '教师',
    student: '学生',
    channel_manager: '渠道经理',
    channel_partner: '渠道商',
    admin: '管理员',
    user: '普通用户'
  }
  return labels[role] || role
}

const getRoleTagType = (role) => {
  const types = {
    platform_admin: 'danger',
    individual: 'primary',
    // 兼容其他可能存在的角色
    team_admin: 'warning',
    teacher: 'success',
    student: 'primary',
    channel_manager: '',
    channel_partner: '',
    admin: 'warning',
    user: 'primary'
  }
  return types[role] || 'default'
}

const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  const date = new Date(dateTime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 加载用户列表
const loadUsers = async () => {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    
    if (filterForm.username) {
      params.username = filterForm.username
    }
    
    if (filterForm.email) {
      params.email = filterForm.email
    }
    
    if (filterForm.role) {
      params.role = filterForm.role
    }
    
    if (filterForm.is_active !== null) {
      params.is_active = filterForm.is_active
    }
    
    // 创建时间范围筛选
    if (filterForm.created_date_range && filterForm.created_date_range.length === 2) {
      params.created_start = filterForm.created_date_range[0]
      params.created_end = filterForm.created_date_range[1]
    }
    
    // 最后登录时间范围筛选
    if (filterForm.last_login_date_range && filterForm.last_login_date_range.length === 2) {
      params.last_login_start = filterForm.last_login_date_range[0]
      params.last_login_end = filterForm.last_login_date_range[1]
    }
    
    const response = await getUserList(params)
    console.log('用户列表响应:', response)
    
    // 响应拦截器返回格式：{ success: true, data: { items: [...], total: 2 } }
    if (response.data && response.data.items) {
      users.value = response.data.items
      total.value = response.data.total || 0
      console.log('加载用户数据:', users.value.length, '条，总计:', total.value)
    } else if (Array.isArray(response.data)) {
      // 兼容直接返回数组的情况
      users.value = response.data
      total.value = response.data.length
      console.log('加载用户数据（数组格式）:', users.value.length, '条')
    } else {
      console.warn('无法解析的响应格式:', response)
      users.value = []
      total.value = 0
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 查询
const handleSearch = () => {
  currentPage.value = 1
  loadUsers()
}

const resetFilter = () => {
  filterForm.username = ''
  filterForm.email = ''
  filterForm.role = ''
  filterForm.is_active = null
  filterForm.created_date_range = null
  filterForm.last_login_date_range = null
  currentPage.value = 1
  loadUsers()
}

// 导出数据
const handleExport = () => {
  try {
    // 导出当前筛选的数据为CSV
    const csvContent = generateCSV()
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `用户数据_${new Date().getTime()}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 生成CSV内容
const generateCSV = () => {
  const headers = ['用户名', '邮箱', '角色', '状态', '最后登录', '创建时间']
  const rows = users.value.map(user => [
    user.username,
    user.email,
    getRoleLabel(user.role),
    user.is_active ? '启用' : '禁用',
    formatDateTime(user.last_login),
    formatDateTime(user.created_at)
  ])
  
  const csvRows = [headers, ...rows]
  return csvRows.map(row => row.join(',')).join('\n')
}

const handleAddUser = () => {
  editingUser.value = null
  resetForm()
  showCreateDialog.value = true
}

const handleEditUser = (user) => {
  editingUser.value = user
  Object.assign(userForm, {
    username: user.username,
    email: user.email,
    role: user.role,
    password: '' // 编辑时不显示密码
  })
  showCreateDialog.value = true
}

const handleSaveUser = async () => {
  if (!userFormRef.value) return
  
  await userFormRef.value.validate(async (valid) => {
    if (valid) {
      saving.value = true
      try {
        if (editingUser.value) {
          // 更新用户
          await updateUser(editingUser.value.uuid, {
            username: userForm.username,
            is_active: editingUser.value.is_active // 保持原有状态
          })
          ElMessage.success('用户更新成功')
        } else {
          // 创建用户
          await createUser({
            username: userForm.username,
            email: userForm.email,
            password: userForm.password,
            role: userForm.role
          })
          ElMessage.success('用户创建成功')
        }
        
        resetForm()
        showCreateDialog.value = false
        loadUsers()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        saving.value = false
      }
    }
  })
}

const handleDeleteUser = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户"${user.username}"吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteUser(user.uuid)
    ElMessage.success('用户删除成功')
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除用户失败')
    }
  }
}

const handleToggleStatus = async (user) => {
  try {
    await toggleUserStatus(user.uuid)
    ElMessage.success(`用户已${user.is_active ? '启用' : '禁用'}`)
    loadUsers()
  } catch (error) {
    // 如果失败，恢复原状态
    user.is_active = !user.is_active
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const handleResetPassword = (user) => {
  resettingUser.value = user
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  showPasswordDialog.value = true
}

const handleConfirmResetPassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      resetting.value = true
      try {
        await resetUserPassword(resettingUser.value.uuid, passwordForm.newPassword)
        ElMessage.success('密码重置成功')
        showPasswordDialog.value = false
        passwordForm.newPassword = ''
        passwordForm.confirmPassword = ''
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '密码重置失败')
      } finally {
        resetting.value = false
      }
    }
  })
}

const resetForm = () => {
  Object.assign(userForm, {
    username: '',
    email: '',
    password: '',
    role: 'individual'
  })
  editingUser.value = null
  userFormRef.value?.resetFields()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  loadUsers()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadUsers()
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.users-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
  font-size: 20px;
  font-weight: 600;
}

.filter-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.filter-card :deep(.el-card__body) {
  padding: 16px 20px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.filter-title .el-icon {
  font-size: 16px;
  color: #409eff;
}

.filter-count {
  margin-left: 4px;
}

.expand-btn {
  font-size: 14px;
  padding: 4px 8px;
}

.expand-btn .el-icon {
  margin-left: 4px;
  transition: transform 0.3s;
}

.expand-btn .el-icon.rotate-180 {
  transform: rotate(180deg);
}

.filter-content {
  padding-top: 8px;
}

.filter-content .el-form {
  margin: 0;
}

.filter-content .el-form-item {
  margin-bottom: 18px;
}

.filter-content .el-form-item__label {
  font-weight: 500;
  color: #606266;
}

.filter-actions {
  text-align: left;
  margin-bottom: 0 !important;
}

.filter-actions .el-button {
  margin-right: 12px;
}

.option-item {
  display: flex;
  align-items: center;
}

.users-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.users-card :deep(.el-table) {
  font-size: 14px;
}

.users-card :deep(.el-table th) {
  background-color: #f5f7fa;
  font-weight: 600;
  color: #303133;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.5;
}

/* 响应式优化 */
@media screen and (max-width: 768px) {
  .users-container {
    padding: 12px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .filter-content .el-form-item__label {
    font-size: 13px;
  }
  
  .users-card :deep(.el-table) {
    font-size: 13px;
  }
}

/* 动画效果 */
.el-collapse-transition {
  transition: all 0.3s ease-in-out;
}
</style>
