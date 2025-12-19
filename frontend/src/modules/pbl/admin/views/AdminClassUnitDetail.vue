<template>
  <div class="unit-detail-container">
    <!-- 返回按钮 -->
    <div class="page-header">
      <el-button @click="goBack" text>
        <el-icon><ArrowLeft /></el-icon>
        返回进度列表
      </el-button>
    </div>

    <!-- 页面标题 -->
    <el-card shadow="never" class="header-card" v-loading="loadingDetail">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">{{ unitDetail?.unit.title || '加载中...' }}</h1>
          <p class="page-subtitle">{{ className }}</p>
        </div>
      </div>
    </el-card>

    <!-- 单元信息 -->
    <el-card shadow="never" class="info-card" v-loading="loadingDetail">
      <template #header>
        <div class="card-header">
          <span>单元信息</span>
        </div>
      </template>
      
      <el-descriptions :column="2" border class="unit-info">
        <el-descriptions-item label="单元名称">
          {{ unitDetail?.unit.title || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="任务数量">
          {{ unitDetail?.tasks.length || 0 }} 个
        </el-descriptions-item>
        <el-descriptions-item label="单元顺序">
          第 {{ unitDetail?.unit.order }} 单元
        </el-descriptions-item>
        <el-descriptions-item label="学生人数">
          {{ unitDetail?.students.length || 0 }} 人
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ unitDetail?.unit.description || '暂无描述' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 任务列表 -->
    <el-card shadow="never" class="tasks-card" v-loading="loadingDetail">
      <template #header>
        <div class="card-header">
          <span>任务列表</span>
        </div>
      </template>
      
      <div class="task-tags">
        <el-tag 
          v-for="task in unitDetail?.tasks" 
          :key="task.id"
          :type="task.is_required ? 'danger' : ''"
          size="large"
          style="margin-right: 8px; margin-bottom: 8px"
        >
          {{ task.title }}
          <span v-if="task.is_required"> （必做）</span>
        </el-tag>
        <el-empty 
          v-if="!unitDetail?.tasks || unitDetail.tasks.length === 0" 
          description="暂无任务"
          :image-size="60"
        />
      </div>
    </el-card>

    <!-- 学生完成情况 -->
    <el-card shadow="never" class="students-card" v-loading="loadingDetail">
      <template #header>
        <div class="card-header">
          <span>学生完成情况</span>
        </div>
      </template>
      
      <!-- 搜索 -->
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索学生（姓名或学号）"
          style="width: 300px"
          clearable
          @change="loadUnitDetail"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <span class="search-tip">
          找到 {{ filteredStudents.length }} 名学生
        </span>
      </div>

      <el-table 
        :data="filteredStudents" 
        border
        stripe
        style="width: 100%"
        :max-height="600"
        :default-sort="{ prop: 'student_number', order: 'ascending' }"
      >
        <el-table-column 
          type="index" 
          label="序号" 
          width="80" 
          align="center"
          fixed="left"
        />
        <el-table-column 
          prop="student_number" 
          label="学号" 
          width="150" 
          sortable
          fixed="left"
        />
        <el-table-column 
          prop="name" 
          label="姓名" 
          width="120" 
          sortable
          fixed="left"
        />
        <el-table-column 
          label="进度" 
          width="120" 
          align="center"
          sortable
          :sort-method="sortByProgress"
        >
          <template #default="{ row }">
            <el-tag :type="getProgressTagType(row.completion_rate)">
              {{ row.completed_tasks }}/{{ row.total_tasks }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="任务完成详情" min-width="400">
          <template #default="{ row }">
            <div class="task-progress-tags">
              <template v-if="getSubmittedTasks(row.task_progress).length > 0">
                <el-tooltip 
                  v-for="tp in getSubmittedTasks(row.task_progress)" 
                  :key="tp.task_id"
                  :content="getTaskTooltip(tp)"
                  placement="top"
                >
                  <el-tag 
                    :type="getTaskStatusType(tp.status)"
                    size="small"
                    style="margin-right: 4px; margin-bottom: 4px"
                  >
                    {{ tp.task_title.substring(0, 10) }}{{ tp.task_title.length > 10 ? '...' : '' }}
                  </el-tag>
                </el-tooltip>
              </template>
              <span v-else class="no-submission">暂无提交</span>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-empty 
        v-if="!loadingDetail && filteredStudents.length === 0" 
        description="暂无学生数据"
        style="padding: 60px 0"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Search } from '@element-plus/icons-vue'
import { getClubClassDetail } from '@pbl/admin/api/club'
import request from '@/utils/request'

const route = useRoute()
const router = useRouter()

const loadingDetail = ref(false)
const className = ref('')
const unitDetail = ref(null)
const searchKeyword = ref('')

// 计算属性 - 过滤后的学生列表
const filteredStudents = computed(() => {
  if (!unitDetail.value || !unitDetail.value.students) {
    return []
  }
  return unitDetail.value.students
})

// 加载班级名称
const loadClassName = async () => {
  try {
    const res = await getClubClassDetail(route.params.classUuid)
    className.value = res.data.data.name
  } catch (error) {
    console.error('加载班级名称失败:', error)
  }
}

// 加载单元详情
const loadUnitDetail = async () => {
  loadingDetail.value = true
  try {
    const res = await request({
      url: `/admin/club/classes/${route.params.classUuid}/progress/units/${route.params.unitId}`,
      method: 'get',
      params: {
        search: searchKeyword.value || undefined
      }
    })
    unitDetail.value = res.data.data
  } catch (error) {
    ElMessage.error(error.message || '加载单元详情失败')
  } finally {
    loadingDetail.value = false
  }
}

// 工具方法
const getProgressTagType = (rate) => {
  if (rate === 100) return 'success'
  if (rate >= 50) return 'warning'
  if (rate > 0) return 'info'
  return 'info'
}

// 自定义进度排序方法
const sortByProgress = (a, b) => {
  return a.completion_rate - b.completion_rate
}

const getTaskStatusType = (status) => {
  const map = {
    'not_started': 'info',
    'pending': 'info',
    'in-progress': 'warning',
    'review': '',
    'completed': 'success'
  }
  return map[status] || 'info'
}

const getTaskTooltip = (tp) => {
  const statusMap = {
    'not_started': '未开始',
    'pending': '未开始',
    'in-progress': '进行中',
    'review': '待批改',
    'completed': '已完成'
  }
  const statusText = statusMap[tp.status] || tp.status
  const scoreText = tp.score ? ` - ${tp.score}分` : ''
  return `${tp.task_title}: ${statusText}${scoreText}`
}

// 过滤出已提交的任务（is_completed为true的任务）
const getSubmittedTasks = (taskProgress) => {
  if (!taskProgress) return []
  return taskProgress.filter(tp => tp.is_completed === true)
}

const goBack = () => {
  router.push(`/pbl/admin/classes/${route.params.classUuid}/progress`)
}

onMounted(async () => {
  await loadClassName()
  await loadUnitDetail()
})
</script>

<style scoped lang="scss">
.unit-detail-container {
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

.info-card,
.tasks-card,
.students-card {
  margin-bottom: 24px;
  border-radius: 12px;
  
  .card-header {
    font-size: 16px;
    font-weight: 600;
  }
}

.unit-info {
  margin-bottom: 0;
}

.task-tags {
  padding: 12px 0;
  min-height: 60px;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  
  .search-tip {
    font-size: 14px;
    color: #909399;
  }
}

.task-progress-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  
  .no-submission {
    font-size: 14px;
    color: #c0c4cc;
    font-style: italic;
  }
}
</style>
