<template>
  <div class="course-student-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" type="text" size="large">
          <el-icon><ArrowLeft /></el-icon> 返回课程列表
        </el-button>
        <h2>{{ courseName }} - 学生管理</h2>
      </div>
      <div class="header-actions">
        <el-button type="success" @click="showAddStudentDialog">
          <el-icon><Plus /></el-icon> 添加学生
        </el-button>
        <el-button type="primary" @click="showBatchImportDialog">
          <el-icon><Upload /></el-icon> 批量导入
        </el-button>
        <el-button type="warning" @click="showGroupManagement">
          <el-icon><Grid /></el-icon> 学生分组
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card>
        <div class="stat-item">
          <el-icon size="32" color="#409EFF"><UserFilled /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ students.length }}</div>
            <div class="stat-label">学生总数</div>
          </div>
        </div>
      </el-card>
      <el-card>
        <div class="stat-item">
          <el-icon size="32" color="#67C23A"><Grid /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ groupCount }}</div>
            <div class="stat-label">分组数量</div>
          </div>
        </div>
      </el-card>
      <el-card>
        <div class="stat-item">
          <el-icon size="32" color="#E6A23C"><Warning /></el-icon>
          <div class="stat-info">
            <div class="stat-value">{{ ungroupedCount }}</div>
            <div class="stat-label">未分组学生</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 学生列表 -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>学生列表</span>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索学生姓名或学号"
            style="width: 300px"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>

      <el-table
        :data="filteredStudents"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="student_number" label="学号" width="150" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column label="性别" width="80">
          <template #default="{ row }">
            {{ row.gender === 'male' ? '男' : row.gender === 'female' ? '女' : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="所属小组" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.group_name" type="success">{{ row.group_name }}</el-tag>
            <span v-else style="color: #999;">未分组</span>
          </template>
        </el-table-column>
        <el-table-column label="是否组长" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_leader" type="warning" size="small">组长</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="joined_at" label="加入时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.joined_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" link @click="removeStudent(row)">
              <el-icon><Delete /></el-icon> 移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加学生对话框 -->
    <el-dialog
      v-model="addStudentDialogVisible"
      title="添加学生到课程"
      width="800px"
    >
      <el-input
        v-model="studentSearchKeyword"
        placeholder="搜索学生姓名或学号"
        clearable
        @input="searchSchoolStudents"
        style="margin-bottom: 16px"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <el-table
        ref="studentTableRef"
        :data="availableStudents"
        v-loading="availableStudentsLoading"
        @selection-change="handleStudentSelectionChange"
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="student_number" label="学号" width="150" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column label="性别" width="80">
          <template #default="{ row }">
            {{ row.gender === 'male' ? '男' : row.gender === 'female' ? '女' : '-' }}
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="addStudentDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="confirmAddStudents"
          :disabled="selectedStudents.length === 0"
        >
          确定添加（已选{{ selectedStudents.length }}个）
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量导入组件 -->
    <BatchImport
      v-if="batchImportVisible"
      v-model="batchImportVisible"
      :api-type="'course-students'"
      :title="`批量导入学生到课程：${courseName}`"
      :template-url="`/courses/${courseUuid}/students/template`"
      :import-url="`/courses/${courseUuid}/students/batch-import`"
      @success="loadStudents"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, Plus, Upload, Grid, Search, Delete,
  UserFilled, Warning
} from '@element-plus/icons-vue'
import { getCourseStudents, addStudentToCourse, removeStudentFromCourse } from '@/api/courses'
import { getUsers } from '@/api/userManagement'
import BatchImport from '@/components/BatchImport.vue'
import { useUserStore } from '@/store/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const courseUuid = route.params.courseUuid
const courseName = ref(route.query.name || '课程')

// 数据
const loading = ref(false)
const students = ref([])
const searchKeyword = ref('')
const addStudentDialogVisible = ref(false)
const batchImportVisible = ref(false)
const studentSearchKeyword = ref('')
const availableStudents = ref([])
const availableStudentsLoading = ref(false)
const selectedStudents = ref([])
const studentTableRef = ref(null)

// 计算属性
const filteredStudents = computed(() => {
  if (!searchKeyword.value) return students.value
  
  const keyword = searchKeyword.value.toLowerCase()
  return students.value.filter(student =>
    student.name?.toLowerCase().includes(keyword) ||
    student.student_number?.toLowerCase().includes(keyword)
  )
})

const groupCount = computed(() => {
  const groups = new Set(students.value.filter(s => s.group_name).map(s => s.group_name))
  return groups.size
})

const ungroupedCount = computed(() => {
  return students.value.filter(s => !s.group_name).length
})

// 返回上一页
const goBack = () => {
  router.back()
}

// 加载学生列表
const loadStudents = async () => {
  loading.value = true
  try {
    const data = await getCourseStudents(courseUuid, {
      page: 1,
      page_size: 1000
    })
    
    const responseData = data.data || data
    students.value = responseData.students || []
  } catch (error) {
    console.error('加载学生列表失败:', error)
    ElMessage.error('加载学生列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  // 由computed自动处理
}

// 显示添加学生对话框
const showAddStudentDialog = () => {
  addStudentDialogVisible.value = true
  searchSchoolStudents()
}

// 搜索学校学生（排除已在课程中的）
const searchSchoolStudents = async () => {
  availableStudentsLoading.value = true
  try {
    const data = await getUsers({
      role: 'student',
      school_id: userStore.userInfo.school_id,
      keyword: studentSearchKeyword.value || undefined,
      page: 1,
      page_size: 100
    })
    
    const responseData = data.data || data
    const allStudents = responseData.users || []
    
    // 过滤掉已在课程中的学生
    const currentStudentIds = students.value.map(s => s.id)
    availableStudents.value = allStudents.filter(s => !currentStudentIds.includes(s.id))
  } catch (error) {
    console.error('加载学生列表失败:', error)
    ElMessage.error('加载学生列表失败')
  } finally {
    availableStudentsLoading.value = false
  }
}

// 学生选择变化
const handleStudentSelectionChange = (selection) => {
  selectedStudents.value = selection
}

// 确认添加学生
const confirmAddStudents = async () => {
  try {
    availableStudentsLoading.value = true
    
    const studentIds = selectedStudents.value.map(s => s.id)
    
    // 批量添加
    for (const studentId of studentIds) {
      await addStudentToCourse(courseUuid, { student_id: studentId })
    }
    
    ElMessage.success(`成功添加 ${studentIds.length} 名学生`)
    addStudentDialogVisible.value = false
    loadStudents()
    
    // 清空选择
    studentTableRef.value?.clearSelection()
  } catch (error) {
    console.error('添加学生失败:', error)
    ElMessage.error(error.message || '添加学生失败')
  } finally {
    availableStudentsLoading.value = false
  }
}

// 移除学生
const removeStudent = async (student) => {
  try {
    await ElMessageBox.confirm(
      `确定要将学生"${student.name}"从课程中移除吗？`,
      '确认移除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await removeStudentFromCourse(courseUuid, student.id)
    ElMessage.success('学生已移除')
    loadStudents()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('移除学生失败:', error)
      ElMessage.error(error.message || '移除学生失败')
    }
  }
}

// 显示批量导入对话框
const showBatchImportDialog = () => {
  batchImportVisible.value = true
}

// 显示分组管理
const showGroupManagement = () => {
  router.push({
    path: `/courses/${courseUuid}/groups`,
    query: { name: courseName.value }
  })
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 页面加载
onMounted(() => {
  loadStudents()
})
</script>

<style scoped>
.course-student-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.table-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>

