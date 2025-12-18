<template>
  <div class="class-courses-container">
    <!-- 返回按钮 -->
    <div class="page-header">
      <el-button @click="goBack" text>
        <el-icon><ArrowLeft /></el-icon>
        返回班级详情
      </el-button>
    </div>

    <!-- 页面标题和操作 -->
    <el-card shadow="never" class="header-card">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">课程管理</h1>
          <p class="page-subtitle">{{ className }}</p>
        </div>
        <div class="header-right">
          <el-button type="primary" size="large" @click="createCourse">
            <el-icon><Plus /></el-icon>
            创建课程
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 统计 -->
    <el-card shadow="never" class="stats-card">
      <el-statistic title="课程总数" :value="courses.length" />
    </el-card>

    <!-- 课程列表 -->
    <el-card shadow="never" class="table-card">
      <el-table 
        :data="courses" 
        v-loading="loading" 
        stripe
        border
        style="width: 100%"
      >
        <el-table-column prop="title" label="课程名称" min-width="250" show-overflow-tooltip />
        <el-table-column prop="description" label="课程描述" min-width="300" show-overflow-tooltip />
        <el-table-column label="难度" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getDifficultyTagType(row.difficulty)" size="default">
              {{ getDifficultyName(row.difficulty) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="选课人数" width="130" align="center">
          <template #default="{ row }">
            <el-tag size="large">{{ row.enrolled_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewCourseMembers(row)">
              <el-icon><User /></el-icon>
              成员管理
            </el-button>
            <el-button link type="primary" @click="viewCourseDetail(row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty 
        v-if="!loading && courses.length === 0" 
        description="暂无课程"
        style="padding: 60px 0"
      >
        <el-button type="primary" @click="createCourse">创建第一个课程</el-button>
      </el-empty>
    </el-card>

    <!-- 课程成员管理对话框 -->
    <el-dialog 
      v-model="courseMembersDialogVisible" 
      :title="`课程成员管理 - ${currentCourseName}`"
      width="900px"
      :close-on-click-modal="false"
    >
      <div class="course-members-header">
        <el-input
          v-model="courseMemberSearchKeyword"
          placeholder="搜索成员"
          style="width: 300px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="showAddCourseMemberDialog">
          <el-icon><Plus /></el-icon>
          添加成员
        </el-button>
      </div>
      
      <el-table :data="filteredCourseMembers" v-loading="courseMembersLoading" style="margin-top: 16px">
        <el-table-column prop="student_name" label="姓名" width="120" />
        <el-table-column prop="student_number" label="学号" width="150" />
        <el-table-column prop="enrolled_at" label="选课时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.enrolled_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="学习进度" width="150" align="center">
          <template #default="{ row }">
            <el-progress 
              :percentage="row.progress || 0" 
              :stroke-width="6"
              :show-text="true"
            />
          </template>
        </el-table-column>
        <el-table-column prop="final_score" label="最终成绩" width="100" align="center">
          <template #default="{ row }">
            {{ row.final_score !== null ? row.final_score : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="danger" @click="removeCourseMemberAction(row)">
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty 
        v-if="!courseMembersLoading && filteredCourseMembers.length === 0" 
        description="暂无成员"
      />
    </el-dialog>

    <!-- 添加课程成员对话框 -->
    <el-dialog 
      v-model="addCourseMemberDialogVisible" 
      title="添加课程成员" 
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="学生ID" required>
          <el-input
            v-model="courseMemberIdsText"
            type="textarea"
            :rows="8"
            placeholder="请输入学生ID，每行一个"
          />
          <div class="form-tip">
            提示：每行输入一个学生ID，添加后学生将选上该课程
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="addCourseMemberDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAddCourseMembers" :loading="addingCourseMembers">
          添加
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, Plus, User, View, Search
} from '@element-plus/icons-vue'
import { getClubClassDetail } from '@pbl/admin/api/club'
import request from '@/utils/request'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const courses = ref([])
const className = ref('')
const classId = ref(null)

// 课程成员管理
const courseMembersDialogVisible = ref(false)
const courseMembersLoading = ref(false)
const courseMembers = ref([])
const courseMemberSearchKeyword = ref('')
const currentCourseId = ref(null)
const currentCourseName = ref('')
const addCourseMemberDialogVisible = ref(false)
const courseMemberIdsText = ref('')
const addingCourseMembers = ref(false)

// 计算属性
const filteredCourseMembers = computed(() => {
  if (!courseMemberSearchKeyword.value) return courseMembers.value
  const keyword = courseMemberSearchKeyword.value.toLowerCase()
  return courseMembers.value.filter(m => 
    m.student_name.toLowerCase().includes(keyword) || 
    m.student_number.includes(keyword)
  )
})

// 加载班级课程列表
const loadClassCourses = async () => {
  loading.value = true
  try {
    const res = await getClubClassDetail(route.params.uuid)
    className.value = res.data.data.name
    classId.value = res.data.data.id
    courses.value = res.data.data.courses || []
  } catch (error) {
    ElMessage.error(error.message || '加载课程列表失败')
  } finally {
    loading.value = false
  }
}

// 查看课程成员
const viewCourseMembers = async (course) => {
  currentCourseId.value = course.id
  currentCourseName.value = course.title
  courseMembersLoading.value = true
  courseMembersDialogVisible.value = true
  
  try {
    const response = await request.get(`/pbl/admin/enrollments/course/${course.id}/students`)
    courseMembers.value = response.data || []
  } catch (error) {
    console.error('加载课程成员失败:', error)
  } finally {
    courseMembersLoading.value = false
  }
}

// 查看课程详情
const viewCourseDetail = (course) => {
  router.push(`/admin/courses/${course.id}`)
}

// 显示添加课程成员对话框
const showAddCourseMemberDialog = () => {
  courseMemberIdsText.value = ''
  addCourseMemberDialogVisible.value = true
}

// 提交添加课程成员
const submitAddCourseMembers = async () => {
  const ids = courseMemberIdsText.value
    .split('\n')
    .map(id => parseInt(id.trim()))
    .filter(id => !isNaN(id))
  
  if (ids.length === 0) {
    ElMessage.warning('请输入有效的学生ID')
    return
  }
  
  addingCourseMembers.value = true
  try {
    const response = await request.post(
      `/api/pbl/admin/enrollments/course/${currentCourseId.value}/batch-enroll`,
      { student_ids: ids }
    )
    
    const enrolledCount = response.data.enrolled_count || 0
    ElMessage.success(`成功为 ${enrolledCount} 名学生选课`)
    addCourseMemberDialogVisible.value = false
    // 刷新课程成员列表
    viewCourseMembers({ id: currentCourseId.value, title: currentCourseName.value })
    // 刷新班级课程列表（更新选课人数）
    loadClassCourses()
  } catch (error) {
    console.error('添加成员失败:', error)
  } finally {
    addingCourseMembers.value = false
  }
}

// 移除课程成员
const removeCourseMemberAction = async (member) => {
  try {
    await ElMessageBox.confirm(
      `确定要移除成员"${member.student_name}"吗？该学生将不再能访问此课程。`,
      '确认移除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    ElMessage.warning('移除课程成员功能需要后端API支持，请联系开发人员添加')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '移除失败')
    }
  }
}

// 创建课程
const createCourse = () => {
  router.push(`/pbl/admin/classes/${route.params.uuid}/create-course`)
}

// 工具方法
const getDifficultyName = (difficulty) => {
  const map = {
    beginner: '入门',
    intermediate: '中级',
    advanced: '高级'
  }
  return map[difficulty] || difficulty
}

const getDifficultyTagType = (difficulty) => {
  const map = {
    beginner: 'success',
    intermediate: 'warning',
    advanced: 'danger'
  }
  return map[difficulty] || 'info'
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

const goBack = () => {
  router.push(`/pbl/admin/classes/${route.params.uuid}`)
}

onMounted(() => {
  loadClassCourses()
})
</script>

<style scoped lang="scss">
.class-courses-container {
  padding: 24px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 24px;
}

.header-card {
  margin-bottom: 24px;
  border-radius: 12px;
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    
    .header-left {
      .page-title {
        margin: 0 0 8px 0;
        font-size: 24px;
        font-weight: 600;
        color: #303133;
      }
      
      .page-subtitle {
        margin: 0;
        font-size: 14px;
        color: #909399;
      }
    }
  }
}

.stats-card {
  margin-bottom: 24px;
  border-radius: 12px;
  
  :deep(.el-statistic) {
    .el-statistic__head {
      font-size: 14px;
      color: #909399;
    }
    
    .el-statistic__content {
      font-size: 28px;
      font-weight: 600;
      color: #409eff;
    }
  }
}

.table-card {
  border-radius: 12px;
}

.course-members-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.form-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}
</style>
