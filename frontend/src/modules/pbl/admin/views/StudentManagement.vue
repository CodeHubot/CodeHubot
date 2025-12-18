<template>
  <div class="student-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>学生管理</span>
          <div class="header-actions">
            <el-button type="primary" @click="handleAdd">
              <el-icon><Plus /></el-icon>
              添加学生
            </el-button>
            <el-button type="success" @click="handleBatchImport">
              <el-icon><Upload /></el-icon>
              批量导入
            </el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="姓名/学号">
          <el-input 
            v-model="searchForm.search" 
            placeholder="请输入姓名或学号" 
            clearable 
            style="width: 250px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="searchForm.class_id" placeholder="请选择班级" clearable style="width: 200px">
            <el-option
              v-for="cls in classes"
              :key="cls.id"
              :label="cls.name"
              :value="cls.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="students" style="width: 100%" v-loading="loading" stripe>
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="student_number" label="学号" width="150" />
        <el-table-column prop="class_name" label="班级" width="150">
          <template #default="{ row }">
            {{ row.class_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="gender" label="性别" width="80">
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
        <el-table-column prop="created_at" label="创建时间" width="180" />
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
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
      :close-on-click-modal="false"
      @close="handleDialogClose"
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="formData.name" placeholder="请输入姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学号" prop="student_number">
              <el-input 
                v-model="formData.student_number" 
                placeholder="请输入学号" 
                :disabled="dialogMode === 'edit'"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="性别" prop="gender">
              <el-select v-model="formData.gender" placeholder="请选择性别" style="width: 100%">
                <el-option label="男" value="male" />
                <el-option label="女" value="female" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="班级">
              <el-select v-model="formData.class_id" placeholder="请选择班级" style="width: 100%" clearable>
                <el-option
                  v-for="cls in classes"
                  :key="cls.id"
                  :label="cls.name"
                  :value="cls.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20" v-if="dialogMode === 'create'">
          <el-col :span="12">
            <el-form-item label="密码" prop="password">
              <el-input v-model="formData.password" type="password" placeholder="登录密码" show-password />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input v-model="formData.confirm_password" type="password" placeholder="确认密码" show-password />
            </el-form-item>
          </el-col>
        </el-row>

        <el-alert
          type="info"
          :closable="false"
          style="margin-top: 10px"
        >
          <template #default>
            <div style="font-size: 13px;">
              <strong>说明：</strong>用户名将自动生成为"学号@学校编码"的格式，无需手动输入
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
      title="批量导入学生"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="模板下载">
          <el-button type="success" size="small" @click="downloadTemplate">
            <el-icon><Download /></el-icon>
            下载学生导入模板
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
              <p><strong>导入格式：</strong>name, student_number, class_name, gender, password</p>
              <p><strong>重要提示：</strong></p>
              <ul style="margin: 5px 0; padding-left: 20px;">
                <li>用户名将自动生成为"学号@学校编码"</li>
                <li><strong>必填字段：</strong>姓名(name)、学号(student_number)、性别(gender)</li>
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Edit, Upload, Download } from '@element-plus/icons-vue'
import { 
  getUserList, 
  createUser, 
  updateUser, 
  toggleUserActive, 
  resetUserPassword,
  batchImportStudents 
} from '../api/users'
import { getClubClasses } from '../api/club'

// 搜索表单
const searchForm = reactive({
  search: '',
  class_id: null
})

// 表格数据
const students = ref([])
const classes = ref([])
const loading = ref(false)
const submitting = ref(false)
const importing = ref(false)

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 对话框
const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const dialogTitle = ref('添加学生')
const dialogMode = ref('create') // 'create' or 'edit'
const formRef = ref(null)
const uploadRef = ref(null)
const selectedFile = ref(null)
const fileList = ref([])

const formData = reactive({
  id: null,
  name: '',
  student_number: '',
  class_id: null,
  gender: '',
  password: '',
  confirm_password: ''
})

// 表单验证规则
const validatePassword = (rule, value, callback) => {
  if (dialogMode.value === 'create' && !value) {
    callback(new Error('请输入密码'))
  } else if (dialogMode.value === 'create' && value.length < 6) {
    callback(new Error('密码长度不能少于6位'))
  } else {
    callback()
  }
}

const validateConfirmPassword = (rule, value, callback) => {
  if (dialogMode.value === 'create' && value !== formData.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  student_number: [{ required: true, message: '请输入学号', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  password: [{ validator: validatePassword, trigger: 'blur' }],
  confirm_password: [{ validator: validateConfirmPassword, trigger: 'blur' }]
}

// 加载班级列表
const loadClasses = async () => {
  try {
    const response = await getClubClasses()
    if (response.success) {
      classes.value = response.data || []
    }
  } catch (error) {
    console.error('加载班级列表失败:', error)
  }
}

// 加载学生列表
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      role: 'student',
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize
    }
    
    const response = await getUserList(params)
    if (response.success) {
      students.value = response.data.items || []
      pagination.total = response.data.total || 0
    }
  } catch (error) {
    ElMessage.error('加载数据失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadData()
}

// 重置
const handleReset = () => {
  searchForm.search = ''
  searchForm.class_id = null
  handleSearch()
}

// 新增
const handleAdd = () => {
  dialogMode.value = 'create'
  dialogTitle.value = '添加学生'
  resetForm()
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row) => {
  dialogMode.value = 'edit'
  dialogTitle.value = '编辑学生'
  Object.assign(formData, {
    id: row.id,
    name: row.name,
    student_number: row.student_number,
    class_id: row.class_id,
    gender: row.gender
  })
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    id: null,
    name: '',
    student_number: '',
    class_id: null,
    gender: '',
    password: '',
    confirm_password: ''
  })
  formRef.value?.resetFields()
}

// 启用/禁用
const handleToggleActive = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要${row.is_active ? '禁用' : '启用'}学生"${row.name}"吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await toggleUserActive(row.id)
    if (response.success) {
      ElMessage.success(response.message || '操作成功')
      loadData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '操作失败')
    }
  }
}

