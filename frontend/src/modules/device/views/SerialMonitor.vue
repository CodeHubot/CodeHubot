<template>
  <div class="serial-monitor-page">
    <el-card class="monitor-card">
      <template #header>
        <div class="card-header">
          <h2>📟 串口监视器</h2>
          <p class="subtitle">实时查看和调试串口通信数据（完整支持中文）</p>
        </div>
      </template>

      <!-- 警告提示 -->
      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px;"
      >
        <template #title>
          <strong>使用说明</strong>
        </template>
        <div>
          <p style="margin: 0 0 8px 0;">
            <strong>🔒 协议要求：</strong>必须使用 HTTPS 访问（或在 localhost 运行）
          </p>
          <p style="margin: 0 0 8px 0;">
            <strong>🌐 浏览器要求：</strong>Chrome (≥89)、Edge (≥89) 或 Opera
          </p>
          <p style="margin: 0;">
            <strong>✨ 功能特点：</strong>完整支持中文显示、可调波特率、实时数据监控
          </p>
        </div>
      </el-alert>

      <!-- 连接控制区 -->
      <el-card class="control-card" shadow="never">
        <div class="control-section">
          <el-row :gutter="16">
            <!-- 连接状态 -->
            <el-col :span="8">
              <div :class="['status-indicator', { connected: isConnected }]">
                <div class="status-dot"></div>
                <span class="status-text">
                  {{ isConnected ? '已连接' : '未连接' }}
                </span>
              </div>
            </el-col>

            <!-- 波特率选择 -->
            <el-col :span="8">
              <el-select 
                v-model="baudRate" 
                :disabled="isConnected"
                placeholder="波特率"
                style="width: 100%;"
              >
                <el-option label="9600" :value="9600" />
                <el-option label="19200" :value="19200" />
                <el-option label="38400" :value="38400" />
                <el-option label="57600" :value="57600" />
                <el-option label="115200" :value="115200" />
                <el-option label="230400" :value="230400" />
                <el-option label="460800" :value="460800" />
                <el-option label="921600" :value="921600" />
              </el-select>
            </el-col>

            <!-- 连接按钮 -->
            <el-col :span="8">
              <el-button 
                v-if="!isConnected"
                type="primary" 
                style="width: 100%;"
                @click="handleConnect"
              >
                <el-icon><Link /></el-icon>
                连接设备
              </el-button>
              <el-button 
                v-else
                type="danger" 
                style="width: 100%;"
                @click="handleDisconnect"
              >
                <el-icon><Close /></el-icon>
                断开连接
              </el-button>
            </el-col>
          </el-row>
        </div>
      </el-card>

      <!-- 数据监视区 -->
      <el-card class="monitor-display-card" shadow="never">
        <template #header>
          <div class="section-header">
            <div class="section-title">
              <el-icon><Monitor /></el-icon>
              <span>接收数据</span>
              <el-tag v-if="isConnected" type="success" size="small" style="margin-left: 10px;">
                实时监控中
              </el-tag>
            </div>
            <div class="header-actions">
              <el-switch
                v-model="autoScroll"
                active-text="自动滚动"
                style="margin-right: 15px;"
              />
              <el-switch
                v-model="showTimestamp"
                active-text="显示时间戳"
                style="margin-right: 15px;"
              />
              <el-switch
                v-model="hexMode"
                active-text="十六进制"
                style="margin-right: 15px;"
              />
              <el-button 
                size="small" 
                @click="clearReceiveData"
              >
                清空
              </el-button>
            </div>
          </div>
        </template>

        <div class="monitor-container" ref="monitorRef">
          <div 
            v-for="(line, index) in receiveBuffer" 
            :key="index"
            class="monitor-line"
          >
            <span v-if="showTimestamp" class="timestamp">{{ line.timestamp }}</span>
            <span class="data-content" :class="{ 'hex-mode': hexMode }">{{ line.data }}</span>
          </div>
          <div v-if="receiveBuffer.length === 0" class="monitor-empty">
            等待接收数据...
          </div>
        </div>

        <!-- 统计信息 -->
        <div class="stats-bar">
          <span>接收行数: {{ receiveBuffer.length }}</span>
          <span>接收字节: {{ totalBytes }}</span>
          <span>速率: {{ dataRate }} B/s</span>
        </div>
      </el-card>

      <!-- 发送数据区 -->
      <el-card class="send-card" shadow="never">
        <template #header>
          <div class="section-title">
            <el-icon><Position /></el-icon>
            <span>发送数据</span>
          </div>
        </template>

        <div class="send-section">
          <el-row :gutter="12">
            <el-col :span="18">
              <el-input
                v-model="sendText"
                placeholder="输入要发送的数据（支持中文）"
                :disabled="!isConnected"
                @keyup.enter="handleSend"
              >
                <template #prepend>
                  <el-select v-model="lineEnding" style="width: 100px;">
                    <el-option label="无" value="none" />
                    <el-option label="换行 (\\n)" value="lf" />
                    <el-option label="回车 (\\r)" value="cr" />
                    <el-option label="回车换行 (\\r\\n)" value="crlf" />
                  </el-select>
                </template>
              </el-input>
            </el-col>
            <el-col :span="6">
              <el-button 
                type="primary" 
                style="width: 100%;"
                :disabled="!isConnected || !sendText"
                @click="handleSend"
              >
                <el-icon><Promotion /></el-icon>
                发送
              </el-button>
            </el-col>
          </el-row>

          <!-- 快捷发送按钮 -->
          <div class="quick-send-section">
            <span class="quick-send-label">快捷命令：</span>
            <el-button 
              v-for="cmd in quickCommands" 
              :key="cmd.label"
              size="small"
              :disabled="!isConnected"
              @click="quickSend(cmd.value)"
            >
              {{ cmd.label }}
            </el-button>
            <el-button 
              size="small"
              type="success"
              plain
              @click="showAddCommandDialog = true"
            >
              <el-icon><Plus /></el-icon>
              添加
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- 高级设置 -->
      <el-card class="advanced-card" shadow="never">
        <template #header>
          <div class="section-title">
            <el-icon><Setting /></el-icon>
            <span>高级设置</span>
          </div>
        </template>

        <el-row :gutter="16}>
          <el-col :span="8">
            <el-form-item label="数据位">
              <el-select v-model="dataBits" :disabled="isConnected" style="width: 100%;">
                <el-option label="7" :value="7" />
                <el-option label="8" :value="8" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="停止位">
              <el-select v-model="stopBits" :disabled="isConnected" style="width: 100%;">
                <el-option label="1" :value="1" />
                <el-option label="2" :value="2" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="校验位">
              <el-select v-model="parity" :disabled="isConnected" style="width: 100%;">
                <el-option label="无" value="none" />
                <el-option label="奇校验" value="odd" />
                <el-option label="偶校验" value="even" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="最大缓冲行数">
              <el-input-number 
                v-model="maxBufferLines" 
                :min="100" 
                :max="10000" 
                :step="100"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="字符编码">
              <el-select v-model="encoding" style="width: 100%;">
                <el-option label="UTF-8" value="utf-8" />
                <el-option label="GBK" value="gbk" />
                <el-option label="ASCII" value="ascii" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-card>
    </el-card>

    <!-- 添加快捷命令对话框 -->
    <el-dialog
      v-model="showAddCommandDialog"
      title="添加快捷命令"
      width="500px"
    >
      <el-form :model="newCommand" label-width="80px">
        <el-form-item label="命令名称">
          <el-input v-model="newCommand.label" placeholder="例如：重启设备" />
        </el-form-item>
        <el-form-item label="命令内容">
          <el-input 
            v-model="newCommand.value" 
            type="textarea"
            :rows="3"
            placeholder="例如：restart"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddCommandDialog = false">取消</el-button>
        <el-button type="primary" @click="addQuickCommand">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Link, Close, Monitor, Position, Promotion, Setting, Plus
} from '@element-plus/icons-vue'

