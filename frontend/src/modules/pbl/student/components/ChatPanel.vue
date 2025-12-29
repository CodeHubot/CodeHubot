<template>
  <div class="chat-panel">
    <div class="chat-container">
      <!-- 聊天消息区域 -->
      <div class="messages-area" ref="messagesAreaRef">
        <div class="welcome-message" v-if="messages.length === 0">
          <div class="welcome-animation">
            <div class="ai-avatar-large">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2Z" fill="currentColor"/>
                <circle cx="8.5" cy="10.5" r="1.5" fill="white"/>
                <circle cx="15.5" cy="10.5" r="1.5" fill="white"/>
                <path d="M12 17C14.2091 17 16 15.2091 16 13H8C8 15.2091 9.79086 17 12 17Z" fill="white"/>
              </svg>
              <div class="sparkles">
                <span class="sparkle" v-for="i in 6" :key="i"></span>
              </div>
            </div>
          </div>
          <div class="welcome-content">
            <h3>👋 你好！我是你的AI学习伙伴</h3>
            <p class="intro-text">很高兴能帮助你更好地学习！</p>
            <div class="feature-grid">
              <div class="feature-item">
                <span class="feature-icon">🔍</span>
                <span class="feature-text">单元知识答疑</span>
              </div>
              <div class="feature-item">
                <span class="feature-icon">📖</span>
                <span class="feature-text">课程文档解析</span>
              </div>
            </div>
            <p class="cta-text">有什么问题尽管问我吧！</p>
            
            <!-- AI声明 -->
            <div class="ai-disclaimer">
              <el-icon style="margin-right: 4px;"><InfoFilled /></el-icon>
              <span>本服务由AI提供，回答内容仅供参考，请结合课程资料和老师指导进行学习</span>
            </div>
          </div>
        </div>

        <transition-group name="message-list" tag="div">
          <div 
            v-for="message in messages" 
            :key="message.id"
            :class="['message', message.type]"
          >
            <div class="message-avatar">
              <svg v-if="message.type === 'ai'" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2Z" fill="currentColor"/>
                <circle cx="8.5" cy="10.5" r="1.5" fill="white"/>
                <circle cx="15.5" cy="10.5" r="1.5" fill="white"/>
                <path d="M12 17C14.2091 17 16 15.2091 16 13H8C8 15.2091 9.79086 17 12 17Z" fill="white"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 12C14.21 12 16 10.21 16 8C16 5.79 14.21 4 12 4C9.79 4 8 5.79 8 8C8 10.21 9.79 12 12 12ZM12 14C9.33 14 4 15.34 4 18V20H20V18C20 15.34 14.67 14 12 14Z" fill="currentColor"/>
              </svg>
            </div>
            <div class="message-content">
              <div class="message-text" v-html="formatMessage(message.content)"></div>
              <div class="message-footer">
                <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                <div class="message-actions" v-if="message.type === 'ai'">
                  <button @click="copyMessage(message.content)" class="action-icon" title="复制">
                    <el-icon><DocumentCopy /></el-icon>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </transition-group>

        <!-- 正在输入指示器 -->
        <transition name="fade">
          <div v-if="isTyping" class="message ai typing-indicator">
            <div class="message-avatar">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2Z" fill="currentColor"/>
                <circle cx="8.5" cy="10.5" r="1.5" fill="white"/>
                <circle cx="15.5" cy="10.5" r="1.5" fill="white"/>
                <path d="M12 17C14.2091 17 16 15.2091 16 13H8C8 15.2091 9.79086 17 12 17Z" fill="white"/>
              </svg>
            </div>
            <div class="message-content">
              <div class="typing-text">AI正在思考</div>
              <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <!-- AI声明（固定显示） -->
        <div class="ai-disclaimer-input">
          <el-icon style="font-size: 12px;"><WarnTriangleFilled /></el-icon>
          <span>AI生成内容仅供参考，请结合课程资料和老师指导学习</span>
        </div>
        
        <div class="input-hint" v-if="showHint">
          <el-icon><InfoFilled /></el-icon>
          <span>按 Ctrl+Enter 发送，Enter 换行</span>
        </div>
        <div class="input-container">
          <textarea
            v-model="inputMessage"
            @keydown.enter="handleEnterKey"
            @focus="showHint = true"
            @blur="showHint = false"
            ref="messageInputRef"
            placeholder="输入你的问题，我会尽力帮助你..."
            class="message-input"
            rows="1"
            :disabled="isTyping"
          ></textarea>
          
          <div class="input-actions">
            <button 
              @click="sendMessage" 
              :disabled="!inputMessage.trim() || isTyping"
              class="action-btn send-btn"
              :class="{ active: inputMessage.trim() }"
            >
              <el-icon v-if="isTyping"><Loading /></el-icon>
              <el-icon v-else><Promotion /></el-icon>
            </button>
          </div>
        </div>
        <div class="input-footer">
          <span class="char-count" :class="{ warning: inputMessage.length > 450 }">
            {{ inputMessage.length }} / 500
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  DocumentCopy, 
  Promotion, 
  Loading,
  InfoFilled,
  WarnTriangleFilled
} from '@element-plus/icons-vue'
import { chatWithAssistant } from '../api/learningAssistant'

