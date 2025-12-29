<template>
  <div class="chat-container">
    <!-- 智能体信息头部 -->
    <div class="chat-header">
      <div class="agent-info">
        <el-icon class="agent-icon"><ChatDotRound /></el-icon>
        <div class="agent-details">
          <h3>{{ agent?.name || '智能体' }}</h3>
          <p v-if="!agent">正在加载...</p>
          <p v-else>{{ agent.description || '暂无描述' }}</p>
        </div>
      </div>
      <div class="header-actions">
        <el-tag v-if="agent?.llm_model_name" type="success">
          <el-icon><TrendCharts /></el-icon>
          {{ agent?.llm_model_name }}
        </el-tag>
        <el-button @click="clearHistory" :disabled="messages.length === 0">
          <el-icon><Delete /></el-icon>
          清空对话
        </el-button>
        <el-button @click="goBack">
          <el-icon><Close /></el-icon>
          退出
        </el-button>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="messages-container" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-chat">
        <el-icon class="empty-icon"><ChatDotSquare /></el-icon>
        <p>开始与智能体对话吧！</p>
        <div class="quick-questions" v-if="suggestedQuestions.length > 0">
          <p class="quick-title">你可以这样问：</p>
          <el-button
            v-for="(question, index) in suggestedQuestions"
            :key="index"
            text
            @click="sendMessage(question)"
            class="quick-question"
          >
            {{ question }}
          </el-button>
        </div>
      </div>

      <div
        v-for="(message, index) in messages"
        :key="index"
        :class="['message-item', message.role]"
      >
        <div class="message-avatar">
          <el-icon v-if="message.role === 'user'"><User /></el-icon>
          <el-icon v-else><Cpu /></el-icon>
        </div>
        <div class="message-content">
          <div class="message-text" v-html="formatMessage(message.content)"></div>
          
          <!-- 知识库检索来源 -->
          <div v-if="message.knowledge_sources && message.knowledge_sources.length > 0" class="knowledge-sources">
            <div v-for="(source, idx) in message.knowledge_sources" :key="idx" class="knowledge-source-item">
              <el-alert type="success" :closable="false">
                <template #title>
                  <div class="knowledge-header">
                    <el-icon><Reading /></el-icon>
                    <span>检索知识库: {{ source.knowledge_base_name }}</span>
                    <el-tag size="small" type="success" style="margin-left: 8px;">命中</el-tag>
                  </div>
                </template>
                <div class="knowledge-source-details">
                  <div class="source-info">
                    <div class="source-header">
                      <el-tag size="small" type="primary">文档</el-tag>
                      <span class="source-title">《{{ source.document_title }}》</span>
                      <el-tag size="small" :type="getSimilarityType(source.similarity)">
                        相似度: {{ (source.similarity * 100).toFixed(1) }}%
                      </el-tag>
                    </div>
                    <div class="source-content">{{ source.chunk_content }}</div>
                    <div class="source-meta">文本块 #{{ source.chunk_index }}</div>
                  </div>
                </div>
              </el-alert>
            </div>
          </div>
          
          <!-- 插件调用信息 -->
          <div v-if="message.plugin_calls && message.plugin_calls.length > 0" class="plugin-calls">
            <div v-for="(call, idx) in message.plugin_calls" :key="idx" class="plugin-call-item">
              <el-alert type="info" :closable="false">
                <template #title>
                  <el-icon><Connection /></el-icon>
                  调用插件: {{ call.plugin_name }} - {{ call.function_name }}
                </template>
                <div class="plugin-call-details">
                  <div class="plugin-args">
                    <strong>调用参数：</strong>
                    <pre>{{ JSON.stringify(call.arguments, null, 2) }}</pre>
                  </div>
                  <div class="plugin-result">
                    <strong>执行结果：</strong>
                    <div>{{ call.result }}</div>
                  </div>
                </div>
              </el-alert>
            </div>
          </div>
          
          <!-- Token 使用量 -->
          <div v-if="message.token_usage" class="token-usage">
            <el-tag size="small" type="info">
              <el-icon><DataAnalysis /></el-icon>
              Token: {{ message.token_usage.total_tokens }} 
              (输入: {{ message.token_usage.prompt_tokens }}, 
              输出: {{ message.token_usage.completion_tokens }})
            </el-tag>
          </div>
          
          <div class="message-time">{{ formatTime(message.timestamp) }}</div>
        </div>
      </div>

      <div v-if="isThinking" class="message-item assistant thinking">
        <div class="message-avatar">
          <el-icon><Cpu /></el-icon>
        </div>
        <div class="message-content">
          <div class="thinking-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-container">
      <!-- 设备选择工具栏 -->
      <div class="input-toolbar">
        <div class="device-selector">
          <el-icon><Monitor /></el-icon>
          <span class="toolbar-label">控制设备：</span>
          <el-select
            v-model="selectedDeviceUuid"
            placeholder="选择要控制的设备"
            clearable
            filterable
            style="width: 300px;"
            :filter-method="filterDevices"
            @change="handleDeviceSelect"
          >
            <el-option
              v-for="device in filteredDevices"
              :key="device.uuid"
              :label="`${device.name}`"
              :value="device.uuid"
            >
              <div class="device-option">
                <span class="device-name">{{ device.name }}</span>
                <el-tag 
                  :type="device.is_online ? 'success' : 'info'" 
                  size="small"
                  style="margin-left: 8px;"
                >
                  {{ device.is_online ? '在线' : '离线' }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
          <span class="device-hint" v-if="selectedDevice">
            <el-icon><CircleCheck /></el-icon>
            已选择: {{ selectedDevice.name }}
          </span>
        </div>
      </div>

      <div class="input-wrapper">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          :placeholder="selectedDevice ? `向 ${selectedDevice.name} 发送指令... (Ctrl+Enter 发送)` : '输入消息... (Ctrl+Enter 发送)'"
          @keydown.ctrl.enter="handleSend"
          :disabled="isThinking"
          class="message-input"
        />
        <div class="input-actions">
          <el-button
            type="primary"
            @click="handleSend"
            :loading="isThinking"
            :disabled="!inputMessage.trim()"
            class="send-button"
          >
            <el-icon><Promotion /></el-icon>
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/store/user'
import {
  ChatDotRound,
  ChatDotSquare,
  User,
  Cpu,
  Connection,
  Delete,
  Close,
  TrendCharts,
  Promotion,
  Monitor,
  CircleCheck,
  DataAnalysis,
  Reading
} from '@element-plus/icons-vue'
import { getAgent } from '@/api/agent'
import { chatWithAgent, getMyDevices } from '@/api/chat'
import { marked } from 'marked'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const agentUuid = computed(() => route.params.uuid)
const agent = ref(null)
const messages = ref([])
const inputMessage = ref('')
const isThinking = ref(false)
const messagesContainer = ref(null)

// 设备选择相关
const devices = ref([])
const filteredDevices = ref([])
const selectedDeviceUuid = ref('')
const selectedDevice = computed(() => {
  return devices.value.find(d => d.uuid === selectedDeviceUuid.value)
})

// 建议问题
const suggestedQuestions = ref([
  '你好，请介绍一下自己',
  '你能帮我做什么？',
  '让我看看你的能力'
])

// 加载智能体信息
const loadAgent = async () => {
  try {
    const response = await getAgent(agentUuid.value)
    agent.value = response.data || response
    
    // 从提示词中提取建议问题
    if (agent.value.system_prompt) {
      // 可以根据提示词内容生成更智能的建议问题
      suggestedQuestions.value = [
        `你好，${agent.value.name}`,
        '你能帮我做什么？',
        '介绍一下你的功能'
      ]
    }
  } catch (error) {
    ElMessage.error('加载智能体信息失败')
    console.error(error)
  }
}

// 发送消息
const sendMessage = async (content) => {
  let messageText = content || inputMessage.value.trim()
  if (!messageText) return

  // 如果选择了设备，自动拼接设备UUID到消息中
  let finalMessage = messageText
  if (selectedDeviceUuid.value) {
    // 在消息前面添加设备标识，让智能体知道要操作哪个设备
    finalMessage = `[设备UUID: ${selectedDeviceUuid.value}] ${messageText}`
  }

  // 添加用户消息（显示原始消息，不显示UUID）
  const userMessage = {
    role: 'user',
    content: messageText,
    timestamp: new Date()
  }
  messages.value.push(userMessage)
  inputMessage.value = ''

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  // 调用 API（发送拼接了UUID的消息）
  isThinking.value = true
  try {
    const response = await chatWithAgent({
      agent_uuid: agentUuid.value,
      message: finalMessage,  // 发送拼接了UUID的消息
      history: messages.value.slice(0, -1).map(msg => ({
        role: msg.role,
        content: msg.content
      }))
    })

    const data = response.data || response

    // 添加助手回复
    const assistantMessage = {
      role: 'assistant',
      content: data.response || data.message,
      timestamp: new Date()
    }

    // 如果有函数调用信息
    if (data.function_call) {
      assistantMessage.function_call = data.function_call
    }
    
    // 添加插件调用信息
    if (data.plugin_calls && data.plugin_calls.length > 0) {
      assistantMessage.plugin_calls = data.plugin_calls
    }
    
    // 添加 Token 使用量
    if (data.token_usage) {
      assistantMessage.token_usage = data.token_usage
    }

    messages.value.push(assistantMessage)

    // 滚动到底部
    await nextTick()
    scrollToBottom()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '发送消息失败')
    console.error(error)
    // 移除失败的用户消息
    messages.value.pop()
  } finally {
    isThinking.value = false
  }
}

