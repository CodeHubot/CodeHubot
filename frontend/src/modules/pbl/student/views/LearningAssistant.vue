<template>
  <div class="learning-assistant">
    <!-- 左侧边栏 - 会话列表 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="header-left" v-if="!sidebarCollapsed">
          <div class="assistant-brand">
            <div class="brand-icon">
              <el-icon><ChatDotRound /></el-icon>
            </div>
            <span class="brand-name">AI学习助手</span>
          </div>
        </div>
      </div>

      <div v-if="!sidebarCollapsed" class="sidebar-content">
        <!-- 搜索框 -->
        <div class="search-wrapper">
          <el-input
            v-model="searchQuery"
            placeholder="搜索对话标题..."
            :prefix-icon="Search"
            clearable
            size="small"
            class="search-input"
          />
        </div>

        <!-- 会话列表 -->
        <div class="conversations-list" ref="conversationsList" @scroll="handleListScroll">
          <div v-if="filteredGroups.today.length > 0" class="list-section">
            <div class="section-title">今天</div>
            <div 
              v-for="conv in filteredGroups.today" 
              :key="conv.id"
              class="conversation-item"
              :class="{ active: currentConversation?.id === conv.id }"
              @click="selectConversation(conv)"
            >
              <div class="conv-content">
                <div class="conv-icon">
                  <el-icon><ChatLineSquare /></el-icon>
                </div>
                <div class="conv-info">
                  <div class="conv-title">{{ conv.title }}</div>
                  <div class="conv-meta">
                    <span class="conv-time">{{ formatTime(conv.lastMessageTime) }}</span>
                    <span class="conv-divider">·</span>
                    <span class="conv-count">{{ conv.messageCount }}条消息</span>
                  </div>
                </div>
              </div>
              <div class="conv-actions">
                <el-dropdown trigger="click" @command="(cmd) => handleConvAction(cmd, conv)">
                  <el-button :icon="MoreFilled" circle size="small" text />
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="rename">
                        <el-icon><Edit /></el-icon>
                        重命名
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>

          <div v-if="filteredGroups.yesterday.length > 0" class="list-section">
            <div class="section-title">昨天</div>
            <div 
              v-for="conv in filteredGroups.yesterday" 
              :key="conv.id"
              class="conversation-item"
              :class="{ active: currentConversation?.id === conv.id }"
              @click="selectConversation(conv)"
            >
              <div class="conv-content">
                <div class="conv-icon">
                  <el-icon><ChatLineSquare /></el-icon>
                </div>
                <div class="conv-info">
                  <div class="conv-title">{{ conv.title }}</div>
                  <div class="conv-meta">
                    <span class="conv-time">{{ formatTime(conv.lastMessageTime) }}</span>
                    <span class="conv-divider">·</span>
                    <span class="conv-count">{{ conv.messageCount }}条消息</span>
                  </div>
                </div>
              </div>
              <div class="conv-actions">
                <el-dropdown trigger="click" @command="(cmd) => handleConvAction(cmd, conv)">
                  <el-button :icon="MoreFilled" circle size="small" text />
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="rename">
                        <el-icon><Edit /></el-icon>
                        重命名
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>

          <div v-if="filteredGroups.last7Days.length > 0" class="list-section">
            <div class="section-title">过去 7 天</div>
            <div 
              v-for="conv in filteredGroups.last7Days" 
              :key="conv.id"
              class="conversation-item"
              :class="{ active: currentConversation?.id === conv.id }"
              @click="selectConversation(conv)"
            >
              <div class="conv-content">
                <div class="conv-icon">
                  <el-icon><ChatLineSquare /></el-icon>
                </div>
                <div class="conv-info">
                  <div class="conv-title">{{ conv.title }}</div>
                  <div class="conv-meta">
                    <span class="conv-time">{{ formatDate(conv.lastMessageTime) }}</span>
                    <span class="conv-divider">·</span>
                    <span class="conv-count">{{ conv.messageCount }}条消息</span>
                  </div>
                </div>
              </div>
              <div class="conv-actions">
                <el-dropdown trigger="click" @command="(cmd) => handleConvAction(cmd, conv)">
                  <el-button :icon="MoreFilled" circle size="small" text />
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="rename">
                        <el-icon><Edit /></el-icon>
                        重命名
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>

          <div v-if="filteredGroups.older.length > 0" class="list-section">
            <div class="section-title">更早</div>
            <div 
              v-for="conv in filteredGroups.older" 
              :key="conv.id"
              class="conversation-item"
              :class="{ active: currentConversation?.id === conv.id }"
              @click="selectConversation(conv)"
            >
              <div class="conv-content">
                <div class="conv-icon">
                  <el-icon><ChatLineSquare /></el-icon>
                </div>
                <div class="conv-info">
                  <div class="conv-title">{{ conv.title }}</div>
                  <div class="conv-meta">
                    <span class="conv-time">{{ formatDate(conv.lastMessageTime) }}</span>
                    <span class="conv-divider">·</span>
                    <span class="conv-count">{{ conv.messageCount }}条消息</span>
                  </div>
                </div>
              </div>
              <div class="conv-actions">
                <el-dropdown trigger="click" @command="(cmd) => handleConvAction(cmd, conv)">
                  <el-button :icon="MoreFilled" circle size="small" text />
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="rename">
                        <el-icon><Edit /></el-icon>
                        重命名
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>

          <!-- 无搜索结果 -->
          <div v-if="isSearching && totalFilteredCount === 0" class="search-empty">
            <el-empty description="未找到相关对话" :image-size="60" />
          </div>

          <div v-if="!isSearching && conversations.length === 0" class="empty-conversations">
            <el-empty description="暂无对话记录" :image-size="80" />
          </div>

          <!-- 加载更多指示器 -->
          <div v-if="loadingMore" class="list-loading-more">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>加载中...</span>
          </div>
          <div v-else-if="!hasMore && conversations.length > 0 && !isSearching" class="list-no-more">
            没有更多了
          </div>
        </div>
      </div>
    </aside>

    <!-- 主内容区 - 对话界面 -->
    <main class="main-content">
      <!-- 空状态 - 欢迎界面 -->
      <div v-if="!currentConversation" class="welcome-screen">
        <div class="welcome-content">
          <div class="welcome-icon">
            <el-icon><MagicStick /></el-icon>
          </div>
          <h1 class="welcome-title">👋 你好！我是你的 AI 学习助手</h1>
          <p class="welcome-subtitle">
            在进行课程单元学习时，你可以随时点击右下角的 AI 图标打开助手。<br/>
            我会根据你当前学习的内容，为你提供实时的答疑和指导。
          </p>

          <div class="welcome-features">
            <div class="feature-item">
              <el-icon color="#409eff"><Clock /></el-icon>
              <span>课程学习记录自动同步</span>
            </div>
            <div class="feature-item">
              <el-icon color="#67c23a"><Document /></el-icon>
              <span>多轮对话上下文理解</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 对话界面 -->
      <div v-else class="chat-container">
        <!-- 对话头部 -->
        <div class="chat-header">
          <div class="header-left">
            <h2 class="chat-title">{{ currentConversation.title }}</h2>
            <span class="chat-info">{{ currentConversation.messageCount }}条消息</span>
            
            <div v-if="currentConversation.course_name" class="header-context">
              <span class="context-divider">|</span>
              <el-tag size="small" type="info" effect="plain" class="course-tag">
                {{ currentConversation.course_name }}
                <span v-if="currentConversation.unit_name"> · {{ currentConversation.unit_name }}</span>
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div class="messages-container" ref="messagesContainer">
          <div 
            v-for="(message, index) in currentMessages" 
            :key="index"
            :class="['message-item', message.role]"
          >
            <div class="message-avatar">
              <el-icon v-if="message.role === 'user'">
                <User />
              </el-icon>
              <el-icon v-else>
                <Cpu />
              </el-icon>
            </div>
            <div class="message-content">
              <div class="message-text" v-html="formatMessage(message.content)"></div>
              
              <!-- 知识库来源 -->
              <div v-if="message.knowledgeSources && message.knowledgeSources.length > 0" class="knowledge-sources">
                <div v-for="(source, idx) in message.knowledgeSources" :key="idx" class="source-item">
                  <el-tag size="small" type="success">
                    <el-icon><Reading /></el-icon>
                    {{ source.document }}
                  </el-tag>
                </div>
              </div>
              
              <div class="message-meta">
                <span class="message-time">{{ formatMessageTime(message.timestamp) }}</span>
              </div>
            </div>
          </div>

          <!-- 思考中动画 -->
          <div v-if="isThinking" class="message-item assistant thinking">
            <div class="message-avatar">
              <el-icon><Cpu /></el-icon>
            </div>
            <div class="message-content">
              <div class="thinking-animation">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-container">
          <div class="input-wrapper">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              :placeholder="isThinking ? 'AI正在思考中...' : '输入你的问题... (Shift+Enter换行，Enter发送)'"
              @keydown.enter.exact.prevent="handleSend"
              :disabled="isThinking"
              class="message-input"
            />
            <el-button 
              type="primary"
              :icon="Promotion"
              @click="handleSend"
              :loading="isThinking"
              :disabled="!inputMessage.trim()"
              class="send-btn"
            >
              发送
            </el-button>
          </div>
          <div class="input-hint">
            你可以问我任何学习相关的问题，我会尽力帮助你~
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatDotRound,
  ChatLineSquare,
  Plus,
  Fold,
  Expand,
  MoreFilled,
  Edit,
  Delete,
  MagicStick,
  Search,
  Notebook,
  Reading,
  Clock,
  Document,
  Star,
  User,
  Cpu,
  Promotion,
  Loading
} from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { 
  getConversations, 
  getConversationMessages, 
  chatWithAssistant,
  deleteConversation,
  updateConversation,
  clearAllConversations
} from '../api/learningAssistant'