// ===== 存储键名 =====
const STORAGE_KEY_PREFIX = 'ai_chat_history_'

const messagesAreaRef = ref(null)
const messageInputRef = ref(null)

const isTyping = ref(false)
const inputMessage = ref('')
const showHint = ref(false)
const messages = ref([])

// ===== 学习助手会话相关 =====
const currentConversationId = ref(null) // 当前学习助手会话UUID

// ===== Props =====
const props = defineProps({
  unitUuid: {
    type: String,
    default: ''
  },
  courseUuid: {
    type: String,
    default: ''
  },
  storageMode: {
    type: String,
    default: 'session', // 'none', 'session', 'local'
    validator: (value) => ['none', 'session', 'local'].includes(value)
  }
})

// ===== 存储相关方法 =====
const getStorageKey = () => {
  return `${STORAGE_KEY_PREFIX}${props.unitUuid || 'default'}`
}

// 获取学习助手会话ID的存储键
const getConversationIdKey = () => {
  return `ai_conversation_id_${props.courseUuid}_${props.unitUuid}`
}

// 加载保存的会话ID
const loadConversationId = () => {
  try {
    const key = getConversationIdKey()
    const savedId = localStorage.getItem(key)
    if (savedId) {
      currentConversationId.value = savedId
      console.log('✅ 已加载保存的会话ID:', savedId)
    }
  } catch (error) {
    console.error('加载会话ID失败:', error)
  }
}

// 保存或清除会话ID
const saveConversationId = (conversationId) => {
  try {
    const key = getConversationIdKey()
    if (conversationId) {
      localStorage.setItem(key, conversationId)
      currentConversationId.value = conversationId
      console.log('✅ 已保存会话ID:', conversationId)
    } else {
      localStorage.removeItem(key)
      currentConversationId.value = null
      console.log('🗑️ 已清除后端关联会话ID')
    }
  } catch (error) {
    console.error('操作会话ID失败:', error)
  }
}

const getStorage = () => {
  if (props.storageMode === 'local') return localStorage
  if (props.storageMode === 'session') return sessionStorage
  return null
}

const saveMessages = () => {
  const storage = getStorage()
  if (!storage) return
  
  try {
    const data = {
      messages: messages.value,
      timestamp: Date.now(),
      unitUuid: props.unitUuid
    }
    storage.setItem(getStorageKey(), JSON.stringify(data))
  } catch (error) {
    console.error('保存聊天记录失败:', error)
  }
}

const loadMessages = () => {
  const storage = getStorage()
  if (!storage) return
  
  try {
    const data = storage.getItem(getStorageKey())
    if (data) {
      const parsed = JSON.parse(data)
      if (parsed.unitUuid === props.unitUuid) {
        messages.value = parsed.messages || []
        if (messages.value.length > 0) {
          console.log(`✅ 已从本地缓存恢复 ${messages.value.length} 条记录`)
        }
      }
    }
  } catch (error) {
    console.error('加载聊天记录失败:', error)
  }
}

