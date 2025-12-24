<template>
  <div class="school-user-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>学校用户管理</span>
          <div class="header-actions">
            <el-button type="primary" @click="handleCreate">
              <el-icon><Plus /></el-icon>
              创建账号
            </el-button>
            <el-button type="success" @click="handleBatchImport">
              <el-icon><Upload /></el-icon>
              批量导入
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="角色">
          <el-select 
            v-model="filters.role" 
            placeholder="请选择角色" 
            clearable 
            style="width: 150px"
            @change="handleFilter"
          >
            <el-option label="教师" value="teacher" />
            <el-option label="学生" value="student" />
          </el-select>
        </el-form-item>
        <el-form-item label="搜索">
          <el-input 
            v-model="filters.search" 
            placeholder="姓名/用户名/学号" 
            clearable
            style="width: 250px"
            @keyup.enter="handleFilter"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleFilter">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetFilters">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 统计信息 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="8">
          <el-statistic title="教师总数" :value="stats.teachers">
            <template #suffix>
              / {{ stats.max_teachers }}
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="8">
          <el-statistic title="学生总数" :value="stats.students">
            <template #suffix>
              / {{ stats.max_students }}
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="8">
          <el-statistic title="激活用户" :value="stats.active" />
        </el-col>
      </el-row>

      <!-- 数据表格 -->
      <el-table 
        :data="users" 
        v-loading="loading" 
        stripe
        style="width: 100%"
      >
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'teacher' ? 'success' : 'primary'" size="small">
              {{ getRoleText(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="工号/学号" width="150">
          <template #default="{ row }">
            {{ row.teacher_number || row.student_number || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="class_name" label="班级" width="150">
          <template #default="{ row }">
            {{ row.class_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="gender" label="性别" width="100">
          <template #default="{ row }">
            <el-tag :type="row.gender === 'male' ? 'primary' : 'danger'" size="small">
              {{ row.gender === 'male' ? '男' : row.gender === 'female' ? '女' : '其他' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button 
              size="small" 
              :type="row.is_active ? 'warning' : 'success'"
              @click="handleToggleActive(row)"
              :disabled="isCurrentAdmin(row) && row.is_active"
              :title="isCurrentAdmin(row) && row.is_active ? '不能禁用自己的账号' : ''"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="info" @click="handleResetPassword(row)">
              重置密码
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '创建用户' : '编辑用户'"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="角色" prop="role">
              <el-select v-model="form.role" placeholder="请选择角色" style="width: 100%" :disabled="dialogMode === 'edit'">
                <el-option label="教师" value="teacher" />
                <el-option label="学生" value="student" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别" prop="gender">
              <el-select v-model="form.gender" placeholder="请选择性别" style="width: 100%">
                <el-option label="男" value="male" />
                <el-option label="女" value="female" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="form.name" placeholder="真实姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="form.role === 'teacher' ? '工号' : '学号'" :prop="form.role === 'teacher' ? 'teacher_number' : 'student_number'">
              <el-input 
                v-if="form.role === 'teacher'" 
                v-model="form.teacher_number" 
                placeholder="教师工号（必填）" 
                :disabled="dialogMode === 'edit'"
              />
              <el-input 
                v-else 
                v-model="form.student_number" 
                placeholder="学生学号（必填）" 
                :disabled="dialogMode === 'edit'"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20" v-if="dialogMode === 'create'">
          <el-col :span="12">
            <el-form-item label="密码" prop="password">
              <el-input v-model="form.password" type="password" placeholder="登录密码" show-password />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input v-model="form.confirm_password" type="password" placeholder="确认密码" show-password />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="班级" v-if="form.role === 'student'">
              <el-select v-model="form.class_id" placeholder="请选择班级" style="width: 100%" filterable>
                <el-option
                  v-for="cls in classes"
                  :key="cls.id"
                  :label="cls.class_name"
                  :value="cls.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="学科" v-else>
              <el-input v-model="form.subject" placeholder="任教学科" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-alert
          type="info"
          :closable="false"
          style="margin-top: 10px"
        >
          <template #default>
            <div style="font-size: 13px; line-height: 1.8;">
              <div><strong>用户名规则：</strong>自动生成为"工号/学号@学校代码"的格式</div>
              <div style="margin-top: 8px;"><strong>密码要求：</strong></div>
              <ul style="margin: 5px 0; padding-left: 20px;">
                <li>至少 8 位字符</li>
                <li>必须包含大小写字母、数字、特殊字符中的至少 2 种</li>
                <li>不能与用户名相同</li>
                <li>不能使用常见弱密码（如 12345678、password 等）</li>
              </ul>
            </div>
          </template>
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入对话框 -->
    <el-dialog
      v-model="importDialogVisible"
      title="批量导入用户"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="用户类型">
          <el-radio-group v-model="importType">
            <el-radio value="student">学生</el-radio>
            <el-radio value="teacher">教师</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="模板下载">
          <el-button type="success" size="small" @click="downloadTemplate">
            <el-icon><Download /></el-icon>
            下载{{ importType === 'student' ? '学生' : '教师' }}导入模板
          </el-button>
        </el-form-item>

        <el-form-item label="选择文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".csv"
            :on-change="handleFileChange"
            :file-list="fileList"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              选择CSV文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                仅支持CSV格式文件，文件需使用UTF-8编码
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-alert
          title="导入说明"
          type="info"
          :closable="false"
          style="margin-top: 20px"
        >
          <template #default>
            <div>
              <p><strong>学生导入格式：</strong>name, student_number, class_name, gender, password</p>
              <p><strong>教师导入格式：</strong>name, teacher_number, subject, gender, password</p>
              <p><strong>重要提示：</strong></p>
              <ul style="margin: 5px 0; padding-left: 20px;">
                <li>用户名将自动生成为"学号/工号@学校编码"</li>
                <li><strong>必填字段：</strong>姓名(name)、学号/工号、性别(gender)</li>
                <li><strong>性别：</strong>直接填写"男"或"女"即可</li>
                <li><strong>班级：</strong>填写已创建的班级名称（如：一年级1班）</li>
                <li>如果不提供密码，默认密码为 123456</li>
              </ul>
            </div>
          </template>
        </el-alert>
      </el-form>

      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleImportSubmit" 
          :loading="importing"
          :disabled="!selectedFile"
        >
          开始导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Edit, Upload, Download } from '@element-plus/icons-vue'
import request from '@/utils/request'

const loading = ref(false)
const submitting = ref(false)
const importing = ref(false)
const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const dialogMode = ref('create') // 'create' or 'edit'
const formRef = ref(null)
const uploadRef = ref(null)

const users = ref([])
const classes = ref([])
const selectedFile = ref(null)
const fileList = ref([])
const importType = ref('student')

const adminInfo = ref(JSON.parse(localStorage.getItem('admin_info') || '{}'))

const filters = reactive({
  role: '',
  search: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const stats = reactive({
  teachers: 0,
  max_teachers: 0,
  students: 0,
  max_students: 0,
  active: 0
})

const form = reactive({
  user_id: null,
  role: 'student',
  name: '',
  password: '',
  confirm_password: '',
  gender: '',
  teacher_number: '',
  student_number: '',
  class_id: null,
  subject: ''
})

// 常见弱密码列表
const weakPasswords = [
  '12345678', '123456789', '11111111', '00000000',
  'password', 'Password', 'password123', 'Password123',
  'qwerty123', 'abc12345', 'abcd1234', '1qaz2wsx',
  '88888888', '66666666', '11223344', '12341234'
]

const validatePassword = (rule, value, callback) => {
  if (dialogMode.value === 'create') {
    if (!value) {
      callback(new Error('请输入密码'))
      return
    }
    
    // 1. 长度检查：至少8位
    if (value.length < 8) {
      callback(new Error('密码长度不能少于8位'))
      return
    }
    
    // 2. 不能是常见弱密码
    if (weakPasswords.includes(value.toLowerCase())) {
      callback(new Error('密码过于简单，请使用更复杂的密码'))
      return
    }
    
    // 3. 生成用户名并检查密码是否与用户名相同
    const schoolCode = adminInfo.value.school_code || ''
    let username = ''
    if (form.role === 'teacher' && form.teacher_number) {
      username = `${form.teacher_number}@${schoolCode}`
    } else if (form.role === 'student' && form.student_number) {
      username = `${form.student_number}@${schoolCode}`
    }
    
    if (username && value.toLowerCase() === username.toLowerCase()) {
      callback(new Error('密码不能与用户名相同'))
      return
    }
    
    // 4. 复杂度检查：至少包含大小写字母、数字、特殊字符中的2种
    const hasLower = /[a-z]/.test(value)
    const hasUpper = /[A-Z]/.test(value)
    const hasDigit = /\d/.test(value)
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]/.test(value)
    
    const complexityCount = [hasLower, hasUpper, hasDigit, hasSpecial].filter(Boolean).length
    
    if (complexityCount < 2) {
      callback(new Error('密码必须包含大小写字母、数字、特殊字符中的至少2种'))
      return
    }
  }
  
  callback()
}

const validateConfirmPassword = (rule, value, callback) => {
  if (dialogMode.value === 'create' && value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  teacher_number: [{ required: true, message: '请输入职工号', trigger: 'blur' }],
  student_number: [{ required: true, message: '请输入学号', trigger: 'blur' }],
  password: [{ validator: validatePassword, trigger: 'blur' }],
  confirm_password: [{ validator: validateConfirmPassword, trigger: 'blur' }]
}

// API请求
// 加载用户列表
const loadUsers = async () => {
  try {
    loading.value = true
    
    const params = {
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize,
      role: filters.role || undefined,
      keyword: filters.search || undefined
    }
    
    // 使用便捷API，无需传递 school_uuid，更安全
    const response = await request.get('/pbl/admin/schools/my-school/users', { params })
    
    if (response.success) {
      users.value = response.data.items || []
      pagination.total = response.data.total || 0
    }
  } catch (error) {
    console.error('加载用户列表失败:', error)
    ElMessage.error(error.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

// 加载统计信息
const loadStats = async () => {
  try {
    // 使用便捷API，无需传递 school_uuid，更安全
    const response = await request.get('/pbl/admin/schools/my-school/statistics')
    
    if (response.success) {
      const data = response.data
      stats.teachers = data.teacher_count || 0
      stats.max_teachers = data.max_teachers || 0
      stats.students = data.student_count || 0
      stats.max_students = data.max_students || 0
    }
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

// 加载班级列表
const loadClasses = async () => {
  try {
    const response = await request.get('/pbl/admin/classes-groups/classes')
    
    if (response.success) {
      classes.value = response.data || []
    }
  } catch (error) {
    console.error('加载班级列表失败:', error)
  }
}

// 打开创建对话框
const handleCreate = () => {
  dialogMode.value = 'create'
  resetForm()
  dialogVisible.value = true
}

// 打开编辑对话框
const handleEdit = (row) => {
  dialogMode.value = 'edit'
  Object.assign(form, {
    user_id: row.id,
    role: row.role,
    name: row.name,
    gender: row.gender,
    teacher_number: row.teacher_number,
    student_number: row.student_number,
    class_id: row.class_id,
    subject: row.subject
  })
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    user_id: null,
    role: 'student',
    name: '',
    password: '',
    confirm_password: '',
    gender: '',
    teacher_number: '',
    student_number: '',
    class_id: null,
    subject: ''
  })
  formRef.value?.resetFields()
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    submitting.value = true
    
    const data = {
      role: form.role,
      name: form.name,
      gender: form.gender
    }
    
    if (dialogMode.value === 'create') {
      data.password = form.password
      // 学校ID由后端从管理员信息中获取，更安全
    }
    
    if (form.role === 'teacher') {
      data.teacher_number = form.teacher_number
      data.subject = form.subject
    } else {
      data.student_number = form.student_number
      data.class_id = form.class_id
    }
    
    let response
    if (dialogMode.value === 'create') {
      response = await request.post('/pbl/admin/users', data)
    } else {
      response = await request.put(`/pbl/admin/users/${form.user_id}`, data)
    }
    
    if (response.success) {
      ElMessage.success(dialogMode.value === 'create' ? '创建成功！' : '更新成功！')
      dialogVisible.value = false
      loadUsers()
      loadStats()
    }
  } catch (error) {
    if (error.errors) {
      return
    }
    console.error('提交失败:', error)
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 判断是否是当前登录的管理员
const isCurrentAdmin = (row) => {
  return row.role === 'school_admin' && row.id === adminInfo.value.id
}

// 启用/禁用用户
const handleToggleActive = async (row) => {
  // 防止禁用自己的账号
  if (isCurrentAdmin(row) && row.is_active) {
    ElMessage.warning('不能禁用自己的账号')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要${row.is_active ? '禁用' : '启用'}用户"${row.name}"吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await request.patch(`/pbl/admin/users/${row.id}/toggle-active`, {})
    
    if (response.success) {
      ElMessage.success(response.message)
      loadUsers()
    }
  } catch (error) {
    if (error === 'cancel') {
      return
    }
    console.error('操作失败:', error)
    ElMessage.error(error.message || '操作失败')
  }
}

// 重置密码
const handleResetPassword = async (row) => {
  try {
    // 先显示密码要求提示
    await ElMessageBox.alert(
      '密码要求：\n' +
      '• 至少 8 位字符\n' +
      '• 必须包含大小写字母、数字、特殊字符中的至少 2 种\n' +
      '• 不能与用户名相同\n' +
      '• 不能使用常见弱密码',
      '密码要求',
      {
        confirmButtonText: '我知道了',
        type: 'info'
      }
    )
    
    const { value: newPassword } = await ElMessageBox.prompt(
      `请为用户"${row.name}"设置新密码`,
      '重置密码',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /.{8,}/,
        inputErrorMessage: '密码长度不能少于8位',
        inputType: 'password'
      }
    )
    
    const response = await request.post(`/pbl/admin/users/${row.id}/reset-password`, 
      { new_password: newPassword }
    )
    
    if (response.success) {
      ElMessage.success('密码重置成功，用户下次登录时需要修改密码')
    }
  } catch (error) {
    if (error === 'cancel') {
      return
    }
    console.error('重置密码失败:', error)
    ElMessage.error(error.message || '操作失败')
  }
}

// 打开批量导入对话框
const handleBatchImport = () => {
  importDialogVisible.value = true
  selectedFile.value = null
  fileList.value = []
}

// 文件选择
const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

// 下载模板
const downloadTemplate = () => {
  const headers = importType.value === 'student'
    ? 'name,student_number,class_name,gender,password\n'
    : 'name,teacher_number,subject,gender,password\n'
  
  const example = importType.value === 'student'
    ? '张三,2024001,一年级1班,男,123456\n李四,2024002,一年级1班,女,123456\n'
    : '王老师,T2024001,数学,女,123456\n李老师,T2024002,英语,男,123456\n'
  
  const content = headers + example
  const blob = new Blob(['\ufeff' + content], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${importType.value === 'student' ? '学生' : '教师'}导入模板.csv`
  link.click()
}

// 提交导入
const handleImportSubmit = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  
  try {
    importing.value = true
    
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    // 学校ID由后端从管理员信息中获取，更安全
    
    const endpoint = importType.value === 'student'
      ? '/pbl/admin/users/batch-import/students'
      : '/pbl/admin/users/batch-import/teachers'
    
    const response = await request.upload(endpoint, formData)
    
    if (response.success) {
      const data = response.data
      ElMessage.success(response.message)
      
      // 显示导入结果
      if (data.error_count > 0) {
        ElMessageBox.alert(
          `成功导入 ${data.success_count} 条，失败 ${data.error_count} 条。${data.errors && data.errors.length > 0 ? '前10条错误：\n' + data.errors.map(e => `第${e.row}行: ${e.error}`).join('\n') : ''}`,
          '导入结果',
          { type: 'warning' }
        )
      }
      
      importDialogVisible.value = false
      loadUsers()
      loadStats()
    }
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error(error.message || '导入失败')
  } finally {
    importing.value = false
  }
}

// 筛选处理
const handleFilter = () => {
  pagination.page = 1
  loadUsers()
}

// 重置筛选
const resetFilters = () => {
  filters.role = ''
  filters.search = ''
  pagination.page = 1
  loadUsers()
}

// 分页处理
const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.page = 1
  loadUsers()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadUsers()
}

// 获取角色文本
const getRoleText = (role) => {
  const texts = {
    teacher: '教师',
    student: '学生',
    school_admin: '学校管理员'
  }
  return texts[role] || role
}

// 初始化
// 获取当前管理员信息
const loadAdminInfo = async () => {
  try {
    const response = await request.get('/pbl/admin/auth/me')
    if (response.success) {
      const admin = response.data
      adminInfo.value = admin
      // 更新 localStorage
      localStorage.setItem('admin_info', JSON.stringify(admin))
    }
  } catch (error) {
    console.error('获取管理员信息失败:', error)
  }
}

onMounted(async () => {
  // 如果 adminInfo 没有 school_id，重新获取
  if (!adminInfo.value.school_id) {
    await loadAdminInfo()
  }
  loadUsers()
  loadStats()
  loadClasses()
})
</script>

<style scoped>
.school-user-management {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-form {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
