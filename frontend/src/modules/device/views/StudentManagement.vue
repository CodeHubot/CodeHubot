<template>
  <div class="student-management">
    <div class="page-header">
      <h1>学生管理</h1>
      <div>
        <el-button type="warning" @click="showBatchImport">
          <el-icon><Upload /></el-icon>
          批量导入
        </el-button>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          创建学生
        </el-button>
      </div>
    </div>

    <!-- 搜索 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="姓名、用户名或学号"
            clearable
            @clear="handleSearch"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 学生列表 -->
    <el-card class="table-card">
      <el-table :data="students" v-loading="loading" stripe>
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="real_name" label="姓名" width="120" />
        <el-table-column label="性别" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.gender === 'male'" type="primary" size="small">男</el-tag>
            <el-tag v-else-if="row.gender === 'female'" type="danger" size="small">女</el-tag>
            <el-tag v-else type="info" size="small">其他</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="student_number" label="学号" width="150" />
        <el-table-column label="已选课程" width="250">
          <template #default="{ row }">
            <div v-if="row.course_names" style="display: flex; flex-wrap: wrap; gap: 4px;">
              <el-tag 
                v-for="(name, index) in row.course_names.split(', ')" 
                :key="index" 
                type="success" 
                size="small"
              >
                {{ name }}
              </el-tag>
            </div>
            <span v-else style="color: #999;">未选课</span>
          </template>
        </el-table-column>
        <el-table-column label="总学分" width="100">
          <template #default="{ row }">
            <el-tag type="warning" size="small">{{ row.total_credits || 0 }} 学分</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadStudents"
          @size-change="loadStudents"
        />
      </div>
    </el-card>

    <!-- 创建学生对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建学生"
      width="500px"
    >
      <el-form
        ref="studentFormRef"
        :model="studentForm"
        :rules="studentRules"
        label-width="100px"
        autocomplete="off"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="studentForm.username" placeholder="用户名" autocomplete="off" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="studentForm.password" type="password" placeholder="密码" autocomplete="new-password" />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="studentForm.real_name" placeholder="真实姓名" autocomplete="off" />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-radio-group v-model="studentForm.gender">
            <el-radio value="male">男</el-radio>
            <el-radio value="female">女</el-radio>
            <el-radio value="other">其他</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="学号" prop="student_number">
          <el-input v-model="studentForm.student_number" placeholder="学号" autocomplete="off" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量导入对话框 -->
    <BatchImport 
      v-model="batchImportVisible" 
      type="student"
      @success="handleBatchImportSuccess"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload } from '@element-plus/icons-vue'
import { getStudents, createStudent, deleteUser } from '@/api/userManagement'
import { formatDate } from '@/utils/format'
import BatchImport from '../components/BatchImport.vue'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()

const loading = ref(false)
const submitting = ref(false)
const students = ref([])
const createDialogVisible = ref(false)
const batchImportVisible = ref(false)
const studentFormRef = ref(null)

const searchForm = reactive({
  keyword: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const studentForm = reactive({
  username: '',
  password: '',
  real_name: '',
  gender: 'male',
  student_number: ''
})

const studentRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码（至少6位）', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  student_number: [{ required: true, message: '请输入学号', trigger: 'blur' }]
}

const loadStudents = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      keyword: searchForm.keyword
    }
    const response = await getStudents(params)
    if (response.data) {
      students.value = response.data.students || []
      pagination.total = response.data.total || 0
    }
  } catch (error) {
    ElMessage.error('加载学生列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadStudents()
}

const handleReset = () => {
  searchForm.keyword = ''
  handleSearch()
}

const showCreateDialog = async () => {
  Object.assign(studentForm, {
    username: '',
    password: '',
    real_name: '',
    gender: 'male',
    student_number: ''
  })
  createDialogVisible.value = true
}

const handleCreate = async () => {
  if (!studentFormRef.value) return
  
  await studentFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      await createStudent(studentForm)
      ElMessage.success('学生创建成功')
      createDialogVisible.value = false
      loadStudents()
    } catch (error) {
      ElMessage.error('创建学生失败: ' + (error.response?.data?.message || error.message))
    } finally {
      submitting.value = false
    }
  })
}

const handleDelete = async (student) => {
  try {
    await ElMessageBox.confirm(`确定要删除学生 "${student.real_name}" 吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deleteUser(student.uuid)
    ElMessage.success('学生删除成功')
    loadStudents()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除学生失败')
    }
  }
}

// 批量导入相关
const showBatchImport = () => {
  batchImportVisible.value = true
}

const handleBatchImportSuccess = () => {
  ElMessage.success('批量导入成功')
  loadStudents()
}

onMounted(() => {
  loadStudents()
})
</script>

<style scoped>
.student-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 24px;
  margin: 0;
}

.search-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>