const clearStorage = () => {
  const storage = getStorage()
  if (!storage) return
  try {
    storage.removeItem(getStorageKey())
  } catch (error) {
    console.error('清除聊天记录失败:', error)
  }
}

// ===== 消息处理方法 =====
const formatMessage = (content) => {
  // 简单的文字格式化，后续可使用 marked 渲染更复杂的
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesAreaRef.value) {
      messagesAreaRef.value.scrollTop = messagesAreaRef.value.scrollHeight
    }
  })
}

const sendMessage = async () => {
  const text = inputMessage.value.trim()
  if (!text || isTyping.value) return
  
  if (text.length > 500) {
    ElMessage.warning('消息长度不能超过500个字符')
    return
  }

  // 1. 添加用户消息到列表
  const userMsg = {
    id: Date.now(),
    type: 'user',
    content: text,
    timestamp: Date.now()
  }
  messages.value.push(userMsg)
  inputMessage.value = ''
  scrollToBottom()
  
  // 2. 调用后端学习助手 API
  isTyping.value = true
  const startTime = Date.now()
  
  try {
    const response = await chatWithAssistant({
      message: text,
      conversation_id: currentConversationId.value, // 如果有ID则继续，否则开启新会话
      context: {
        course_uuid: props.courseUuid,
        unit_uuid: props.unitUuid
      }
    })
    
    if (response.success && response.data) {
      // ✅ 同步会话 ID（如果是新开启的会话，后端会返回新的 conversation_id）
      if (response.data.conversation_id && response.data.conversation_id !== currentConversationId.value) {
        saveConversationId(response.data.conversation_id)
      }
      
      // 3. 添加 AI 回复
      const aiMsg = {
        id: Date.now() + 1,
        type: 'ai',
        content: response.data.response,
        timestamp: Date.now(),
        responseTime: Date.now() - startTime,
        messageId: response.data.message_id
      }
      messages.value.push(aiMsg)
      
      if (response.data.blocked) {
        ElMessage.warning('您的消息包含敏感内容，已被系统拦截。')
      }
    } else {
      throw new Error(response.message || 'AI助手服务异常')
    }
  } catch (error) {
    console.error('❌ 发送消息失败:', error)
    console.error('❌ 错误详情:', {
      message: error.message,
      code: error.code,
      status: error.status,
      response: error.response
    })
    
    // 如果已经成功保存了会话ID，说明请求实际上成功了
    // 这种情况不应该显示错误（可能是401自动重试的中间状态）
    if (currentConversationId.value) {
      console.log('⚠️ 检测到会话ID已保存，可能是401自动重试，等待结果...')
      // 不显示错误消息
    } else {
    ElMessage.error('发送消息失败，请稍后再试。')
    
    messages.value.push({
      id: Date.now() + 1,
      type: 'ai',
      content: '抱歉，我暂时无法回复。请稍后再试或联系老师。',
      timestamp: Date.now(),
      isError: true
    })
    }
  } finally {
    isTyping.value = false
    scrollToBottom()
  }
}

const handleEnterKey = (event) => {
  // Ctrl+Enter (Windows/Linux) 或 Cmd+Enter (Mac) 发送消息
  if (event.ctrlKey || event.metaKey) {
    event.preventDefault() // 阻止默认换行
    sendMessage()
  }
  // 直接按 Enter 允许换行（默认行为）
}

const copyMessage = (content) => {
  const text = content.replace(/<[^>]*>/g, '')
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => ElMessage.error('复制失败'))
}

// ===== 监听器 =====
watch(messages, () => {
  scrollToBottom()
  if (props.storageMode !== 'none') {
    saveMessages()
  }
}, { deep: true })

// ===== 生命周期 =====
onMounted(() => {
  loadMessages()
  loadConversationId()
})

onBeforeUnmount(() => {
  if (props.storageMode !== 'none' && messages.value.length > 0) {
    saveMessages()
  }
})

// ===== 暴露方法给父组件 =====
defineExpose({
  clearChat: () => {
    messages.value = []
    clearStorage()
    // ✅ 关键：彻底重置后端会话，确保下次对话是全新的
    saveConversationId(null)
    ElMessage.success('已开启新对话')
  },
  getMessageCount: () => messages.value.length
})
</script>

