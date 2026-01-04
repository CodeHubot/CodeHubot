<template>
  <div class="channel-course-detail">
    <el-page-header @back="goBack" class="page-header">
      <template #content>
        <span class="page-title">{{ courseData.course?.title || '课程详情' }}</span>
      </template>
    </el-page-header>

    <el-card class="info-card" shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span class="card-title">学生作业提交统计</span>
          <div class="header-info">
            <el-tag>{{ courseData.course?.class_name }}</el-tag>
            <el-tag type="info" style="margin-left: 10px">{{ courseData.course?.school_name }}</el-tag>
          </div>
        </div>
      </template>

      <el-table 
        :data="courseData.students" 
        style="width: 100%"
        border
        stripe
      >
        <el-table-column prop="student_name" label="学生姓名" width="120" fixed>
          <template #default="{ row }">
            <div class="student-info">
              <span class="student-name">{{ row.student_name }}</span>
              <span class="student-number">{{ row.student_number }}</span>
            </div>
          </template>
        </el-table-column>

        <!-- 动态生成每个单元的列 -->
        <el-table-column
          v-for="unit in courseData.units"
          :key="unit.id"
          :label="unit.title"
          width="150"
          align="center"
        >
          <template #default="{ row }">
            <el-tag 
              :type="getSubmissionType(getUnitSubmissionCount(row, unit.id), unit.task_count)"
              size="large"
            >
              {{ getUnitSubmissionCount(row, unit.id) }}/{{ unit.task_count }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 总计列 -->
        <el-table-column 
          label="总计" 
          width="120" 
          align="center"
          fixed="right"
          sortable
          :sort-method="sortByCompletion"
        >
          <template #default="{ row }">
            <el-tag 
              :type="getTotalSubmissionType(row.total_submissions, row.total_tasks)"
              size="large" 
              effect="dark"
            >
              <strong>{{ row.total_submissions }}/{{ row.total_tasks }}</strong>
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="courseData.students?.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无学生数据" />
      </div>

      <!-- 统计摘要 -->
      <div v-if="courseData.students?.length > 0" class="summary-section">
        <el-divider />
        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic 
              title="学生总数" 
              :value="courseData.students.length" 
              suffix="人"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic 
              title="单元总数 / 作业总数" 
              :value="`${courseData.units?.length || 0} / ${totalTasksCount}`"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic 
              title="已提交 / 应提交" 
              :value="`${totalSubmissions} / ${totalExpectedSubmissions}`"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic 
              title="完成率" 
              :value="completionRate" 
              suffix="%"
              :precision="1"
            />
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getCourseStudentSubmissions } from '../api'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const courseData = ref({
  course: null,
  units: [],
  students: []
})

// 计算总任务数（所有单元的任务数之和）
const totalTasksCount = computed(() => {
  return courseData.value.units.reduce((sum, unit) => {
    return sum + (unit.task_count || 0)
  }, 0)
})

// 计算总提交数
const totalSubmissions = computed(() => {
  return courseData.value.students.reduce((sum, student) => {
    return sum + student.total_submissions
  }, 0)
})

// 计算应提交总数（学生数 × 任务总数）
const totalExpectedSubmissions = computed(() => {
  return courseData.value.students.length * totalTasksCount.value
})

// 计算完成率
const completionRate = computed(() => {
  if (totalExpectedSubmissions.value === 0) return 0
  return (totalSubmissions.value / totalExpectedSubmissions.value) * 100
})

function goBack() {
  router.back()
}

// 获取学生在指定单元的提交数
function getUnitSubmissionCount(student, unitId) {
  const unitSub = student.unit_submissions.find(sub => sub.unit_id === unitId)
  return unitSub ? unitSub.submission_count : 0
}

// 根据提交数量和总任务数返回标签类型
function getSubmissionType(submittedCount, totalCount) {
  if (totalCount === 0) return 'info'
  const percentage = (submittedCount / totalCount) * 100
  if (percentage === 0) return 'info'       // 0% - 灰色
  if (percentage < 50) return 'danger'      // <50% - 红色
  if (percentage < 100) return 'warning'    // 50-99% - 橙色
  return 'success'                          // 100% - 绿色
}

// 根据总提交数和总任务数返回标签类型
function getTotalSubmissionType(submittedCount, totalCount) {
  return getSubmissionType(submittedCount, totalCount)
}

// 按完成率排序
function sortByCompletion(a, b) {
  const rateA = a.total_tasks > 0 ? (a.total_submissions / a.total_tasks) : 0
  const rateB = b.total_tasks > 0 ? (b.total_submissions / b.total_tasks) : 0
  return rateA - rateB
}

async function fetchData() {
  loading.value = true
  try {
    const courseUuid = route.params.courseUuid
    const response = await getCourseStudentSubmissions(courseUuid)
    courseData.value = response.data || { course: null, units: [], students: [] }
  } catch (error) {
    console.error('获取课程数据失败:', error)
    ElMessage.error(error.message || '获取课程数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped lang="scss">
.channel-course-detail {
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
  
  .info-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .card-title {
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
      }
      
      .header-info {
        display: flex;
        align-items: center;
      }
    }
    
    .student-info {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      
      .student-name {
        font-weight: 500;
        color: #2c3e50;
        margin-bottom: 4px;
      }
      
      .student-number {
        font-size: 12px;
        color: #909399;
      }
    }
    
    .summary-section {
      margin-top: 20px;
      padding: 20px;
      background: #f5f7fa;
      border-radius: 4px;
    }
    
    .empty-state {
      padding: 40px 0;
    }
  }
}
</style>