// 连接状态
const isConnected = ref(false)
const port = ref(null)
const reader = ref(null)
const writer = ref(null)

// 串口配置
const baudRate = ref(115200)
const dataBits = ref(8)
const stopBits = ref(1)
const parity = ref('none')

// 显示配置
const autoScroll = ref(true)
const showTimestamp = ref(true)
const hexMode = ref(false)
const encoding = ref('utf-8')
const maxBufferLines = ref(1000)

// 数据缓冲
const receiveBuffer = ref([])
const totalBytes = ref(0)
const dataRate = ref(0)
const monitorRef = ref(null)

// 发送配置
const sendText = ref('')
const lineEnding = ref('crlf')
const quickCommands = ref([
  { label: '获取状态', value: 'status' },
  { label: '重启设备', value: 'restart' },
  { label: '获取版本', value: 'version' },
])

// 对话框
const showAddCommandDialog = ref(false)
const newCommand = ref({ label: '', value: '' })

// 读取循环控制
let reading = false
let readController = null
let rateInterval = null
let lastByteCount = 0

// TextDecoder 支持中文
const decoder = new TextDecoder('utf-8')
const textEncoder = new TextEncoder()

// 连接串口
const handleConnect = async () => {
  try {
    // 检查浏览器支持
    if (!('serial' in navigator)) {
      const isSecure = window.isSecureContext
      if (!isSecure) {
        ElMessage.error('Web Serial API 需要 HTTPS 协议！请使用 HTTPS 访问或在 localhost 运行')
      } else {
        ElMessage.error('您的浏览器不支持 Web Serial API，请使用 Chrome、Edge 或 Opera 浏览器')
      }
      return
    }

    // 请求串口访问
    port.value = await navigator.serial.requestPort({
      filters: [
        { usbVendorId: 0x303a }, // Espressif
        { usbVendorId: 0x10c4 }, // Silicon Labs (CP210x)
        { usbVendorId: 0x1a86 }, // QinHeng Electronics (CH340)
      ]
    })

    // 打开串口
    await port.value.open({
      baudRate: baudRate.value,
      dataBits: dataBits.value,
      stopBits: stopBits.value,
      parity: parity.value,
      flowControl: 'none'
    })

    isConnected.value = true
    
    // 获取读写流
    reader.value = port.value.readable.getReader()
    writer.value = port.value.writable.getWriter()

    // 开始读取数据
    startReading()
    
    // 启动速率统计
    startRateCalculation()

    ElMessage.success('串口连接成功')
    addLine('=== 串口已连接 ===', 'system')
  } catch (error) {
    ElMessage.error(`连接失败: ${error.message}`)
    console.error(error)
  }
}