// 处理发送
const handleSend = () => {
  sendMessage()
}

// 清空历史
const clearHistory = () => {
  ElMessageBox.confirm(
    '确定要清空所有对话记录吗？',
    '确认清空',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    messages.value = []
    ElMessage.success('对话记录已清空')
  }).catch(() => {})
}

// 返回
const goBack = () => {
  router.push('/device/agents')
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 格式化消息（支持 Markdown）
const formatMessage = (content) => {
  try {
    return marked.parse(content || '')
  } catch (error) {
    return content
  }
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) {
    return '刚刚'
  } else if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
}

// 获取相似度标签类型
const getSimilarityType = (similarity) => {
  if (similarity >= 0.8) return 'success'
  if (similarity >= 0.7) return 'warning'
  return 'info'
}

// 加载用户设备列表（使用聊天专用接口）
const loadDevices = async () => {
  // 确保已登录才加载设备列表
  if (!userStore.token) {
    console.warn('未找到token，跳过设备列表加载')
    return
  }
  
  try {
    console.log('🔄 开始加载设备列表（使用聊天专用接口）')
    const response = await getMyDevices()
    const data = response.data || response
    devices.value = data || []
    filteredDevices.value = devices.value
    
    if (devices.value.length > 0) {
      console.log(`✅ 成功加载 ${devices.value.length} 个设备`)
    } else {
      console.log('📭 设备列表为空')
    }
  } catch (error) {
    // 静默失败，不影响聊天功能
    console.warn('设备列表加载失败，您仍可手动输入设备UUID:', error.response?.status)
    devices.value = []
    filteredDevices.value = []
  }
}