const router = useRouter()

// ===== 状态管理 =====
const sidebarCollapsed = ref(false)
const conversations = ref([])
const currentConversation = ref(null)
const inputMessage = ref('')
const loading = ref(false)
const loadingMore = ref(false)
const isThinking = ref(false)
const messagesContainer = ref(null)
const conversationsList = ref(null)
const searchQuery = ref('')

// 分页状态
const page = ref(1)
const pageSize = ref(10)
const hasMore = ref(true)

// ===== 计算属性 =====
const filteredConversations = computed(() => {
  if (!searchQuery.value.trim()) return conversations.value
  const query = searchQuery.value.toLowerCase()
  return conversations.value.filter(c => 
    c.title.toLowerCase().includes(query)
  )
})

const filteredGroups = computed(() => {
  const convs = filteredConversations.value
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const yesterday = today - 24 * 60 * 60 * 1000
  const last7Days = today - 7 * 24 * 60 * 60 * 1000

  return {
    today: convs.filter(c => c.lastMessageTime >= today)
      .sort((a, b) => b.lastMessageTime - a.lastMessageTime),
    yesterday: convs.filter(c => c.lastMessageTime >= yesterday && c.lastMessageTime < today)
      .sort((a, b) => b.lastMessageTime - a.lastMessageTime),
    last7Days: convs.filter(c => c.lastMessageTime >= last7Days && c.lastMessageTime < yesterday)
      .sort((a, b) => b.lastMessageTime - a.lastMessageTime),
    older: convs.filter(c => c.lastMessageTime < last7Days)
      .sort((a, b) => b.lastMessageTime - a.lastMessageTime)
  }
})

