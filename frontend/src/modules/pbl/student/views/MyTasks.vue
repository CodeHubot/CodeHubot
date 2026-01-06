<template>
  <div class="my-tasks-container">
    <div class="page-header">
      <h1>我提交的任务</h1>
    </div>

    <!-- 任务列表表格 -->
    <el-table 
      :data="tasks" 
      v-loading="loading"
      stripe
      style="width: 100%"
    >
      <el-table-column prop="course_title" label="课程" width="180" show-overflow-tooltip />
      
      <el-table-column prop="unit_title" label="单元" width="180" show-overflow-tooltip sortable />
      
      <el-table-column prop="task_title" label="任务名称" min-width="200" show-overflow-tooltip />
      
      <el-table-column prop="submitted_at" label="最后提交时间" width="180" sortable>
        <template #default="{ row }">
          <span v-if="row.submitted_at">{{ formatDateTime(row.submitted_at) }}</span>
          <span v-else class="text-muted">-</span>
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="120" align="center" fixed="right">
        <template #default="{ row }">
          <el-button 
            type="primary" 
            link 
            size="small"
            @click="viewSubmission(row)"
          >
            查看详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 提交内容查看对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="currentTask?.task_title"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="currentTask" class="submission-detail">
        <div class="detail-section">
          <div class="section-header">
            <span class="section-title">课程信息</span>
          </div>
          <div class="info-row">
            <span class="label">课程：</span>
            <span class="value">{{ currentTask.course_title }}</span>
          </div>
          <div class="info-row">
            <span class="label">单元：</span>
            <span class="value">{{ currentTask.unit_title }}</span>
          </div>
        </div>

        <div class="detail-section">
          <div class="section-header">
            <span class="section-title">提交信息</span>
          </div>
          <div class="info-row">
            <span class="label">提交时间：</span>
            <span class="value">{{ formatDateTime(currentTask.submitted_at) }}</span>
          </div>
          <div v-if="currentTask.graded_at" class="info-row">
            <span class="label">批改时间：</span>
            <span class="value">{{ formatDateTime(currentTask.graded_at) }}</span>
          </div>
          <div v-if="currentTask.score !== null" class="info-row">
            <span class="label">得分：</span>
            <span class="value score-value">{{ currentTask.score }}</span>
          </div>
        </div>

        <div v-if="submissionContent" class="detail-section">
          <div class="section-header">
            <span class="section-title">提交内容</span>
          </div>
          <div class="submission-content">
            <div v-if="submissionContent.content" class="content-item">
              <div class="content-label">内容：</div>
              <div class="content-value">{{ submissionContent.content }}</div>
            </div>
            
            <!-- ✅ 显示真实的附件列表（从 pbl_task_attachments 表加载） -->
            <div v-if="attachments.length > 0" class="content-item">
              <div class="content-label">附件：</div>
              <div class="attachments-list">
                <div 
                  v-for="attachment in attachments" 
                  :key="attachment.uuid"
                  class="attachment-item"
                >
                  <div class="attachment-info">
                    <el-icon class="file-icon"><Document /></el-icon>
                    <span class="file-name">{{ attachment.filename }}</span>
                    <span class="file-size">{{ formatFileSize(attachment.file_size) }}</span>
                  </div>
                  <el-button
                    type="primary"
                    link
                    :icon="Download"
                    @click="downloadAttachment(attachment)"
                    size="small"
                  >
                    下载
                  </el-button>
                </div>
              </div>
              <div v-if="loadingAttachments" class="loading-text">
                <el-icon class="is-loading"><Loading /></el-icon>
                加载附件列表...
              </div>
            </div>
            
            <!-- 保留旧格式的文件显示（兼容） -->
            <div v-if="submissionContent.files && submissionContent.files.length > 0" class="content-item">
              <div class="content-label">其他文件：</div>
              <div class="files-list">
                <div v-for="(file, index) in submissionContent.files" :key="index" class="file-item">
                  <el-icon><Document /></el-icon>
                  <span>{{ file.name || file }}</span>
                </div>
              </div>
            </div>
            
            <div v-if="submissionContent.url" class="content-item">
              <div class="content-label">链接：</div>
              <div class="content-value">
                <el-link :href="submissionContent.url" target="_blank" type="primary">
                  {{ submissionContent.url }}
                </el-link>
              </div>
            </div>
            <!-- 显示其他提交字段 -->
            <div v-for="(value, key) in otherSubmissionFields" :key="key" class="content-item">
              <div class="content-label">{{ key }}：</div>
              <div class="content-value">{{ value }}</div>
            </div>
          </div>
        </div>

        <div v-if="currentTask.feedback" class="detail-section">
          <div class="section-header">
            <span class="section-title">教师反馈</span>
          </div>
          <div class="feedback-content">
            {{ currentTask.feedback }}
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-empty v-if="!loading && tasks.length === 0" description="您还没有提交过任何任务" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Download, Loading } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { 
  getAttachmentsByProgress,
  downloadAttachment as downloadAttachmentAPI,
  formatFileSize
} from '../api/attachment'