// 过滤设备
const filterDevices = (query) => {
  if (!query) {
    filteredDevices.value = devices.value
  } else {
    const lowerQuery = query.toLowerCase()
    filteredDevices.value = devices.value.filter(device => 
      device.name.toLowerCase().includes(lowerQuery) ||
      device.uuid.toLowerCase().includes(lowerQuery) ||
      (device.device_id && device.device_id.toLowerCase().includes(lowerQuery))
    )
  }
}

// 选择设备
const handleDeviceSelect = (uuid) => {
  selectedDeviceUuid.value = uuid
  
  if (uuid) {
    const device = devices.value.find(d => d.uuid === uuid)
    const deviceName = device ? device.name : '设备'
    ElMessage.success(`已选择${deviceName}`)
  }
}

onMounted(async () => {
  // 先加载智能体信息
  await loadAgent()
  
  // 延迟一小段时间，确保token已经准备好
  // 这样可以避免初始化时的竞争条件
  setTimeout(() => {
    loadDevices()
  }, 100)
})

// 监听路由参数变化，切换智能体时重新加载
watch(
  () => agentUuid.value,
  (newUuid, oldUuid) => {
    // 只有当 UUID 真正变化且新 UUID 有效时才重新加载
    if (oldUuid !== undefined && newUuid !== oldUuid && newUuid) {
      // 清空消息历史
      messages.value = []
      // 重新加载智能体信息
      loadAgent()
      // 清空已选设备
      selectedDeviceId.value = null
    }
  }
)
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  background: #f5f7fa;
}

.chat-header {
  background: white;
  padding: 16px 24px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.agent-details h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.agent-details p {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-chat p {
  font-size: 16px;
  margin-bottom: 24px;
}

.quick-questions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}

.quick-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.quick-question {
  font-size: 14px;
}

.message-item {
  display: flex;
  gap: 12px;
  animation: messageSlideIn 0.3s ease-out;
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
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 18px;
}

.message-item.user .message-avatar {
  background: #409eff;
  color: white;
}

.message-item.assistant .message-avatar {
  background: #67c23a;
  color: white;
}

.message-content {
  max-width: 70%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message-item.user .message-content {
  align-items: flex-end;
}

.message-text {
  background: white;
  padding: 16px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  word-wrap: break-word;
  line-height: 1.8;
  color: #303133;
  font-size: 15px;
  max-width: 100%;
  overflow-x: auto;
}

.message-item.user .message-text {
  background: #409eff;
  color: white;
}

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
}

.message-item.user .message-text :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}