const isSearching = computed(() => !!searchQuery.value.trim())
const totalFilteredCount = computed(() => filteredConversations.value.length)

const currentMessages = computed(() => {
  if (!currentConversation.value) return []
  return currentConversation.value.messages || []
})

// ===== 方法 =====

// 切换侧边栏
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 创建新对话
// ✅ 创建新会话（本地临时会话，首次发送消息时后端会创建真实会话）
const createNewConversation = () => {
  const newConv = {
    id: `temp-${Date.now()}`, // 临时ID
    uuid: null, // 后端会话UUID（首次发送消息时获取）
    title: '新的对话',
    messages: [],
    messageCount: 0,
    createdAt: Date.now(),
    lastMessageTime: Date.now()
  }
  
  conversations.value.unshift(newConv)
  currentConversation.value = newConv
  
  ElMessage.success('已创建新对话')
  
  return newConv
}

// 选择对话
// ✅ 选择会话，从后端加载消息
const selectConversation = async (conv) => {
  try {
    // 如果会话已经有消息，直接切换
    if (conv.messages && conv.messages.length > 0) {
      currentConversation.value = conv
      nextTick(() => {
        scrollToBottom()
      })
      return
    }
    
    // 从后端加载会话消息
    loading.value = true
    const response = await getConversationMessages(conv.uuid)
    
    if (response.success && response.data && response.data.messages) {
      // 转换消息格式
      conv.messages = response.data.messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.created_at).getTime()
      }))
      
      currentConversation.value = conv
      nextTick(() => {
        scrollToBottom()
      })
      
      console.log(`✅ 已加载会话消息: ${conv.messages.length}条`)
    } else {
      throw new Error(response.message || '加载消息失败')
    }
  } catch (error) {
    console.error('加载会话消息失败:', error)
    ElMessage.error('加载会话消息失败')
    // 即使失败也切换到该会话
    currentConversation.value = conv
  } finally {
    loading.value = false
  }
}