// 断开连接
const handleDisconnect = async () => {
  try {
    reading = false
    
    // 停止速率统计
    if (rateInterval) {
      clearInterval(rateInterval)
      rateInterval = null
    }

    // 取消读取
    if (readController) {
      readController.abort()
    }

    // 释放读写流
    if (reader.value) {
      await reader.value.cancel()
      await reader.value.releaseLock()
      reader.value = null
    }

    if (writer.value) {
      await writer.value.releaseLock()
      writer.value = null
    }

    // 关闭串口
    if (port.value) {
      await port.value.close()
      port.value = null
    }

    isConnected.value = false
    dataRate.value = 0
    ElMessage.success('串口已断开')
    addLine('=== 串口已断开 ===', 'system')
  } catch (error) {
    ElMessage.error(`断开失败: ${error.message}`)
    console.error(error)
  }
}

// 开始读取数据
const startReading = async () => {
  reading = true
  readController = new AbortController()
  
  try {
    let partialData = ''
    
    while (reading && reader.value) {
      const { value, done } = await reader.value.read()
      
      if (done) {
        break
      }

      if (value) {
        totalBytes.value += value.length
        
        // 解码数据（支持中文）
        const text = decoder.decode(value, { stream: true })
        partialData += text

        // 按行分割
        const lines = partialData.split('\n')
        partialData = lines.pop() || '' // 保留未完成的行

        // 添加完整的行
        for (const line of lines) {
          if (line.trim()) {
            addLine(line.replace('\r', ''), 'data')
          }
        }
      }
    }
  } catch (error) {
    if (error.name !== 'AbortError') {
      console.error('读取错误:', error)
      addLine(`错误: ${error.message}`, 'error')
    }
  }
}

// 添加一行数据
const addLine = (data, type = 'data') => {
  const timestamp = new Date().toLocaleTimeString('zh-CN', { 
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3
  })

  let displayData = data
  if (hexMode.value && type === 'data') {
    // 转换为十六进制显示
    displayData = Array.from(textEncoder.encode(data))
      .map(b => b.toString(16).padStart(2, '0').toUpperCase())
      .join(' ')
  }

  receiveBuffer.value.push({
    timestamp,
    data: displayData,
    type
  })

  // 限制缓冲区大小
  if (receiveBuffer.value.length > maxBufferLines.value) {
    receiveBuffer.value.shift()
  }

  // 自动滚动到底部
  if (autoScroll.value) {
    nextTick(() => {
      if (monitorRef.value) {
        monitorRef.value.scrollTop = monitorRef.value.scrollHeight
      }
    })
  }
}

// 清空接收数据
const clearReceiveData = () => {
  receiveBuffer.value = []
  totalBytes.value = 0
}

// 发送数据
const handleSend = async () => {
  if (!isConnected.value || !writer.value || !sendText.value) {
    return
  }

  try {
    let dataToSend = sendText.value

    // 添加行尾符
    switch (lineEnding.value) {
      case 'lf':
        dataToSend += '\n'
        break
      case 'cr':
        dataToSend += '\r'
        break
      case 'crlf':
        dataToSend += '\r\n'
        break
    }

    // 编码并发送（支持中文）
    const encoded = textEncoder.encode(dataToSend)
    await writer.value.write(encoded)

    addLine(`>>> ${sendText.value}`, 'send')
    sendText.value = ''
    ElMessage.success('数据已发送')
  } catch (error) {
    ElMessage.error(`发送失败: ${error.message}`)
    console.error(error)
  }
}

