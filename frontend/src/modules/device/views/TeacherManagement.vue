<template>
  <div class="teacher-management">
    <div class="page-header">
      <h1>教师管理</h1>
      <div>
        <el-button type="warning" @click="showBatchImport">
          <el-icon><Upload /></el-icon>
          批量导入
        </el-button>
        <el-button type="success" @click="showAddIndividualDialog">
          <el-icon><UserFilled /></el-icon>
          从独立用户添加
        </el-button>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          创建教师
        </el-button>
      </div>
    </div>

    <!-- 搜索 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="姓名、用户名或工号"
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

    <!-- 教师列表 -->
    <el-card class="table-card">
      <el-table :data="teachers" v-loading="loading" stripe>
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="real_name" label="姓名" width="120" />
        <el-table-column prop="teacher_number" label="工号" width="120" />
        <el-table-column prop="subject" label="学科" width="100" />
        <el-table-column label="任教课程" width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <template v-if="row.course_names">
              <el-tag
                v-for="(courseName, index) in row.course_names.split(', ')"
                :key="index"
                size="small"
                type="info"
                effect="plain"
                style="margin: 2px;"
              >
                {{ courseName }}
              </el-tag>
            </template>
            <span v-else style="color: #999;">未分配</span>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="phone" label="电话" width="130" />
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
          @current-change="loadTeachers"
          @size-change="loadTeachers"
        />
      </div>
    </el-card>

    <!-- 创建教师对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建教师"
      width="500px"
    >
      <el-form
        ref="teacherFormRef"
        :model="teacherForm"
        :rules="teacherRules"
        label-width="100px"
        autocomplete="off"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="teacherForm.username" placeholder="用户名" autocomplete="off" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="teacherForm.password" type="password" placeholder="密码" autocomplete="new-password" />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="teacherForm.real_name" placeholder="真实姓名" autocomplete="off" />
        </el-form-item>
        <el-form-item label="工号" prop="teacher_number">
          <el-input v-model="teacherForm.teacher_number" placeholder="工号" autocomplete="off" />
        </el-form-item>
        <el-form-item label="学科" prop="subject">
          <el-input v-model="teacherForm.subject" placeholder="学科" autocomplete="off" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="teacherForm.email" placeholder="邮箱" autocomplete="off" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="teacherForm.phone" placeholder="电话" autocomplete="off" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 从独立用户添加对话框 -->
    <el-dialog
      v-model="addIndividualDialogVisible"
      title="从独立用户添加教师"
      width="800px"
    >
      <el-form :inline="true">
        <el-form-item label="搜索">
          <el-input
            v-model="individualSearchKeyword"
            placeholder="用户名或姓名"
            @change="searchIndividualUsers"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchIndividualUsers">搜索</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="individualUsers" v-loading="individualLoading">
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="real_name" label="姓名" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="selectIndividualUser(row)">
              选择
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 分配角色对话框 -->
    <el-dialog
      v-model="assignDialogVisible"
      title="分配教师角色"
      width="400px"
    >
      <el-form
        ref="assignFormRef"
        :model="assignForm"
        :rules="assignRules"
        label-width="100px"
        autocomplete="off"
      >
        <el-form-item label="用户" >
          <el-input :value="selectedUser?.username" disabled autocomplete="off" />
        </el-form-item>
        <el-form-item label="工号" prop="teacher_number">
          <el-input v-model="assignForm.teacher_number" placeholder="工号" autocomplete="off" />
        </el-form-item>
        <el-form-item label="学科" prop="subject">
          <el-input v-model="assignForm.subject" placeholder="学科" autocomplete="off" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="assignDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAssign" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量导入对话框 -->
    <BatchImport 
      v-model="batchImportVisible" 
      type="teacher"
      @success="handleBatchImportSuccess"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, UserFilled, Upload } from '@element-plus/icons-vue'
import { getTeachers, createTeacher, deleteUser, searchIndividualUsers as searchIndividualUsersAPI, assignRole } from '@/api/userManagement'
import { formatDate } from '@/utils/format'
import BatchImport from '../components/BatchImport.vue'