const loading = ref(false)
const tasks = ref([])
const dialogVisible = ref(false)
const currentTask = ref(null)
const submissionContent = ref(null)
const attachments = ref([])  // 真实的附件列表
const loadingAttachments = ref(false)

// 加载任务列表
const loadTasks = async () => {
  loading.value = true
  try {
    const response = await request.get('/pbl/student/my-tasks')
    // response.data 已经是后端返回的 data 字段（拦截器已处理）
    tasks.value = response.data || []
  } catch (error) {
    console.error('加载任务列表失败:', error)
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

// 加载附件列表
const loadAttachments = async (progressId) => {
  if (!progressId) {
    attachments.value = []
    return
  }
  
  loadingAttachments.value = true
  try {
    const result = await getAttachmentsByProgress(progressId)
    attachments.value = result.data || []
  } catch (error) {
    console.error('加载附件列表失败:', error)
    attachments.value = []
  } finally {
    loadingAttachments.value = false
  }
}

// 下载附件
const downloadAttachment = async (attachment) => {
  try {
    const response = await downloadAttachmentAPI(attachment.uuid)
    
    // 创建Blob对象并触发下载
    const blob = new Blob([response])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = attachment.filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('附件下载成功')
  } catch (error) {
    console.error('下载附件失败:', error)
    ElMessage.error(error.message || '下载失败')
  }
}

// 查看提交内容
const viewSubmission = async (task) => {
  try {
    // 获取任务详情（包含提交内容）
    const response = await request.get(`/pbl/student/tasks/${task.task_uuid}`)
    // response.data 已经是后端返回的 data 字段（拦截器已处理）
    const taskDetail = response.data
    
    currentTask.value = {
      ...task,
      feedback: taskDetail.progress?.feedback || task.feedback
    }
    submissionContent.value = taskDetail.progress?.submission || null
    dialogVisible.value = true
    
    // 加载附件列表（使用 progress_id）
    if (taskDetail.progress?.id) {
      await loadAttachments(taskDetail.progress.id)
    } else {
      attachments.value = []
    }
  } catch (error) {
    console.error('获取提交内容失败:', error)
    ElMessage.error('获取提交内容失败')
  }
}

// 计算其他提交字段（排除已显示的字段）
const otherSubmissionFields = computed(() => {
  if (!submissionContent.value) return {}
  
  const excludeKeys = ['content', 'files', 'url', 'submitted_at']
  const result = {}
  
  for (const [key, value] of Object.entries(submissionContent.value)) {
    if (!excludeKeys.includes(key) && value !== null && value !== undefined && value !== '') {
      result[key] = typeof value === 'object' ? JSON.stringify(value, null, 2) : value
    }
  }
  
  return result
})

// 格式化日期时间
const formatDateTime = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.my-tasks-container {
  padding: 24px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 20px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.task-name {
  display: flex;
  align-items: center;
}

.text-muted {
  color: #94a3b8;
}

/* 提交内容详情样式 */
.submission-detail {
  max-height: 600px;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e2e8f0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.info-row {
  display: flex;
  margin-bottom: 12px;
  line-height: 1.6;
}

.info-row .label {
  width: 100px;
  color: #64748b;
  font-weight: 500;
  flex-shrink: 0;
}

.info-row .value {
  flex: 1;
  color: #1e293b;
}

.score-value {
  font-size: 18px;
  font-weight: 600;
  color: #3b82f6;
}

.submission-content {
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
}

.content-item {
  margin-bottom: 16px;
}

.content-item:last-child {
  margin-bottom: 0;
}

.content-label {
  color: #64748b;
  font-weight: 500;
  margin-bottom: 8px;
}

.content-value {
  color: #1e293b;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  color: #475569;
}

.file-item .el-icon {
  color: #3b82f6;
  font-size: 18px;
}

/* 附件列表样式 */
.attachments-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.attachment-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
}

.attachment-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.attachment-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.attachment-info .file-icon {
  color: #3b82f6;
  font-size: 20px;
  flex-shrink: 0;
}

.attachment-info .file-name {
  color: #1e293b;
  font-weight: 500;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attachment-info .file-size {
  color: #94a3b8;
  font-size: 13px;
  flex-shrink: 0;
}

.loading-text {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748b;
  font-size: 14px;
  padding: 12px;
  justify-content: center;
}

.loading-text .el-icon {
  font-size: 16px;
}

.feedback-content {
  background: #fff7ed;
  border-left: 4px solid #f59e0b;
  padding: 16px;
  border-radius: 4px;
  color: #475569;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

:deep(.el-table) {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
}

:deep(.el-table th) {
  background-color: #f8fafc;
  color: #475569;
  font-weight: 600;
}

:deep(.el-table td) {
  color: #1e293b;
}

@media (max-width: 768px) {
  .my-tasks-container {
    padding: 12px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .page-header h1 {
    font-size: 20px;
  }
}
</style>
