<template>
  <div class="learning-assistant-teacher">
    <el-card shadow="never" class="header-card">
      <div class="header">
        <div class="title">
          <el-icon><View /></el-icon>
          <span>学生AI学习助手监控</span>
        </div>
        <div class="actions">
          <el-select v-model="filterCourse" placeholder="筛选课程" clearable style="width: 200px">
            <el-option label="全部课程" value="" />
            <el-option label="Python编程" value="course-1" />
          </el-select>
          <el-button :icon="Refresh" @click="loadStudents">刷新</el-button>
        </div>
      </div>
    </el-card>

    <div class="content-wrapper">
      <!-- 左侧：学生列表 -->
      <el-card shadow="never" class="students-panel">
        <template #header>
          <div class="panel-header">
            <span>学生列表</span>
            <el-badge :value="students.length" class="badge" />
          </div>
        </template>
        
        <el-input
          v-model="searchStudent"
          placeholder="搜索学生姓名"
          :prefix-icon="Search"
          clearable
          style="margin-bottom: 16px"
        />

        <el-scrollbar height="calc(100vh - 320px)">
          <div
            v-for="student in filteredStudents"
            :key="student.student_id"
            class="student-item"
            :class="{ active: selectedStudent?.student_id === student.student_id }"
            @click="selectStudent(student)"
          >
            <div class="student-info">
              <el-avatar :size="40">{{ student.student_name.slice(0, 1) }}</el-avatar>
              <div class="info">
                <div class="name">{{ student.student_name }}</div>
                <div class="stats">
                  {{ student.total_conversations }}个会话 · {{ student.total_messages }}条消息
                </div>
              </div>
            </div>
            <div class="last-active">
              {{ formatTime(student.last_active_at) }}
            </div>
          </div>

          <el-empty v-if="filteredStudents.length === 0" description="暂无学生数据" />
        </el-scrollbar>
      </el-card>

      <!-- 右侧：对话详情 -->
      <div class="conversations-panel">
        <el-card v-if="!selectedStudent" shadow="never" class="empty-state">
          <el-empty description="请选择一个学生查看对话记录" />
        </el-card>

        <template v-else>
          <div class="detail-wrapper">
            <!-- 学生信息卡片 -->
            <el-card shadow="never" class="student-detail">
              <div class="detail-header">
                <el-avatar :size="60">{{ selectedStudent.student_name.slice(0, 1) }}</el-avatar>
                <div class="detail-info">
                  <h3>{{ selectedStudent.student_name }}</h3>
                  <div class="stats-row">
                    <el-tag>总会话: {{ selectedStudent.total_conversations }}</el-tag>
                    <el-tag type="success">总消息: {{ selectedStudent.total_messages || 0 }}</el-tag>
                    <el-tag type="info">最后活跃: {{ formatTime(selectedStudent.last_active_at) }}</el-tag>
                  </div>
                </div>
              </div>
            </el-card>

            <!-- 会话列表 -->
            <el-card shadow="never" class="conversations-list-card">
              <template #header>
                <div class="panel-header">
                  <span>对话记录</span>
                  <el-badge :value="conversations.length" class="badge" />
                </div>
              </template>

              <div class="list-container">
                <el-scrollbar>
                  <div
                    v-for="conv in conversations"
                    :key="conv.uuid"
                    class="conversation-item"
                    @click="viewConversation(conv)"
                  >
                    <div class="conv-header">
                      <div class="conv-title">
                        <el-icon><ChatLineSquare /></el-icon>
                        {{ conv.title || '新的对话' }}
                      </div>
                      <el-tag v-if="conv.teacher_flagged" type="danger" size="small">
                        <el-icon><Flag /></el-icon> 已标记
                      </el-tag>
                    </div>
                    <div class="conv-meta">
                      <span>{{ conv.message_count }}条消息</span>
                      <span>·</span>
                      <span>{{ formatTime(conv.last_message_at) }}</span>
                      <span v-if="conv.course_name">·</span>
                      <span v-if="conv.course_name" class="course">{{ conv.course_name }}</span>
                    </div>
                  </div>

                  <el-empty v-if="conversations.length === 0" description="该学生暂无对话记录" />
                </el-scrollbar>
              </div>
            </el-card>
          </div>
        </template>
      </div>
    </div>

    <!-- 对话详情弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="对话详情"
      width="70%"
      :before-close="handleClose"
    >
      <div v-if="currentConversation" class="dialog-content">
        <div class="conv-info">
          <h3>{{ currentConversation.title }}</h3>
          <div class="conv-tags">
            <el-tag>{{ currentConversation.message_count }}条消息</el-tag>
            <el-tag type="info" v-if="currentConversation.course_name">
              {{ currentConversation.course_name }}
            </el-tag>
            <el-tag type="success">{{ formatTime(currentConversation.created_at) }}</el-tag>
          </div>
        </div>

        <el-divider />

        <el-scrollbar height="500px">
          <div class="messages-container">
            <div
              v-for="msg in currentMessages"
              :key="msg.uuid"
              class="message-item"
              :class="msg.role"
            >
              <div class="message-header">
                <span class="role">{{ msg.role === 'user' ? '学生' : 'AI助手' }}</span>
                <span class="time">{{ formatTime(msg.created_at) }}</span>
              </div>
              <div class="message-content" v-html="formatMarkdown(msg.content)"></div>
              
              <!-- AI消息的反馈和修正 -->
              <div v-if="msg.role === 'assistant'" class="message-actions">
                <el-tag v-if="msg.was_helpful === 1" type="success" size="small">
                  <el-icon><Select /></el-icon> 学生觉得有帮助
                </el-tag>
                <el-tag v-if="msg.was_helpful === 0" type="danger" size="small">
                  <el-icon><Close /></el-icon> 学生觉得无帮助
                </el-tag>
                <el-tag v-if="msg.teacher_corrected" type="warning" size="small">
                  <el-icon><Edit /></el-icon> 教师已修正
                </el-tag>
              </div>
            </div>
          </div>
        </el-scrollbar>

        <el-divider />

        <div class="dialog-actions">
          <el-button
            :type="currentConversation.teacher_flagged ? 'danger' : 'default'"
            :icon="Flag"
            @click="toggleFlag"
          >
            {{ currentConversation.teacher_flagged ? '取消标记' : '标记关注' }}
          </el-button>
          <el-button :icon="Edit" @click="addComment">添加备注</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  View, Refresh, Search, ChatLineSquare, Flag, Edit, Select, Close
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import {
  getStudentsList,
  getStudentConversations,
  getConversationMessagesAsTeacher,
  flagConversation,
  unflagConversation
} from '@/modules/pbl/student/api/learningAssistant'

