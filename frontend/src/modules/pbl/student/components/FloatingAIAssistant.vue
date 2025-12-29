<template>
  <div class="floating-ai-assistant">
    <!-- 悬浮按钮 -->
    <transition name="bounce">
      <button 
        v-show="!isExpanded"
        class="ai-fab"
        :class="{ pulse: showPulse, dragging: isDragging }"
        :style="fabStyle"
        @mousedown="startDrag"
        @touchstart="startDrag"
        @click="handleFabClick"
      >
        <div class="ai-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C7.59 20 4 16.41 4 12C4 7.59 7.59 4 12 4C16.41 4 20 7.59 20 12C20 16.41 16.41 20 12 20Z" fill="currentColor"/>
            <circle cx="8.5" cy="10.5" r="1.5" fill="currentColor"/>
            <circle cx="15.5" cy="10.5" r="1.5" fill="currentColor"/>
            <path d="M12 17C14.2091 17 16 15.2091 16 13H8C8 15.2091 9.79086 17 12 17Z" fill="currentColor"/>
          </svg>
        </div>
        <span class="ai-text">AI助手</span>
        
        <!-- 新消息提示 -->
        <span v-if="unreadCount > 0" class="unread-badge">{{ unreadCount }}</span>
        
        <!-- 拖拽提示 -->
        <span v-if="!isDragging" class="drag-hint">按住拖动</span>
      </button>
    </transition>

    <!-- 对话窗口 -->
    <transition name="slide-up">
      <div v-show="isExpanded" class="chat-window">
        <div class="chat-header">
          <div class="header-left">
            <div class="ai-avatar-small">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2Z" fill="currentColor"/>
                <circle cx="8.5" cy="10.5" r="1.5" fill="white"/>
                <circle cx="15.5" cy="10.5" r="1.5" fill="white"/>
                <path d="M12 17C14.2091 17 16 15.2091 16 13H8C8 15.2091 9.79086 17 12 17Z" fill="white"/>
              </svg>
            </div>
            <div class="header-info">
              <h3>AI学习助手</h3>
              <span class="status-text">
                <span class="status-dot" :class="{ online: isOnline }"></span>
                {{ isOnline ? '在线' : '离线' }}
              </span>
            </div>
          </div>
          
          <div class="header-actions">
            <button @click="minimizeChat" class="header-btn" title="最小化">
              <el-icon><Minus /></el-icon>
            </button>
            <button @click="closeChat" class="header-btn close-btn" title="关闭">
              <el-icon><Close /></el-icon>
            </button>
          </div>
        </div>

        <div class="chat-content">
          <ChatPanel 
            ref="chatPanelRef" 
            :unit-uuid="unitUuid"
            :course-uuid="courseUuid"
            :storage-mode="storageMode"
            :enable-server-sync="enableServerSync"
          />
        </div>
      </div>
    </transition>

    <!-- 遮罩层（可选） -->
    <transition name="fade">
      <div 
        v-show="isExpanded && showOverlay" 
        class="chat-overlay"
        @click="minimizeChat"
      ></div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { Close, Minus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ChatPanel from './ChatPanel.vue'

// ===== Props =====
const props = defineProps({
  showOverlay: {
    type: Boolean,
    default: false
  },
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
  },
  enableServerSync: {
    type: Boolean,
    default: true
  }
})

// ===== 响应式数据 =====
const isExpanded = ref(false)
const isOnline = ref(true)
const unreadCount = ref(0)
const showPulse = ref(true)
const isMinimized = ref(false)
const chatPanelRef = ref(null)

// 拖拽相关状态
const isDragging = ref(false)
const hasMoved = ref(false)  // 是否真的移动了
const fabPosition = ref({ bottom: 24, right: 24 })
const dragStart = ref({ x: 0, y: 0 })
const dragOffset = ref({ x: 0, y: 0 })
const dragThreshold = 5  // 移动超过5px才算拖拽

// 计算悬浮按钮的样式
const fabStyle = computed(() => {
  return {
    bottom: `${fabPosition.value.bottom}px`,
    right: `${fabPosition.value.right}px`,
  }
})

// ===== 拖拽方法 =====
const startDrag = (e) => {
  // 不要阻止默认行为，让点击事件可以正常触发
  
  hasMoved.value = false
  isDragging.value = false  // 先不设为true，等移动超过阈值再设
  
  // 获取初始鼠标/触摸位置
  const clientX = e.type === 'touchstart' ? e.touches[0].clientX : e.clientX
  const clientY = e.type === 'touchstart' ? e.touches[0].clientY : e.clientY
  
  dragStart.value = { x: clientX, y: clientY }
  dragOffset.value = { ...fabPosition.value }
  
  // 添加事件监听
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.addEventListener('touchmove', onDrag, { passive: false })
  document.addEventListener('touchend', stopDrag)
}