// 对话操作
const handleConvAction = async (command, conv) => {
  if (command === 'rename') {
    ElMessageBox.prompt('请输入新的对话名称', '重命名对话', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: conv.title,
      inputPattern: /.+/,
      inputErrorMessage: '对话名称不能为空'
    }).then(({ value }) => {
      conv.title = value
      saveConversations()
      ElMessage.success('重命名成功')
    }).catch(() => {})
  } else if (command === 'delete') {
    ElMessageBox.confirm(
      '确定要删除这个对话吗？删除后无法恢复。',
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).then(() => {
      const index = conversations.value.findIndex(c => c.id === conv.id)
      if (index !== -1) {
        conversations.value.splice(index, 1)
      }
      if (currentConversation.value?.id === conv.id) {
        currentConversation.value = null
      }
      saveConversations()
      ElMessage.success('已删除对话')
    }).catch(() => {})
  }
}

// 清空当前对话
const clearCurrentConversation = () => {
  ElMessageBox.confirm(
    '确定要清空当前对话的所有消息吗？',
    '清空确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    if (currentConversation.value) {
      currentConversation.value.messages = []
      currentConversation.value.messageCount = 0
      saveConversations()
      ElMessage.success('已清空对话')
    }
  }).catch(() => {})
}

// 发送消息
const handleSend = async () => {
  const message = inputMessage.value.trim()
  if (!message || isThinking.value) return
  
  // 独立学习助手页面场景：不允许在这里创建新对话，必须从课程内发起
  if (!currentConversation.value) {
    ElMessage.info('请先在侧边栏选择一个历史对话，或从课程学习页面发起新提问')
    return
  }

  // 添加用户消息
  const userMessage = {
    role: 'user',
    content: message,
    timestamp: Date.now()
  }

  currentConversation.value.messages.push(userMessage)
  currentConversation.value.messageCount++
  currentConversation.value.lastMessageTime = Date.now()

  inputMessage.value = ''
  isThinking.value = true

  await nextTick()
  scrollToBottom()

  try {
    const context = {
      // 独立页面场景：通用学习问题，不传递课程上下文
      // course_uuid: null,
      // unit_uuid: null
    }

    const response = await chatWithAssistant({
      message: message,
      conversation_id: currentConversation.value.uuid,
      context: context
    })

    if (response.success && response.data) {
      // 更新会话UUID（第一次发送时后端会创建）
      if (response.data.conversation_id && !currentConversation.value.uuid) {
        currentConversation.value.uuid = response.data.conversation_id
        currentConversation.value.id = response.data.conversation_id
      }

      // 更新会话标题（如果后端返回了智能标题）
      if (response.data.suggested_title && currentConversation.value.title === '新的对话') {
        currentConversation.value.title = response.data.suggested_title
      }

      // 添加AI回复
      const aiMessage = {
        role: 'assistant',
        content: response.data.response,
        timestamp: Date.now(),
        message_id: response.data.message_id,
        token_usage: response.data.token_usage,
        knowledge_sources: response.data.knowledge_sources || []
      }

      currentConversation.value.messages.push(aiMessage)
      currentConversation.value.messageCount++
      currentConversation.value.lastMessageTime = Date.now()

      // 更新会话列表（无需保存到localStorage）
      const convIndex = conversations.value.findIndex(c => c.id === currentConversation.value.id)
      if (convIndex !== -1) {
        conversations.value[convIndex] = { ...currentConversation.value }
      }

      if (response.data.blocked) {
        ElMessage.warning('您的消息包含敏感内容，已被系统拦截。')
      }
    } else {
      ElMessage.error(response.message || 'AI助手服务异常')
      // 如果AI回复失败，移除用户消息
      currentConversation.value.messages.pop()
      currentConversation.value.messageCount--
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败，请稍后再试。')
    // 如果AI回复失败，移除用户消息
    currentConversation.value.messages.pop()
    currentConversation.value.messageCount--
  } finally {
    isThinking.value = false
    nextTick(() => {
      scrollToBottom()
    })
  }
}

// 生成模拟回复（后端实现后替换）
const generateMockResponse = (userMessage) => {
  const responses = [
    '这是一个很好的问题！让我来帮你分析一下。\n\n首先，我们需要理解这个概念的核心要点...',
    '我理解你的困惑。让我用一个简单的例子来解释：\n\n想象一下...',
    '关于这个问题，我建议你可以从以下几个方面入手：\n\n1. 首先...\n2. 其次...\n3. 最后...',
    '很高兴能帮助你！根据我的理解，这个知识点的关键在于...',
    '这个问题涉及到几个重要概念。让我们一步步来看：\n\n**第一步**：...'
  ]
  return responses[Math.floor(Math.random() * responses.length)]
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 格式化消息内容（Markdown）
const formatMessage = (content) => {
  try {
    const html = marked.parse(content || '')
    return DOMPurify.sanitize(html)
  } catch (error) {
    return content
  }
}

// 时间格式化
const formatTime = (timestamp) => {
  const now = Date.now()
  const diff = now - timestamp
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return formatDate(timestamp)
}

const formatDate = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) {
    return '昨天'
  }
  
  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

const formatMessageTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 数据持久化
// ⚠️ 已弃用：数据现在保存在后端，不再使用localStorage
const saveConversations = () => {
  // 保留空函数以兼容旧代码
  // 所有数据现在通过API自动保存到后端
}

// ✅ 从后端API加载会话列表（初始加载）
const loadConversations = async () => {
  try {
    loading.value = true
    page.value = 1
    hasMore.value = true
    
    const response = await getConversations({
      page: page.value,
      pageSize: pageSize.value
    })
    
    if (response.success && response.data) {
      const items = response.data.items || []
      const total = response.data.total || 0
      
      // 转换后端数据格式为前端格式
      conversations.value = items.map(conv => ({
        id: conv.uuid,
        uuid: conv.uuid,
        title: conv.title || '新的对话',
        messageCount: conv.message_count || 0,
        lastMessageTime: conv.last_message_at ? new Date(conv.last_message_at).getTime() : Date.now(),
        messages: [], // 消息按需加载
        course_uuid: conv.course_uuid,
        course_name: conv.course_name,
        unit_uuid: conv.unit_uuid,
        unit_name: conv.unit_name,
      }))
      
      // 判断是否还有更多数据
      hasMore.value = conversations.value.length < total
      
      console.log(`✅ 已加载 ${conversations.value.length}/${total} 个会话`)
    } else {
      console.warn('加载会话失败:', response.message)
      conversations.value = []
    }
  } catch (error) {
    console.error('加载对话失败:', error)
    ElMessage.error('加载对话历史失败')
    conversations.value = []
  } finally {
    loading.value = false
  }
}

// ✅ 加载更多会话（滚动加载）
const loadMoreConversations = async () => {
  if (loadingMore.value || !hasMore.value) return
  
  try {
    loadingMore.value = true
    const nextPage = page.value + 1
    
    const response = await getConversations({
      page: nextPage,
      pageSize: pageSize.value
    })
    
    if (response.success && response.data) {
      const items = response.data.items || []
      const total = response.data.total || 0
      
      if (items.length > 0) {
        // 转换为前端格式并追加
        const newConvs = items.map(conv => ({
          id: conv.uuid,
          uuid: conv.uuid,
          title: conv.title || '新的对话',
          messageCount: conv.message_count || 0,
          lastMessageTime: conv.last_message_at ? new Date(conv.last_message_at).getTime() : Date.now(),
          messages: [],
          course_uuid: conv.course_uuid,
          course_name: conv.course_name,
          unit_uuid: conv.unit_uuid,
          unit_name: conv.unit_name,
        }))
        
        conversations.value = [...conversations.value, ...newConvs]
        page.value = nextPage
        
        // 判断是否还有更多
        hasMore.value = conversations.value.length < total
      } else {
        hasMore.value = false
      }
    }
  } catch (error) {
    console.error('加载更多对话失败:', error)
  } finally {
    loadingMore.value = false
  }
}

// 监听列表滚动
const handleListScroll = (e) => {
  const { scrollTop, scrollHeight, clientHeight } = e.target
  // 距离底部 50px 时加载更多
  if (scrollHeight - scrollTop - clientHeight < 50) {
    loadMoreConversations()
  }
}

// 清空所有对话记录
const handleClearAll = () => {
  ElMessageBox.confirm(
    '确定要清空所有的对话记录吗？此操作不可撤销（记录将在历史列表中隐藏）。',
    '清空全部确认',
    {
      confirmButtonText: '确定清空',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      const response = await clearAllConversations()
      if (response.success) {
        ElMessage.success(response.message || '已清空所有对话')
        conversations.value = []
        currentConversation.value = null
        hasMore.value = false
        page.value = 1
      } else {
        ElMessage.error(response.message || '清空失败')
      }
    } catch (error) {
      console.error('清空对话失败:', error)
      ElMessage.error('清空对话请求失败')
    }
  }).catch(() => {})
}