// 数据
const students = ref([])
const selectedStudent = ref(null)
const conversations = ref([])
const searchStudent = ref('')
const filterCourse = ref('')
const dialogVisible = ref(false)
const currentConversation = ref(null)
const currentMessages = ref([])

// 计算属性
const filteredStudents = computed(() => {
  let result = students.value
  if (searchStudent.value) {
    result = result.filter(s => 
      s.student_name.toLowerCase().includes(searchStudent.value.toLowerCase())
    )
  }
  return result
})

// 加载学生列表
const loadStudents = async () => {
  try {
    const res = await getStudentsList({
      course_uuid: filterCourse.value || undefined,
      page: 1,
      pageSize: 100
    })
    students.value = res.data.items || res.data || []
    ElMessage.success('加载成功')
  } catch (error) {
    console.error('加载学生列表失败:', error)
    ElMessage.error('加载失败')
  }
}

// 选择学生
const selectStudent = async (student) => {
  selectedStudent.value = student
  await loadConversations()
}

// 加载会话列表
const loadConversations = async () => {
  if (!selectedStudent.value) return
  
  try {
    const res = await getStudentConversations(selectedStudent.value.student_uuid, {
      page: 1,
      pageSize: 100
    })
    conversations.value = res.data.items || res.data || []
  } catch (error) {
    console.error('加载会话列表失败:', error)
    ElMessage.error('加载会话失败')
  }
}