const onDrag = (e) => {
  // 获取当前鼠标/触摸位置
  const clientX = e.type === 'touchmove' ? e.touches[0].clientX : e.clientX
  const clientY = e.type === 'touchmove' ? e.touches[0].clientY : e.clientY
  
  // 计算移动距离
  const deltaX = clientX - dragStart.value.x
  const deltaY = clientY - dragStart.value.y
  const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY)
  
  // 只有移动超过阈值才算真正的拖拽
  if (distance > dragThreshold) {
    hasMoved.value = true
    isDragging.value = true
    
    // 阻止默认行为和点击事件
    e.preventDefault()
    e.stopPropagation()
    
    // 计算新位置（从视口右下角开始计算）
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight
    const buttonSize = 64 // 按钮大小
    
    // 新的 bottom 和 right 值
    let newBottom = dragOffset.value.bottom - deltaY
    let newRight = dragOffset.value.right - deltaX
    
    // 限制在视口范围内
    newBottom = Math.max(10, Math.min(viewportHeight - buttonSize - 10, newBottom))
    newRight = Math.max(10, Math.min(viewportWidth - buttonSize - 10, newRight))
    
    fabPosition.value = {
      bottom: newBottom,
      right: newRight
    }
  }
}

const stopDrag = (e) => {
  // 移除事件监听
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
  
  // 如果真的拖拽了（移动超过阈值），保存位置并阻止点击
  if (hasMoved.value && isDragging.value) {
    // 保存位置
    saveFabPosition()
    
    // 阻止点击事件触发
    e.preventDefault()
    e.stopPropagation()
    
    // 延迟重置拖拽状态
    setTimeout(() => {
      isDragging.value = false
      hasMoved.value = false
    }, 100)
  } else {
    // 没有移动或移动很小，重置状态，允许点击事件触发
    isDragging.value = false
    hasMoved.value = false
  }
}

const saveFabPosition = () => {
  try {
    localStorage.setItem('ai_fab_position', JSON.stringify(fabPosition.value))
  } catch (error) {
    console.error('保存按钮位置失败:', error)
  }
}

const loadFabPosition = () => {
  try {
    const saved = localStorage.getItem('ai_fab_position')
    if (saved) {
      fabPosition.value = JSON.parse(saved)
    }
  } catch (error) {
    console.error('加载按钮位置失败:', error)
  }
}

// ===== 方法 =====
const handleFabClick = (e) => {
  // 如果刚刚拖拽过，阻止点击
  if (hasMoved.value || isDragging.value) {
    e.preventDefault()
    e.stopPropagation()
    return
  }
  
  // 否则触发切换对话窗口
  toggleChat()
}

const toggleChat = () => {
  if (isMinimized.value) {
    // 如果是最小化状态，则恢复
    isMinimized.value = false
    isExpanded.value = true
  } else {
    // 否则切换展开状态
    isExpanded.value = !isExpanded.value
  }
  
  if (isExpanded.value) {
    unreadCount.value = 0
    showPulse.value = false
  }
}

const closeChat = () => {
  ElMessageBox.confirm(
    '确定要关闭AI助手吗？关闭后将清空当前对话记录。',
    '提示',
    {
      confirmButtonText: '确定关闭',
      cancelButtonText: '只是最小化',
      distinguishCancelAndClose: true,
      type: 'warning'
    }
  ).then(() => {
    // 用户选择关闭
    isExpanded.value = false
    isMinimized.value = false
    // 清空聊天记录
    if (chatPanelRef.value) {
      chatPanelRef.value.clearChat()
    }
    ElMessage.success('对话已清空')
  }).catch((action) => {
    // 用户选择最小化或取消
    if (action === 'cancel') {
      minimizeChat()
    }
  })
}

const minimizeChat = () => {
  isExpanded.value = false
  isMinimized.value = true
  ElMessage({
    message: 'AI助手已最小化，点击右下角按钮可恢复',
    type: 'info',
    duration: 2000
  })
}

// ===== 生命周期 =====
onMounted(() => {
  // 加载保存的按钮位置
  loadFabPosition()
  
  // 5秒后停止脉动动画
  setTimeout(() => {
    showPulse.value = false
  }, 5000)
})

onBeforeUnmount(() => {
  // 清理拖拽事件监听
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDrag)
  document.removeEventListener('touchend', stopDrag)
})

// ===== 定义可被父组件调用的方法 =====
defineExpose({
  openChat: () => {
    isExpanded.value = true
    isMinimized.value = false
    unreadCount.value = 0
  },
  closeChat,
  addUnreadCount: () => {
    if (!isExpanded.value) {
      unreadCount.value++
    }
  }
})
</script>

<style scoped lang="scss">
.floating-ai-assistant {
  position: fixed;
  bottom: 0;
  right: 0;
  z-index: 9999;
}