// 快捷发送
const quickSend = (value) => {
  sendText.value = value
  handleSend()
}

// 添加快捷命令
const addQuickCommand = () => {
  if (!newCommand.value.label || !newCommand.value.value) {
    ElMessage.warning('请填写完整信息')
    return
  }

  quickCommands.value.push({ ...newCommand.value })
  
  // 保存到本地存储
  localStorage.setItem('serialMonitorQuickCommands', JSON.stringify(quickCommands.value))
  
  newCommand.value = { label: '', value: '' }
  showAddCommandDialog.value = false
  ElMessage.success('快捷命令已添加')
}

// 启动速率计算
const startRateCalculation = () => {
  lastByteCount = totalBytes.value
  rateInterval = setInterval(() => {
    const current = totalBytes.value
    dataRate.value = current - lastByteCount
    lastByteCount = current
  }, 1000)
}

// 监听十六进制模式切换，重新渲染数据
watch(hexMode, () => {
  // 简单刷新显示
  const oldBuffer = [...receiveBuffer.value]
  receiveBuffer.value = []
  nextTick(() => {
    receiveBuffer.value = oldBuffer
  })
})

// 组件挂载
onMounted(() => {
  // 加载保存的快捷命令
  const saved = localStorage.getItem('serialMonitorQuickCommands')
  if (saved) {
    try {
      quickCommands.value = JSON.parse(saved)
    } catch (e) {
      console.error('加载快捷命令失败:', e)
    }
  }

  // 检查浏览器支持
  if (!('serial' in navigator)) {
    addLine('❌ 浏览器不支持 Web Serial API', 'error')
    if (!window.isSecureContext) {
      addLine('⚠️ 原因：当前页面不是安全上下文（需要 HTTPS）', 'error')
    } else {
      addLine('⚠️ 请使用 Chrome、Edge 或 Opera 浏览器', 'error')
    }
  } else {
    addLine('✅ Web Serial API 可用，点击"连接设备"开始', 'system')
  }
})

// 组件卸载
onUnmounted(() => {
  if (isConnected.value) {
    handleDisconnect()
  }
})
</script>

<style scoped lang="scss">
.serial-monitor-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.monitor-card {
  .card-header {
    text-align: center;
    
    h2 {
      margin: 0 0 8px 0;
      font-size: 24px;
      color: #333;
    }
    
    .subtitle {
      margin: 0;
      font-size: 14px;
      color: #666;
    }
  }
}

.control-card,
.monitor-display-card,
.send-card,
.advanced-card {
  margin-bottom: 20px;
}

.control-section {
  .status-indicator {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 15px;
    background: #f5f7fa;
    border-radius: 4px;
    border: 2px solid #e4e7ed;
    height: 40px;
    transition: all 0.3s;
    
    &.connected {
      background: #f0f9ff;
      border-color: #67c23a;
    }
    
    .status-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: #f56c6c;
      animation: pulse 2s infinite;
    }
    
    .status-text {
      font-weight: 500;
      color: #606266;
    }
  }
  
  .status-indicator.connected .status-dot {
    background: #67c23a;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }
  
  .header-actions {
    display: flex;
    align-items: center;
  }
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.monitor-container {
  min-height: 400px;
  max-height: 600px;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 4px;
  padding: 15px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  
  .monitor-line {
    margin-bottom: 2px;
    word-wrap: break-word;
    
    .timestamp {
      color: #858585;
      margin-right: 10px;
      user-select: none;
    }
    
    .data-content {
      color: #d4d4d4;
      
      &.hex-mode {
        color: #4ec9b0;
        font-family: monospace;
      }
    }
  }
  
  .monitor-empty {
    text-align: center;
    color: #858585;
    padding: 50px 0;
    font-style: italic;
  }
}

.stats-bar {
  display: flex;
  justify-content: space-around;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-top: 10px;
  font-size: 13px;
  color: #606266;
  
  span {
    font-family: 'Consolas', monospace;
  }
}

.send-section {
  .quick-send-section {
    margin-top: 15px;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    
    .quick-send-label {
      font-size: 14px;
      color: #606266;
      font-weight: 500;
    }
  }
}

.advanced-card {
  :deep(.el-form-item) {
    margin-bottom: 10px;
  }
  
  :deep(.el-form-item__label) {
    font-size: 13px;
  }
}
</style>

