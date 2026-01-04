<template>
  <div class="channel-school-courses">
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ schoolInfo.school_name }} - 课程列表</span>
      </template>
    </el-page-header>

    <el-card class="content-card" shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span class="card-title">课程列表</span>
          <el-input
            v-model="searchText"
            placeholder="搜索课程名称"
            style="width: 300px"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>

      <el-table
        :data="filteredCourses"
        style="width: 100%"
      >
        <el-table-column prop="course_name" label="课程名称" min-width="200">
          <template #default="{ row }">
            <div class="course-name">
              <el-icon color="#67c23a"><Reading /></el-icon>
              <span>{{ row.course_name }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="class_name" label="班级" width="150">
          <template #default="{ row }">
            <el-tag>{{ row.class_name }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="teacher_name" label="授课教师" width="120" />
        
        <el-table-column prop="student_count" label="学生数" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="success">{{ row.student_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="start_date" label="开始时间" width="120">
          <template #default="{ row }">
            {{ formatDate(row.start_date) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="end_date" label="结束时间" width="120">
          <template #default="{ row }">
            {{ formatDate(row.end_date) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="viewCourseDetail(row)"
              :icon="View"
            >
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="filteredCourses.length === 0 && !loading" class="empty-state">
        <el-empty description="该学校暂无课程数据" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Reading, View } from '@element-plus/icons-vue'
import { getSchoolCourses, getSchoolDetail } from '../api'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const schoolInfo = ref({})
const courses = ref([])
const searchText = ref('')

const filteredCourses = computed(() => {
  if (!searchText.value) return courses.value
  return courses.value.filter(course => 
    course.course_name.toLowerCase().includes(searchText.value.toLowerCase())
  )
})

function goBack() {
  router.push({ name: 'ChannelSchools' })
}

async function fetchSchoolInfo() {
  try {
    const response = await getSchoolDetail(route.params.schoolId)
    schoolInfo.value = response.data || {}
  } catch (error) {
    console.error('获取学校信息失败:', error)
  }
}

async function fetchCourses() {
  loading.value = true
  try {
    const response = await getSchoolCourses(route.params.schoolId)
    courses.value = response.data || []
  } catch (error) {
    console.error('获取课程列表失败:', error)
    ElMessage.error(error.message || '获取课程列表失败')
  } finally {
    loading.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return dateStr.split('T')[0]
}

function getStatusType(status) {
  const typeMap = {
    'draft': 'info',
    'published': 'success',
    'archived': 'warning',
    'not_started': 'info',
    'in_progress': 'success',
    'completed': 'warning'
  }
  return typeMap[status] || 'info'
}

function getStatusText(status) {
  const textMap = {
    'draft': '草稿',
    'published': '已发布',
    'archived': '已归档',
    'not_started': '未开始',
    'in_progress': '进行中',
    'completed': '已完成'
  }
  return textMap[status] || status
}

function viewCourseDetail(course) {
  router.push({
    name: 'ChannelCourseDetail',
    params: { courseUuid: course.uuid }
  })
}

onMounted(() => {
  fetchSchoolInfo()
  fetchCourses()
})
</script>

<style scoped lang="scss">
.channel-school-courses {
  .page-header {
    margin-bottom: 20px;
    background: white;
    padding: 16px 20px;
    border-radius: 4px;
    
    .page-title {
      font-size: 18px;
      font-weight: 600;
      color: #2c3e50;
    }
  }
  
  .content-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .card-title {
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
      }
    }
    
    .course-name {
      display: flex;
      align-items: center;
      gap: 8px;
      
      span {
        font-weight: 500;
      }
    }
    
    .empty-state {
      padding: 40px 0;
    }
  }
}
</style>