// ===== 悬浮按钮 =====
.ai-fab {
  position: fixed;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 
    0 4px 16px rgba(102, 126, 234, 0.4),
    0 8px 32px rgba(118, 75, 162, 0.3);
  cursor: move;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: white;
  transition: none;
  overflow: visible;
  z-index: 9999;
  user-select: none;
  touch-action: none;
  
  &::before {
    content: '';
    position: absolute;
    inset: -4px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    opacity: 0;
    transition: opacity 0.3s;
  }
  
  &:hover:not(.dragging) {
    transform: scale(1.05);
    box-shadow: 
      0 8px 24px rgba(102, 126, 234, 0.5),
      0 12px 40px rgba(118, 75, 162, 0.4);
    
    &::before {
      opacity: 0.3;
      animation: ripple 1s ease-out;
    }
    
    .drag-hint {
      opacity: 1;
    }
  }
  
  &.dragging {
    transform: scale(1.1);
    box-shadow: 
      0 12px 32px rgba(102, 126, 234, 0.6),
      0 16px 48px rgba(118, 75, 162, 0.5);
    cursor: grabbing;
  }
  
  &.pulse {
    animation: pulse 2s infinite;
  }
}

@keyframes ripple {
  0% {
    transform: scale(1);
    opacity: 0.3;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

.ai-icon {
  width: 28px;
  height: 28px;
  
  svg {
    width: 100%;
    height: 100%;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
  }
}

.ai-text {
  font-size: 10px;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  letter-spacing: 0.5px;
}

.unread-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: #ef4444;
  color: white;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.4);
  animation: bounce-in 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.drag-hint {
  position: absolute;
  top: -32px;
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 12px;
  background: rgba(0, 0, 0, 0.75);
  color: white;
  font-size: 11px;
  border-radius: 12px;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
  backdrop-filter: blur(4px);
  
  &::after {
    content: '';
    position: absolute;
    bottom: -4px;
    left: 50%;
    transform: translateX(-50%);
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid rgba(0, 0, 0, 0.75);
  }
}

// ===== 对话窗口 =====
.chat-window {
  position: fixed;
  bottom: 90px;
  right: 24px;
  width: 420px;
  height: 760px;
  max-height: calc(100vh - 110px);
  background: white;
  border-radius: 20px;
  box-shadow: 
    0 20px 60px rgba(102, 126, 234, 0.15),
    0 8px 24px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(102, 126, 234, 0.1);
  animation: float 3s ease-in-out infinite;
  z-index: 10000;
}

.chat-header {
  padding: 20px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
  position: relative;
  z-index: 10;
  flex-shrink: 0;
  
  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, 
      transparent 0%,
      rgba(255, 255, 255, 0.3) 50%,
      transparent 100%
    );
  }
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-avatar-small {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  
  svg {
    width: 24px;
    height: 24px;
  }
}

.header-info {
  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    line-height: 1.2;
  }
  
  .status-text {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    opacity: 0.9;
    margin-top: 4px;
  }
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ef4444;
  animation: blink 2s infinite;
  
  &.online {
    background: #10b981;
  }
}

.header-actions {
  display: flex;
  gap: 8px;
  position: relative;
  z-index: 20;
}

.header-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  position: relative;
  z-index: 30;
  pointer-events: auto;
  
  &:hover {
    background: rgba(255, 255, 255, 0.25);
    transform: scale(1.05);
  }
  
  &.close-btn:hover {
    background: rgba(239, 68, 68, 0.8);
  }
}

.chat-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

// ===== 遮罩层 =====
.chat-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(2px);
  z-index: 9998;
}

// ===== 动画 =====
@keyframes pulse {
  0%, 100% {
    box-shadow: 
      0 4px 16px rgba(102, 126, 234, 0.4),
      0 8px 32px rgba(118, 75, 162, 0.3),
      0 0 0 0 rgba(102, 126, 234, 0.7);
  }
  
  50% {
    box-shadow: 
      0 4px 16px rgba(102, 126, 234, 0.4),
      0 8px 32px rgba(118, 75, 162, 0.3),
      0 0 0 20px rgba(102, 126, 234, 0);
  }
}

@keyframes bounce-in {
  0% {
    transform: scale(0);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes blink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}

// ===== 过渡动画 =====
.bounce-enter-active {
  animation: bounce-in 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.bounce-leave-active {
  animation: bounce-in 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55) reverse;
}

.slide-up-enter-active {
  animation: slide-up 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-up-leave-active {
  animation: slide-up 0.2s cubic-bezier(0.4, 0, 0.2, 1) reverse;
}

@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(40px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// ===== 响应式设计 =====
@media (max-width: 768px) {
  .chat-window {
    width: calc(100vw - 32px);
    height: calc(100vh - 100px);
    bottom: 16px;
    right: 16px;
  }
  
  .ai-fab {
    bottom: 16px;
    right: 16px;
    width: 56px;
    height: 56px;
  }
  
  .ai-icon {
    width: 24px;
    height: 24px;
  }
}

@media (max-height: 700px) {
  .chat-window {
    height: calc(100vh - 80px);
  }
}
</style>