.message-text :deep(pre) {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-text :deep(pre code) {
  background: none;
  padding: 0;
}

/* Markdown 列表样式 */
.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.message-text :deep(li) {
  margin: 4px 0;
  line-height: 1.8;
}

.message-text :deep(ul li) {
  list-style-type: disc;
}

.message-text :deep(ol li) {
  list-style-type: decimal;
}

.message-text :deep(ul ul),
.message-text :deep(ol ol) {
  margin: 4px 0;
}

/* Markdown 标题样式 */
.message-text :deep(h1),
.message-text :deep(h2),
.message-text :deep(h3),
.message-text :deep(h4),
.message-text :deep(h5),
.message-text :deep(h6) {
  margin: 16px 0 8px 0;
  font-weight: 600;
  line-height: 1.4;
}

.message-text :deep(h1) { font-size: 24px; }
.message-text :deep(h2) { font-size: 20px; }
.message-text :deep(h3) { font-size: 18px; }
.message-text :deep(h4) { font-size: 16px; }
.message-text :deep(h5) { font-size: 14px; }
.message-text :deep(h6) { font-size: 13px; }

/* Markdown 表格样式 */
.message-text :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
  font-size: 14px;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  overflow: hidden;
}

.message-text :deep(thead) {
  background: #f5f7fa;
}

.message-text :deep(th) {
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #e4e7ed;
  color: #303133;
}

.message-text :deep(td) {
  padding: 10px 12px;
  border-bottom: 1px solid #ebeef5;
  color: #606266;
}

.message-text :deep(tr:last-child td) {
  border-bottom: none;
}

.message-text :deep(tr:hover) {
  background: #fafafa;
}

/* Markdown 引用样式 */
.message-text :deep(blockquote) {
  border-left: 4px solid #409eff;
  padding: 8px 16px;
  margin: 12px 0;
  background: #f0f9ff;
  color: #606266;
  border-radius: 0 4px 4px 0;
}

.message-text :deep(blockquote p) {
  margin: 0;
}

/* Markdown 分割线样式 */
.message-text :deep(hr) {
  border: none;
  border-top: 1px solid #e4e7ed;
  margin: 16px 0;
}

/* Markdown 链接样式 */
.message-text :deep(a) {
  color: #409eff;
  text-decoration: none;
}

.message-text :deep(a:hover) {
  text-decoration: underline;
}

/* Markdown 强调样式 */
.message-text :deep(strong) {
  font-weight: 600;
  color: #303133;
}

.message-text :deep(em) {
  font-style: italic;
  color: #606266;
}

.function-call {
  margin-top: 8px;
}

.function-args {
  margin-top: 8px;
  font-size: 12px;
}

.function-args pre {
  margin: 0;
  background: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
}

.message-time {
  font-size: 12px;
  color: #909399;
}

.thinking {
  opacity: 0.8;
}

.thinking-dots {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.thinking-dots span {
  width: 8px;
  height: 8px;
  background: #909399;
  border-radius: 50%;
  animation: thinking 1.4s infinite;
}

.thinking-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-dots span:nth-child(3) {
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

.input-container {
  background: white;
  padding: 16px 24px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
}

.message-input {
  flex: 1;
}

.input-actions {
  position: absolute;
  bottom: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.send-button {
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
  transition: all 0.3s ease;
}

.send-button:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
  transform: translateY(-1px);
}

.send-button:active:not(:disabled) {
  transform: translateY(0);
}

.input-toolbar {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 12px;
}

.device-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.device-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.device-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 12px;
  color: #67c23a;
  font-size: 14px;
}

/* 知识库来源样式 */
.knowledge-sources {
  margin-top: 12px;
}

.knowledge-source-item {
  margin-bottom: 8px;
}

.knowledge-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
}

.knowledge-source-details {
  margin-top: 8px;
}

.source-info {
  padding: 8px 0;
}

.source-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.source-title {
  font-weight: 500;
  color: #303133;
  flex: 1;
}

.source-content {
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
  padding: 8px 0;
  border-top: 1px dashed #e4e7ed;
  border-bottom: 1px dashed #e4e7ed;
  margin: 8px 0;
  max-height: 120px;
  overflow-y: auto;
}

.source-meta {
  font-size: 12px;
  color: #909399;
  font-style: italic;
  margin-top: 4px;
}

.plugin-calls {
  margin-top: 12px;
}

.plugin-call-item {
  margin-bottom: 8px;
}

.plugin-call-details {
  margin-top: 8px;
}

.plugin-args,
.plugin-result {
  margin-bottom: 8px;
}

.plugin-args pre {
  background: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}

.plugin-result {
  color: #67c23a;
}

.token-usage {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>