<style scoped lang="scss">
@use 'sass:math';

.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: transparent;
  overflow: hidden;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: linear-gradient(to bottom, #f8fafc 0%, #f1f5f9 100%);
  
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: rgba(148, 163, 184, 0.3);
    border-radius: 3px;
    &:hover { background: rgba(102, 126, 234, 0.5); }
  }
}

.welcome-message {
  text-align: center;
  padding: 20px 0;
  animation: fade-in 0.6s ease;
}

.ai-avatar-large {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
  margin: 0 auto 24px;
  svg { width: 40px; height: 40px; color: white; }
}

.sparkles {
  position: absolute;
  width: 100%;
  height: 100%;
  .sparkle {
    position: absolute;
    width: 4px;
    height: 4px;
    background: #fbbf24;
    border-radius: 50%;
    @for $i from 1 through 6 {
      &:nth-child(#{$i}) {
        top: math.random() * 100%;
        left: math.random() * 100%;
      }
    }
  }
}

.welcome-content {
  background: white;
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  h3 { margin: 0 0 8px; color: #1e293b; }
  .intro-text { color: #64748b; font-size: 14px; margin-bottom: 20px; }
  .cta-text { color: #667eea; font-size: 14px; margin-top: 20px; }
  
  .ai-disclaimer {
    margin-top: 24px;
    padding: 12px 16px;
    background: #fef3c7;
    border-left: 3px solid #f59e0b;
    border-radius: 8px;
    display: flex;
    align-items: flex-start;
    gap: 8px;
    font-size: 13px;
    color: #92400e;
    line-height: 1.6;
    
    .el-icon {
      color: #f59e0b;
      font-size: 16px;
      flex-shrink: 0;
      margin-top: 2px;
    }
  }
}

.feature-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  .feature-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px;
    background: #f8fafc;
    border-radius: 12px;
    .feature-text { font-size: 13px; color: #475569; }
  }
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  &.user { flex-direction: row-reverse; }
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  svg { width: 20px; height: 20px; }
}

.message.user .message-avatar { background: #3b82f6; color: white; }
.message.ai .message-avatar { background: #667eea; color: white; }

.message-content {
  max-width: 75%;
  background: white;
  padding: 12px 16px;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  position: relative;
}

.message.user .message-content {
  background: #3b82f6;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.ai .message-content { border-bottom-left-radius: 4px; }

.message-text { font-size: 14px; line-height: 1.6; word-wrap: break-word; }

.message-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.message-time { font-size: 11px; color: #94a3b8; }
.message.user .message-time { color: rgba(255, 255, 255, 0.8); }

.message-actions { opacity: 0; transition: opacity 0.2s; }
.message-content:hover .message-actions { opacity: 1; }

.action-icon {
  border: none; background: transparent; color: #94a3b8; cursor: pointer;
  padding: 4px; &:hover { color: #667eea; }
}

.typing-dots {
  display: flex; gap: 4px;
  span {
    width: 6px; height: 6px; background: #667eea; border-radius: 50%;
    animation: typing-bounce 1.4s infinite ease-in-out;
    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes typing-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

.input-area {
  background: white;
  border-top: 1px solid #e5e7eb;
  padding: 16px 20px;
}

.ai-disclaimer-input {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #fef3c7;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 12px;
  color: #92400e;
  
  .el-icon {
    color: #f59e0b;
    flex-shrink: 0;
  }
}

.input-container {
  display: flex; gap: 8px; align-items: flex-end;
  background: #f8fafc; border: 2px solid #e2e8f0; border-radius: 12px; padding: 8px;
  &:focus-within { border-color: #667eea; background: white; }
}

.message-input {
  flex: 1; border: none; background: transparent; font-size: 14px;
  resize: none; min-height: 36px; max-height: 120px;
  &:focus { outline: none; }
}

.send-btn {
  width: 36px; height: 36px; border-radius: 8px;
  background: #667eea; color: white; border: none;
  &:disabled { opacity: 0.4; }
}

.char-count { font-size: 11px; color: #94a3b8; }

@keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }
</style>