// ===== 生命周期 =====
onMounted(() => {
  loadConversations()
  
  // 配置marked
  marked.setOptions({
    breaks: true,
    gfm: true
  })
})

// 监听对话变化，自动保存
watch(() => currentConversation.value, () => {
  if (currentConversation.value) {
    localStorage.setItem('learning_assistant_current', currentConversation.value.id)
  }
}, { deep: true })
</script>

<style scoped>
.learning-assistant {
  display: flex;
  height: calc(100vh - 110px); /* 适配顶部导航和页面内边距，确保不产生全局滚动条 */
  background: #f5f7fa;
  overflow: hidden;
}

/* ========== 侧边栏样式 ========== */
.sidebar {
  width: 280px;
  background: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar-header {
  height: 60px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e4e7ed;
}

.assistant-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
}

.brand-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.sidebar-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.new-chat-btn {
  width: 100%;
  margin-bottom: 16px;
  height: 44px;
  font-size: 15px;
}

.search-wrapper {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-input {
  flex: 1;
}

.clear-all-btn {
  color: #909399;
  transition: all 0.3s;
}

.clear-all-btn:hover {
  color: #f56c6c;
  background-color: #fef0f0 !important;
}

.list-loading-more,
.list-no-more {
  padding: 16px;
  text-align: center;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.search-input :deep(.el-input__wrapper) {
  background-color: #f5f7fa;
  box-shadow: none !important;
  border: 1px solid transparent;
  border-radius: 8px;
  transition: all 0.2s;
}

.search-input :deep(.el-input__wrapper):hover {
  border-color: #dcdfe6;
}

.search-input :deep(.el-input__wrapper).is-focus {
  background-color: white;
  border-color: #409eff;
}

.conversations-list {
  flex: 1;
  overflow-y: auto;
  margin: 0 -16px;
  padding: 0 16px;
}

.list-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 12px;
  color: #909399;
  padding: 8px 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.conversation-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.conversation-item:hover {
  background: #f5f7fa;
}

.conversation-item.active {
  background: #ecf5ff;
  border-left: 3px solid #409eff;
}

.conv-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.conv-icon {
  width: 32px;
  height: 32px;
  background: #f0f2f5;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #606266;
  flex-shrink: 0;
}

.conversation-item.active .conv-icon {
  background: #409eff;
  color: white;
}

.conv-info {
  flex: 1;
  min-width: 0;
}

.conv-title {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.conv-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.conv-divider {
  color: #dcdfe6;
}

.conv-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0 6px;
  border-radius: 4px;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-tag.course {
  background-color: #f0f9eb;
  color: #67c23a;
}

.conversation-item.active .conv-tag.course {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.conv-actions {
  opacity: 0;
  transition: opacity 0.2s;
}

.conversation-item:hover .conv-actions {
  opacity: 1;
}

.empty-conversations {
  padding: 40px 20px;
  text-align: center;
}

/* ========== 主内容区样式 ========== */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 欢迎界面 */
.welcome-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  overflow-y: auto;
}

.welcome-content {
  max-width: 800px;
  text-align: center;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 24px;
  color: #667eea;
}

.welcome-title {
  font-size: 32px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px 0;
}

.welcome-subtitle {
  font-size: 18px;
  color: #606266;
  margin: 0 0 48px 0;
}

.welcome-features {
  display: flex;
  justify-content: center;
  gap: 32px;
  padding-top: 32px;
  border-top: 1px solid #e4e7ed;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

/* 对话容器 */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  overflow: hidden;
}

.chat-header {
  height: 64px;
  padding: 0 24px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.chat-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.chat-info {
  font-size: 14px;
  color: #909399;
}

.header-context {
  display: flex;
  align-items: center;
  gap: 12px;
}

.context-divider {
  color: #dcdfe6;
  font-weight: 300;
}

.course-tag {
  border: none;
  background-color: #f4f4f5;
  color: #606266;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 8px;
  height: 24px;
}

/* 消息列表 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f5f7fa;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  animation: messageSlideIn 0.3s ease;
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.message-item.user .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message-item.assistant .message-avatar {
  background: #f0f2f5;
  color: #409eff;
}

.message-content {
  flex: 1;
  max-width: 70%;
}

.message-item.user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-text {
  background: white;
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  line-height: 1.8;
  color: #303133;
  font-size: 15px;
  word-wrap: break-word;
}

.message-item.user .message-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* Markdown 样式 */
.message-text :deep(p) {
  margin: 0 0 8px 0;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(code) {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 14px;
}

.message-text :deep(pre) {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-text :deep(strong) {
  font-weight: 600;
}

.knowledge-sources {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.message-meta {
  margin-top: 8px;
}

.message-time {
  font-size: 12px;
  color: #909399;
}

/* 思考动画 */
.thinking-animation {
  display: flex;
  gap: 6px;
  padding: 16px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.thinking-animation span {
  width: 8px;
  height: 8px;
  background: #409eff;
  border-radius: 50%;
  animation: thinking 1.4s infinite;
}

.thinking-animation span:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-animation span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes thinking {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1.2);
    opacity: 1;
  }
}

/* 输入区域 */
.input-container {
  padding: 20px 24px;
  background: white;
  border-top: 1px solid #e4e7ed;
}

.input-wrapper {
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  gap: 12px;
  margin-bottom: 8px;
  width: 100%;
}

.message-input {
  flex: 1;
  min-width: 0; /* 防止 flex 子元素溢出 */
}

.message-input :deep(.el-textarea__inner) {
  border: 1px solid #dcdfe6;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 15px;
  resize: none;
  transition: all 0.3s;
}

.message-input :deep(.el-textarea__inner):focus {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
}

.send-btn {
  padding: 10px 24px;
  height: 40px;
  font-size: 15px;
  border-radius: 20px;
  flex-shrink: 0; /* 确保按钮不会被挤压 */
  margin-bottom: 4px; /* 对齐微调 */
}

.input-hint {
  font-size: 12px;
  color: #909399;
  text-align: center;
}

/* 滚动条样式 */
.conversations-list::-webkit-scrollbar,
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.conversations-list::-webkit-scrollbar-thumb,
.messages-container::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.conversations-list::-webkit-scrollbar-thumb:hover,
.messages-container::-webkit-scrollbar-thumb:hover {
  background: #c0c4cc;
}
</style>