// 查看对话详情
const viewConversation = async (conv) => {
  currentConversation.value = conv
  dialogVisible.value = true
  
  try {
    const res = await getConversationMessagesAsTeacher(conv.uuid)
    currentMessages.value = res.data.messages || []
  } catch (error) {
    console.error('加载消息失败:', error)
    ElMessage.error('加载消息失败')
  }
}

// 标记/取消标记
const toggleFlag = async () => {
  try {
    if (currentConversation.value.teacher_flagged) {
      await unflagConversation(currentConversation.value.uuid)
      currentConversation.value.teacher_flagged = 0
      ElMessage.success('已取消标记')
    } else {
      await flagConversation(currentConversation.value.uuid, {})
      currentConversation.value.teacher_flagged = 1
      ElMessage.success('已标记为需要关注')
    }
    await loadConversations()
  } catch (error) {
    console.error('标记操作失败:', error)
    ElMessage.error('操作失败')
  }
}

// 添加备注
const addComment = () => {
  ElMessage.info('备注功能开发中')
}

// 关闭弹窗
const handleClose = () => {
  dialogVisible.value = false
  currentConversation.value = null
  currentMessages.value = []
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  
  return date.toLocaleDateString('zh-CN', { 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Markdown渲染
const formatMarkdown = (content) => {
  try {
    const html = marked.parse(content || '')
    return DOMPurify.sanitize(html)
  } catch {
    return content
  }
}

// 初始化
onMounted(() => {
  loadStudents()
})
</script>

<style scoped lang="scss">
.learning-assistant-teacher {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.header-card {
  margin-bottom: 20px;
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 18px;
      font-weight: 600;
    }
    
    .actions {
      display: flex;
      gap: 12px;
    }
  }
}

.content-wrapper {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 20px;
  height: calc(100vh - 140px);
  overflow: hidden;
}

.students-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  
  :deep(.el-card__body) {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
}

.conversations-panel {
  height: 100%;
  overflow: hidden;
  
  .empty-state {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .detail-wrapper {
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  
  .student-detail {
    flex-shrink: 0;
    
    .detail-header {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .detail-info {
        h3 {
          margin: 0 0 8px;
        }
        
        .stats-row {
          display: flex;
          gap: 8px;
        }
      }
    }
  }
  
  .conversations-list-card {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    
    :deep(.el-card__body) {
      flex: 1;
      overflow: hidden;
      padding: 0;
      display: flex;
      flex-direction: column;
    }
    
    .list-container {
      flex: 1;
      overflow: hidden;
    }
    
    .conversation-item {
      padding: 16px 20px;
      border-bottom: 1px solid #f0f0f0;
      cursor: pointer;
      transition: all 0.3s;
      
      &:last-child {
        border-bottom: none;
      }
      
      &:hover {
        background: #f9f9f9;
      }
      
      .conv-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        
        .conv-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 500;
          color: #333;
        }
      }
      
      .conv-meta {
        font-size: 12px;
        color: #999;
        display: flex;
        gap: 12px;
        
        .course {
          color: #1890ff;
          background: #e6f7ff;
          padding: 0 4px;
          border-radius: 2px;
        }
      }
    }
  }
}

.dialog-content {
  .conv-info {
    h3 {
      margin: 0 0 12px;
    }
    
    .conv-tags {
      display: flex;
      gap: 8px;
    }
  }
  
  .messages-container {
    .message-item {
      margin-bottom: 20px;
      padding: 12px;
      border-radius: 8px;
      
      &.user {
        background: #e6f7ff;
      }
      
      &.assistant {
        background: #f6ffed;
      }
      
      .message-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-size: 12px;
        
        .role {
          font-weight: 600;
          color: #1890ff;
        }
        
        .time {
          color: #999;
        }
      }
      
      .message-content {
        line-height: 1.6;
        
        :deep(code) {
          background: #f5f5f5;
          padding: 2px 6px;
          border-radius: 4px;
        }
      }
      
      .message-actions {
        margin-top: 8px;
        display: flex;
        gap: 8px;
      }
    }
  }
  
  .dialog-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }
}
</style>