const loading = ref(false)
const submitting = ref(false)
const teachers = ref([])
const createDialogVisible = ref(false)
const addIndividualDialogVisible = ref(false)
const assignDialogVisible = ref(false)
const batchImportVisible = ref(false)
const teacherFormRef = ref(null)
const assignFormRef = ref(null)
const individualLoading = ref(false)
const individualUsers = ref([])
const individualSearchKeyword = ref('')
const selectedUser = ref(null)

const searchForm = reactive({
  keyword: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const teacherForm = reactive({
  username: '',
  password: '',
  real_name: '',
  teacher_number: '',
  subject: '',
  email: '',
  phone: ''
})

const assignForm = reactive({
  teacher_number: '',
  subject: ''
})

const teacherRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  teacher_number: [{ required: true, message: '请输入工号', trigger: 'blur' }]
}

const assignRules = {
  teacher_number: [{ required: true, message: '请输入工号', trigger: 'blur' }]
}

const loadTeachers = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      keyword: searchForm.keyword
    }
    const response = await getTeachers(params)
    if (response.data) {
      teachers.value = response.data.teachers || []
      pagination.total = response.data.total || 0
    }
  } catch (error) {
    ElMessage.error('加载教师列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadTeachers()
}

const handleReset = () => {
  searchForm.keyword = ''
  handleSearch()
}

const showCreateDialog = () => {
  Object.assign(teacherForm, {
    username: '',
    password: '',
    real_name: '',
    teacher_number: '',
    subject: '',
    email: '',
    phone: ''
  })
  createDialogVisible.value = true
}

const handleCreate = async () => {
  if (!teacherFormRef.value) return
  
  await teacherFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      await createTeacher(teacherForm)
      ElMessage.success('教师创建成功')
      createDialogVisible.value = false
      loadTeachers()
    } catch (error) {
      ElMessage.error('创建教师失败: ' + (error.response?.data?.message || error.message))
    } finally {
      submitting.value = false
    }
  })
}

const showAddIndividualDialog = () => {
  individualSearchKeyword.value = ''
  individualUsers.value = []
  addIndividualDialogVisible.value = true
}

const searchIndividualUsers = async () => {
  individualLoading.value = true
  try {
    const response = await searchIndividualUsersAPI({
      keyword: individualSearchKeyword.value,
      page: 1,
      page_size: 20
    })
    if (response.data) {
      individualUsers.value = response.data.users || []
    }
  } catch (error) {
    ElMessage.error('搜索用户失败')
  } finally {
    individualLoading.value = false
  }
}

const selectIndividualUser = (user) => {
  selectedUser.value = user
  addIndividualDialogVisible.value = false
  assignForm.teacher_number = ''
  assignForm.subject = ''
  assignDialogVisible.value = true
}

const handleAssign = async () => {
  if (!assignFormRef.value) return
  
  await assignFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      await assignRole(selectedUser.value.uuid, {
        new_role: 'teacher',
        teacher_number: assignForm.teacher_number,
        subject: assignForm.subject
      })
      ElMessage.success('角色分配成功')
      assignDialogVisible.value = false
      loadTeachers()
    } catch (error) {
      ElMessage.error('分配角色失败: ' + (error.response?.data?.message || error.message))
    } finally {
      submitting.value = false
    }
  })
}

const handleDelete = async (teacher) => {
  try {
    await ElMessageBox.confirm(`确定要删除教师 "${teacher.real_name}" 吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deleteUser(teacher.uuid)
    ElMessage.success('教师删除成功')
    loadTeachers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除教师失败')
    }
  }
}

// 批量导入相关
const showBatchImport = () => {
  batchImportVisible.value = true
}

const handleBatchImportSuccess = () => {
  ElMessage.success('批量导入成功')
  loadTeachers()
}

onMounted(() => {
  loadTeachers()
})
</script>

<style scoped>
.teacher-management {
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