// 重置密码
const handleResetPassword = async (row) => {
  try {
    const { value: newPassword } = await ElMessageBox.prompt(
      `请输入新密码（学生"${row.name}"）`,
      '重置密码',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /.{6,}/,
        inputErrorMessage: '密码长度不能少于6位'
      }
    )
    
    const response = await resetUserPassword(row.id, newPassword)
    if (response.success) {
      ElMessage.success('密码重置成功')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '操作失败')
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    submitting.value = true
    
    const data = {
      role: 'student',
      name: formData.name,
      student_number: formData.student_number,
      class_id: formData.class_id,
      gender: formData.gender
    }
    
    if (dialogMode.value === 'create') {
      data.password = formData.password
    }
    
    let response
    if (dialogMode.value === 'create') {
      response = await createUser(data)
    } else {
      response = await updateUser(formData.id, data)
    }
    
    if (response.success) {
      ElMessage.success(dialogMode.value === 'create' ? '创建成功' : '更新成功')
      dialogVisible.value = false
      loadData()
    }
  } catch (error) {
    if (error.errors) {
      return
    }
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 关闭对话框
const handleDialogClose = () => {
  resetForm()
}

// 批量导入
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
  const headers = 'name,student_number,class_name,gender,password\n'
  const example = '张三,2024001,一年级1班,男,123456\n李四,2024002,一年级1班,女,123456\n'
  
  const content = headers + example
  const blob = new Blob(['\ufeff' + content], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = '学生导入模板.csv'
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
    
    const response = await batchImportStudents(selectedFile.value)
    
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
      loadData()
    }
  } catch (error) {
    ElMessage.error(error.message || '导入失败')
  } finally {
    importing.value = false
  }
}

// 分页改变
const handleSizeChange = (val) => {
  pagination.pageSize = val
  pagination.page = 1
  loadData()
}

const handleCurrentChange = (val) => {
  pagination.page = val
  loadData()
}

// 初始化
onMounted(() => {
  loadClasses()
  loadData()
})
</script>

<style scoped>
.student-management {
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

.search-form {
  margin-bottom: 20px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>


