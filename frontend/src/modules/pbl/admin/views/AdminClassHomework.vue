<template>
  <div class="class-homework-container">
    <!-- 返回按钮 -->
    <div class="page-header">
      <el-button @click="goBack" text>
        <el-icon><ArrowLeft /></el-icon>
        返回班级详情
      </el-button>
    </div>

    <!-- 页面标题 -->
    <el-card shadow="never" class="header-card">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">作业管理</h1>
          <p class="page-subtitle">{{ className }}</p>
        </div>
      </div>
    </el-card>

    <!-- 单元列表 -->
    <el-card shadow="never" class="units-card">
      <template #header>
        <div class="card-header">
          <span>学习单元列表</span>
          <span class="unit-count">共 {{ unitList.length }} 个单元</span>
        </div>
      </template>
      
      <div v-loading="loading" class="units-grid">
        <div 
          v-for="unit in unitList" 
          :key="unit.id" 
          class="unit-card"
          @click="selectUnit(unit)"
        >
          <div class="unit-header">
            <h3>{{ unit.title }}</h3>
            <el-tag size="large" type="warning">{{ unit.task_count }} 个作业</el-tag>
          </div>
          <div class="unit-order">
            <el-tag type="info" size="small">单元 {{ unit.order }}</el-tag>
          </div>
          <div class="unit-description">
            {{ unit.description || '暂无描述' }}
          </div>
          <div class="unit-footer">
            <el-button type="primary" link>
              查看作业
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>
        
        <el-empty 
          v-if="!loading && unitList.length === 0" 
          description="暂无学习单元"
          style="grid-column: 1 / -1;"
        />
      </div>
    </el-card>


    <!-- 批改作业抽屉 -->
    <el-drawer
      v-model="gradingDrawerVisible"
      :title="selectedTask?.title + ' - 批改作业'"
      size="95%"
      direction="rtl"
    >
      <div v-loading="loadingSubmissions" class="grading-content">
        <!-- 作业信息 -->
        <el-descriptions :column="2" border class="task-info">
          <el-descriptions-item label="作业标题" :span="2">
            {{ selectedTask?.title }}
          </el-descriptions-item>
          <el-descriptions-item label="作业描述" :span="2">
            {{ selectedTask?.description || '暂无描述' }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">
          <h3>学生提交列表</h3>
        </el-divider>

        <!-- 筛选 -->
        <div class="filter-bar">
          <el-select v-model="filterStatus" placeholder="筛选状态" style="width: 150px" clearable>
            <el-option label="全部" value="" />
            <el-option label="未提交" value="pending" />
            <el-option label="已提交" value="review" />
            <el-option label="已批改" value="completed" />
          </el-select>
          <span class="filter-tip">
            找到 {{ filteredSubmissions.length }} 名学生
          </span>
        </div>

        <!-- 提交列表 -->
        <el-table 
          :data="filteredSubmissions" 
          border
          stripe
          style="width: 100%"
          :max-height="600"
        >
          <el-table-column type="index" label="序号" width="80" align="center" fixed="left" />
          <el-table-column prop="student_number" label="学号" width="150" sortable fixed="left" />
          <el-table-column prop="student_name" label="姓名" width="120" sortable fixed="left" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getSubmissionStatusType(row.status)">
                {{ getSubmissionStatusName(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="等级" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.grade" :type="getGradeTagType(row.grade)">
                {{ getGradeName(row.grade) }}
              </el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="score" label="分数" width="100" sortable>
            <template #default="{ row }">
              {{ row.score !== null ? row.score : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="feedback" label="评语" min-width="200" show-overflow-tooltip />
          <el-table-column prop="submitted_at" label="提交时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.submitted_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="graded_at" label="批改时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.graded_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button 
                link 
                type="primary" 
                @click="openGradeDialog(row)"
                v-if="row.submission_id"
              >
                <el-icon><Edit /></el-icon>
                {{ row.graded_at ? '重新批改' : '批改' }}
              </el-button>
              <el-button 
                link 
                type="info" 
                @click="viewSubmission(row)"
                v-if="row.submission"
              >
                <el-icon><View /></el-icon>
                查看提交
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-drawer>

    <!-- 批改对话框 -->
    <el-dialog
      v-model="gradeDialogVisible"
      title="批改作业"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form :model="gradeForm" label-width="100px">
        <el-form-item label="学生">
          <el-input :value="currentSubmission?.student_name + ' (' + currentSubmission?.student_number + ')'" disabled />
        </el-form-item>
        
        <el-form-item label="等级" required>
          <el-radio-group v-model="gradeForm.grade" @change="onGradeChange">
            <el-radio value="excellent">
              <el-tag type="success" size="large">优秀</el-tag>
            </el-radio>
            <el-radio value="good">
              <el-tag type="success" effect="plain" size="large">良好</el-tag>
            </el-radio>
            <el-radio value="pass">
              <el-tag type="warning" size="large">及格</el-tag>
            </el-radio>
            <el-radio value="fail">
              <el-tag type="danger" size="large">不及格</el-tag>
            </el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="分数">
          <el-input-number 
            v-model="gradeForm.score" 
            :min="0" 
            :max="100" 
            placeholder="0-100"
            style="width: 200px"
          />
          <span style="margin-left: 12px; color: #909399;">分（可选）</span>
        </el-form-item>
        
        <el-form-item label="评语模板">
          <el-select 
            v-model="selectedTemplate" 
            placeholder="选择评语模板" 
            style="width: 100%"
            clearable
            @change="onTemplateChange"
          >
            <el-option
              v-for="template in filteredTemplates"
              :key="template.id"
              :label="template.title"
              :value="template.id"
            >
              <div style="display: flex; justify-content: space-between;">
                <span>{{ template.title }}</span>
                <el-tag :type="getCategoryTagType(template.category)" size="small">
                  {{ template.category }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
          <div class="form-tip">提示：选择模板后，评语会自动填充，你也可以自行修改</div>
        </el-form-item>
        
        <el-form-item label="评语" required>
          <el-input 
            v-model="gradeForm.feedback" 
            type="textarea" 
            :rows="5"
            placeholder="请输入评语"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="gradeDialogVisible = false" size="large">取消</el-button>
        <el-button type="primary" @click="submitGrade" :loading="submittingGrade" size="large">
          提交批改
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看提交对话框 -->
    <el-dialog
      v-model="viewSubmissionDialogVisible"
      title="查看提交内容"
      width="800px"
    >
      <div class="submission-content">
        <pre>{{ JSON.stringify(currentSubmission?.submission, null, 2) }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, ArrowRight, Edit, View
} from '@element-plus/icons-vue'
import { getClubClassDetail } from '@pbl/admin/api/club'
import request from '@/utils/request'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const loadingSubmissions = ref(false)
const unitList = ref([])
const className = ref('')
const gradingDrawerVisible = ref(false)
const gradeDialogVisible = ref(false)
const viewSubmissionDialogVisible = ref(false)
const selectedTask = ref(null)
const submissions = ref([])
const currentSubmission = ref(null)
const filterStatus = ref('')
const submittingGrade = ref(false)
const feedbackTemplates = ref([])
const selectedTemplate = ref(null)

const gradeForm = ref({
  grade: '',
  score: null,
  feedback: ''
})

// 计算属性 - 过滤后的提交列表
const filteredSubmissions = computed(() => {
  if (!submissions.value) return []
  if (!filterStatus.value) return submissions.value
  return submissions.value.filter(s => s.status === filterStatus.value)
})

// 计算属性 - 根据等级过滤模板
const filteredTemplates = computed(() => {
  if (!gradeForm.value.grade) return feedbackTemplates.value
  
  const gradeMap = {
    'excellent': '优秀',
    'good': '良好',
    'pass': '及格',
    'fail': '不及格'
  }
  
  const category = gradeMap[gradeForm.value.grade]
  return feedbackTemplates.value.filter(t => t.category === category)
})

// 加载班级名称
const loadClassName = async () => {
  try {
    const res = await getClubClassDetail(route.params.uuid)
    className.value = res.data.data.name
  } catch (error) {
    console.error('加载班级名称失败:', error)
  }
}

// 加载单元列表（极速）
const loadUnitList = async () => {
  loading.value = true
  try {
    const res = await request({
      url: `/admin/club/classes/${route.params.uuid}/homework/units`,
      method: 'get'
    })
    unitList.value = res.data.data || []
  } catch (error) {
    ElMessage.error(error.message || '加载单元列表失败')
  } finally {
    loading.value = false
  }
}

// 加载评语模板
const loadFeedbackTemplates = async () => {
  try {
    const res = await request({
      url: '/admin/feedback-templates',
      method: 'get'
    })
    feedbackTemplates.value = res.data.data || []
  } catch (error) {
    console.error('加载评语模板失败:', error)
  }
}

// 选择单元 - 跳转到单独页面
const selectUnit = (unit) => {
  router.push(`/pbl/admin/classes/${route.params.uuid}/homework/units/${unit.id}`)
}

// 批改作业
const gradeHomework = (task) => {
  selectedTask.value = task
  gradingDrawerVisible.value = true
  submissions.value = []
  filterStatus.value = ''
  loadTaskSubmissions()
}

// 加载作业提交列表
const loadTaskSubmissions = async () => {
  if (!selectedTask.value) return
  
  loadingSubmissions.value = true
  try {
    const res = await request({
      url: `/admin/club/classes/${route.params.uuid}/homework/tasks/${selectedTask.value.id}/submissions`,
      method: 'get'
    })
    submissions.value = res.data.data.submissions || []
  } catch (error) {
    ElMessage.error(error.message || '加载提交列表失败')
  } finally {
    loadingSubmissions.value = false
  }
}

// 打开批改对话框
const openGradeDialog = (submission) => {
  currentSubmission.value = submission
  gradeForm.value = {
    grade: submission.grade || '',
    score: submission.score,
    feedback: submission.feedback || ''
  }
  selectedTemplate.value = null
  gradeDialogVisible.value = true
}

// 等级变化时，重置模板选择
const onGradeChange = () => {
  selectedTemplate.value = null
}

// 模板变化时，填充评语
const onTemplateChange = (templateId) => {
  if (!templateId) return
  const template = feedbackTemplates.value.find(t => t.id === templateId)
  if (template) {
    gradeForm.value.feedback = template.content
  }
}

// 提交批改
const submitGrade = async () => {
  if (!gradeForm.value.grade) {
    ElMessage.warning('请选择等级')
    return
  }
  if (!gradeForm.value.feedback) {
    ElMessage.warning('请输入评语')
    return
  }
  
  submittingGrade.value = true
  try {
    await request({
      url: `/admin/club/classes/${route.params.uuid}/homework/submissions/${currentSubmission.value.submission_id}/review`,
      method: 'put',
      data: {
        grade: gradeForm.value.grade,
        score: gradeForm.value.score,
        feedback: gradeForm.value.feedback,
        status: 'completed'
      }
    })
    ElMessage.success('批改成功')
    gradeDialogVisible.value = false
    loadTaskSubmissions() // 刷新列表
  } catch (error) {
    ElMessage.error(error.message || '批改失败')
  } finally {
    submittingGrade.value = false
  }
}

// 查看提交内容
const viewSubmission = (submission) => {
  currentSubmission.value = submission
  viewSubmissionDialogVisible.value = true
}

// 工具方法
const getSubmissionRate = (task) => {
  if (task.total_count === 0) return 0
  return Math.round((task.submitted_count / task.total_count) * 100)
}

const getStatusName = (status) => {
  const map = {
    draft: '未发布',
    ongoing: '进行中',
    ended: '已截止'
  }
  return map[status] || status
}

const getStatusTagType = (status) => {
  const map = {
    draft: 'info',
    ongoing: 'success',
    ended: 'danger'
  }
  return map[status] || 'info'
}

const getTypeName = (type) => {
  const map = {
    analysis: '分析',
    coding: '编程',
    design: '设计',
    deployment: '部署'
  }
  return map[type] || type
}

const getTypeTagType = (type) => {
  const map = {
    analysis: '',
    coding: 'success',
    design: 'warning',
    deployment: 'danger'
  }
  return map[type] || 'info'
}

const getDifficultyName = (difficulty) => {
  const map = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  }
  return map[difficulty] || difficulty
}

const getDifficultyTagType = (difficulty) => {
  const map = {
    easy: 'success',
    medium: 'warning',
    hard: 'danger'
  }
  return map[difficulty] || 'info'
}

const getSubmissionStatusName = (status) => {
  const map = {
    pending: '未提交',
    'in-progress': '进行中',
    review: '已提交',
    completed: '已批改'
  }
  return map[status] || status
}

const getSubmissionStatusType = (status) => {
  const map = {
    pending: 'info',
    'in-progress': 'warning',
    review: '',
    completed: 'success'
  }
  return map[status] || 'info'
}

const getGradeName = (grade) => {
  const map = {
    excellent: '优秀',
    good: '良好',
    pass: '及格',
    fail: '不及格'
  }
  return map[grade] || grade
}

const getGradeTagType = (grade) => {
  const map = {
    excellent: 'success',
    good: 'success',
    pass: 'warning',
    fail: 'danger'
  }
  return map[grade] || 'info'
}

const getCategoryTagType = (category) => {
  const map = {
    '优秀': 'success',
    '良好': 'success',
    '及格': 'warning',
    '不及格': 'danger'
  }
  return map[category] || 'info'
}

const getDeadlineClass = (deadline) => {
  if (!deadline) return ''
  const now = dayjs()
  const deadlineDate = dayjs(deadline)
  const diffDays = deadlineDate.diff(now, 'day')
  
  if (diffDays < 0) return 'deadline-passed'
  if (diffDays <= 1) return 'deadline-soon'
  return ''
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
}

const goBack = () => {
  router.push(`/pbl/admin/classes/${route.params.uuid}`)
}

onMounted(async () => {
  await loadClassName()
  await loadUnitList()
  await loadFeedbackTemplates()
})
</script>

<style scoped lang="scss">
.class-homework-container {
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

.units-card {
  border-radius: 12px;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 16px;
    font-weight: 600;
    
    .unit-count {
      font-size: 14px;
      color: #909399;
      font-weight: normal;
    }
  }
}

.units-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  padding: 20px 0;
}

.unit-card {
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fff;
  
  &:hover {
    border-color: #409eff;
    box-shadow: 0 4px 16px 0 rgba(64, 158, 255, 0.25);
    transform: translateY(-4px);
  }
  
  .unit-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
    
    h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #303133;
      flex: 1;
      margin-right: 12px;
    }
  }
  
  .unit-order {
    margin-bottom: 12px;
  }
  
  .unit-description {
    font-size: 14px;
    color: #606266;
    line-height: 1.6;
    min-height: 44px;
    margin-bottom: 16px;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  
  .unit-footer {
    border-top: 1px solid #f0f0f0;
    padding-top: 12px;
    text-align: right;
  }
}

.grading-content {
  padding: 0 24px 24px 24px;
  
  .task-info {
    margin-bottom: 24px;
  }
  
  .filter-bar {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 16px;
    
    .filter-tip {
      font-size: 14px;
      color: #909399;
    }
  }
}

.task-title {
  display: flex;
  align-items: center;
}

.deadline-soon {
  color: #e6a23c;
  font-weight: 600;
}

.deadline-passed {
  color: #f56c6c;
  font-weight: 600;
}

.submission-content {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  max-height: 500px;
  overflow-y: auto;
  
  pre {
    margin: 0;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
}

.form-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

:deep(.el-drawer__header) {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-radio) {
  margin-right: 20px;
  margin-bottom: 12px;
}
</style>
