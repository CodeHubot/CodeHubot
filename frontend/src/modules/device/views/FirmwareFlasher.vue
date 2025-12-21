<template>
  <div class="firmware-flasher-page">
    <el-card class="flasher-card">
      <template #header>
        <div class="card-header">
          <h2>🔧 ESP32 固件烧录工具</h2>
          <p class="subtitle">通过浏览器一键烧录固件，无需安装任何软件</p>
        </div>
      </template>

      <!-- 警告提示 -->
      <el-alert
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 20px;"
      >
        <template #title>
          <strong>重要提示</strong>
        </template>
        <div>
          <p style="margin: 0 0 8px 0;">
            <strong>🔒 必须使用 HTTPS 访问本页面</strong>（或在 localhost 运行）
          </p>
          <p style="margin: 0 0 8px 0;">
            <strong>🌐 浏览器要求：</strong>Chrome (≥89)、Edge (≥89) 或 Opera
          </p>
          <p style="margin: 0;">
            <strong>🔌 连接要求：</strong>使用 USB 数据线（非充电线）连接设备
          </p>
        </div>
      </el-alert>

      <!-- 连接状态 -->
      <div class="status-section">
        <el-card :class="['status-card', { connected: isConnected }]">
          <div class="status-indicator">
            <div class="status-dot"></div>
            <span class="status-text">
              {{ isConnected ? `已连接 - ${chipInfo}` : '未连接设备' }}
            </span>
          </div>
        </el-card>
      </div>

      <!-- 连接控制 -->
      <div class="control-section">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-button 
              type="primary" 
              size="large"
              style="width: 100%;"
              :disabled="isConnected"
              @click="handleConnect"
            >
              <el-icon><Link /></el-icon>
              连接设备
            </el-button>
          </el-col>
          <el-col :span="12">
            <el-button 
              size="large"
              style="width: 100%;"
              :disabled="!isConnected"
              @click="handleDisconnect"
            >
              <el-icon><Close /></el-icon>
              断开连接
            </el-button>
          </el-col>
        </el-row>
      </div>

      <!-- 固件选择 -->
      <el-card class="firmware-selector-card" shadow="never">
        <template #header>
          <div class="section-title">
            <el-icon><FolderOpened /></el-icon>
            <span>选择固件版本</span>
          </div>
        </template>
        
        <el-select 
          v-model="selectedFirmwareId" 
          placeholder="请选择固件版本"
          size="large"
          style="width: 100%;"
          @change="handleSelectFirmware"
        >
          <el-option
            v-for="firmware in firmwareList"
            :key="firmware.id"
            :label="`${firmware.name} (${firmware.date})`"
            :value="firmware.id"
          />
        </el-select>

        <!-- 固件信息 -->
        <div v-if="selectedFirmware" class="firmware-info">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="固件名称">{{ selectedFirmware.name }}</el-descriptions-item>
            <el-descriptions-item label="版本号">{{ selectedFirmware.version }}</el-descriptions-item>
            <el-descriptions-item label="发布日期">{{ selectedFirmware.date }}</el-descriptions-item>
            <el-descriptions-item label="文件大小">{{ selectedFirmware.size }}</el-descriptions-item>
            <el-descriptions-item label="说明">{{ selectedFirmware.description }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <el-alert
          type="info"
          :closable="false"
          show-icon
          style="margin-top: 15px;"
        >
          💡 固件文件已部署在服务器上，选择版本后直接烧录即可
        </el-alert>
      </el-card>

      <!-- 操作按钮 -->
      <div class="action-section">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-button 
              type="primary" 
              size="large"
              style="width: 100%;"
              :disabled="!isConnected || !selectedFirmware || isFlashing"
              :loading="isFlashing"
              @click="handleFlash"
            >
              <el-icon v-if="!isFlashing"><Upload /></el-icon>
              {{ isFlashing ? '烧录中...' : '开始烧录' }}
            </el-button>
          </el-col>
          <el-col :span="12">
            <el-button 
              type="danger" 
              size="large"
              style="width: 100%;"
              :disabled="!isConnected || isFlashing"
              @click="handleErase"
            >
              <el-icon><Delete /></el-icon>
              擦除Flash
            </el-button>
          </el-col>
        </el-row>
        
        <el-button 
          type="success" 
          size="large"
          style="width: 100%; margin-top: 12px;"
          :disabled="!isConnected || isFlashing"
          @click="handleReset"
        >
          <el-icon><Refresh /></el-icon>
          重启设备
        </el-button>
      </div>

      <!-- 进度条 -->
      <div v-if="isFlashing" class="progress-section">
        <el-progress 
          :percentage="Math.round(flashProgress)" 
          :status="flashProgress === 100 ? 'success' : undefined"
          :stroke-width="20"
        />
      </div>

      <!-- 日志面板 -->
      <el-card class="log-panel" shadow="never">
        <template #header>
          <div class="section-title">
            <el-icon><Document /></el-icon>
            <span>操作日志</span>
            <el-button 
              size="small" 
              text 
              style="margin-left: auto;"
              @click="clearLogs"
            >
              清空日志
            </el-button>
          </div>
        </template>
        
        <div class="log-container" ref="logContainerRef">
          <div 
            v-for="(log, index) in logs" 
            :key="index"
            :class="['log-item', `log-${log.type}`]"
          >
            <span class="log-time">{{ log.timestamp }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
          <div v-if="logs.length === 0" class="log-empty">
            暂无日志信息
          </div>
        </div>
      </el-card>

      <!-- 使用提示 -->
      <el-card class="tips-panel" shadow="never">
        <template #header>
          <div class="section-title">
            <el-icon><InfoFilled /></el-icon>
            <span>使用提示</span>
          </div>
        </template>
        
        <div class="tips-content">
          <div class="tip-item">
            <el-icon class="tip-icon" color="#F56C6C"><Check /></el-icon>
            <div>
              <strong>1. 安全协议要求（重要！）：</strong>
              <p>必须通过 <strong>HTTPS</strong> 访问本页面，或在 <strong>localhost</strong> 环境下运行</p>
              <p style="margin-top: 5px; color: #f56c6c;">
                ⚠️ 如果使用 HTTP 协议，Web Serial API 将不可用
              </p>
            </div>
          </div>
          <div class="tip-item">
            <el-icon class="tip-icon" color="#409EFF"><Check /></el-icon>
            <div>
              <strong>2. 浏览器要求：</strong>
              <p>必须使用 Chrome (≥89)、Edge (≥89) 或 Opera 浏览器</p>
              <p style="margin-top: 5px; color: #909399;">
                Firefox、Safari 等浏览器暂不支持 Web Serial API
              </p>
            </div>
          </div>
          <div class="tip-item">
            <el-icon class="tip-icon" color="#67C23A"><Check /></el-icon>
            <div>
              <strong>3. 连接设备：</strong>
              <p>使用 USB 数据线（非充电线）连接 ESP32 设备到电脑，点击"连接设备"按钮</p>
            </div>
          </div>
          <div class="tip-item">
            <el-icon class="tip-icon" color="#E6A23C"><Check /></el-icon>
            <div>
              <strong>4. 选择固件：</strong>
              <p>从下拉列表中选择要烧录的固件版本</p>
            </div>
          </div>
          <div class="tip-item">
            <el-icon class="tip-icon" color="#9C27B0"><Check /></el-icon>
            <div>
              <strong>5. 开始烧录：</strong>
              <p>点击"开始烧录"按钮，等待烧录完成（约2-3分钟）</p>
            </div>
          </div>
          <div class="tip-item">
            <el-icon class="tip-icon" color="#909399"><Check /></el-icon>
            <div>
              <strong>6. 故障排除：</strong>
              <p>如果烧录失败，可以先尝试"擦除Flash"，然后重新烧录</p>
            </div>
          </div>
        </div>
      </el-card>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Link, Close, FolderOpened, Upload, Delete, Refresh,
  Document, InfoFilled, Check
} from '@element-plus/icons-vue'

// 状态
const isConnected = ref(false)
const chipInfo = ref(null)
const selectedFirmwareId = ref('')
const selectedFirmware = ref(null)
const isFlashing = ref(false)
const flashProgress = ref(0)
const logs = ref([])
const logContainerRef = ref(null)

// ESP烧录器相关
let esploader = null
let transport = null

// 固件列表配置
const firmwareList = ref([
  {
    id: 'esp32s3-lite-v1.6',
    name: 'ESP32-S3-Lite v1.6',
    version: '1.6',
    filename: '/firmware/ESP32-S3-Lite-01-v1.6.bin',
    size: '约 6 MB',
    date: '2024-12-20',
    description: '最新稳定版本，包含所有功能优化',
    address: '0x0'
  },
  // 可以添加更多固件版本
])

// 添加日志
const addLog = (message, type = 'info') => {
  const timestamp = new Date().toLocaleTimeString('zh-CN')
  logs.value.push({
    timestamp,
    message,
    type
  })
  // 自动滚动到底部
  nextTick(() => {
    if (logContainerRef.value) {
      logContainerRef.value.scrollTop = logContainerRef.value.scrollHeight
    }
  })
}

// 清空日志
const clearLogs = () => {
  logs.value = []
}

// 动态加载 esptool-js
const loadESPTool = async () => {
  try {
    // 使用动态导入
    const module = await import('esptool-js')
    return module
  } catch (error) {
    addLog(`❌ 加载 esptool-js 失败: ${error.message}`, 'error')
    throw error
  }
}

// 连接设备
const handleConnect = async () => {
  try {
    addLog('🔍 正在请求串口访问权限...')
    
    const { ESPLoader, Transport } = await loadESPTool()
    
    // 请求串口访问
    const port = await navigator.serial.requestPort({
      filters: [
        { usbVendorId: 0x303a }, // Espressif
        { usbVendorId: 0x10c4 }, // Silicon Labs (CP210x)
        { usbVendorId: 0x1a86 }, // QinHeng Electronics (CH340)
      ]
    })
    
    transport = new Transport(port, true)
    
    // 创建ESPLoader实例
    esploader = new ESPLoader({
      transport: transport,
      baudrate: 115200,
      terminal: {
        clean() { },
        writeLine(data) { 
          if (data.trim()) console.log(data)
        },
        write(data) { 
          if (data.trim()) console.log(data)
        }
      }
    })

    const chip = await esploader.main()
    isConnected.value = true
    chipInfo.value = chip
    addLog(`✅ 连接成功！芯片: ${chip}`, 'success')
    ElMessage.success('设备连接成功')
  } catch (error) {
    addLog(`❌ 连接失败: ${error.message}`, 'error')
    ElMessage.error(`连接失败: ${error.message}`)
    console.error(error)
  }
}

// 断开连接
const handleDisconnect = async () => {
  try {
    if (transport) {
      await transport.disconnect()
      await transport.waitForUnlock(500)
      transport = null
      esploader = null
    }
    isConnected.value = false
    chipInfo.value = null
    addLog('🔌 已断开连接', 'success')
    ElMessage.success('已断开连接')
  } catch (error) {
    addLog(`⚠️ 断开连接时出错: ${error.message}`, 'error')
    ElMessage.warning('断开连接时出错')
  }
}

// 选择固件
const handleSelectFirmware = () => {
  const firmware = firmwareList.value.find(f => f.id === selectedFirmwareId.value)
  if (firmware) {
    selectedFirmware.value = firmware
    addLog(`📦 已选择固件: ${firmware.name}`)
  }
}

// 烧录固件
const handleFlash = async () => {
  if (!isConnected.value) {
    ElMessage.error('请先连接设备！')
    return
  }

  if (!selectedFirmware.value) {
    ElMessage.error('请选择固件版本！')
    return
  }

  try {
    isFlashing.value = true
    flashProgress.value = 0
    addLog(`⚡ 开始烧录固件: ${selectedFirmware.value.name}...`)
    
    // 从服务器下载固件文件
    const response = await fetch(selectedFirmware.value.filename)
    if (!response.ok) {
      throw new Error(`下载固件失败: ${response.status} ${response.statusText}`)
    }
    
    const firmwareData = await response.arrayBuffer()
    const address = parseInt(selectedFirmware.value.address, 16)
    
    // 将 ArrayBuffer 转换为字符串（esptool-js 需要）
    const uint8Array = new Uint8Array(firmwareData)
    let binaryString = ''
    for (let i = 0; i < uint8Array.length; i++) {
      binaryString += String.fromCharCode(uint8Array[i])
    }
    
    const fileArray = [{
      data: binaryString,
      address: address
    }]

    // 执行烧录
    await esploader.writeFlash({
      fileArray: fileArray,
      flashSize: 'keep',
      eraseAll: false,
      compress: true,
      reportProgress: (fileIndex, written, total) => {
        const percent = (written / total) * 100
        flashProgress.value = percent
        if (percent % 10 < 1) { // 每10%记录一次
          addLog(`💾 烧录进度: ${Math.round(percent)}%`)
        }
      }
    })
    
    flashProgress.value = 100
    addLog('🎉 固件烧录完成！', 'success')
    ElMessage.success('固件烧录完成！')
    
    // 尝试重启设备
    try {
      addLog('🔄 正在重启设备...')
      await esploader.hardReset()
      addLog('✅ 设备已重启！', 'success')
    } catch (resetError) {
      addLog('⚠️ 自动重启失败，请手动重启设备', 'error')
      console.error('Reset error:', resetError)
    }
    
    setTimeout(() => {
      isFlashing.value = false
      flashProgress.value = 0
    }, 3000)
  } catch (error) {
    addLog(`❌ 烧录失败: ${error.message}`, 'error')
    ElMessage.error(`烧录失败: ${error.message}`)
    console.error(error)
    isFlashing.value = false
    flashProgress.value = 0
  }
}

// 擦除Flash
const handleErase = async () => {
  if (!isConnected.value) {
    ElMessage.error('请先连接设备！')
    return
  }

  try {
    await ElMessageBox.confirm(
      '确定要擦除整个 Flash 吗？此操作不可恢复！',
      '警告',
      {
        confirmButtonText: '确定擦除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    addLog('🗑️ 开始擦除 Flash...')
    await esploader.eraseFlash()
    addLog('✅ Flash 擦除完成！', 'success')
    ElMessage.success('Flash 擦除完成')
  } catch (error) {
    if (error !== 'cancel') {
      addLog(`❌ 擦除失败: ${error.message}`, 'error')
      ElMessage.error('擦除失败')
    }
  }
}

// 重启设备
const handleReset = async () => {
  if (!isConnected.value) {
    ElMessage.error('请先连接设备！')
    return
  }

  try {
    addLog('🔄 正在重启设备...')
    await esploader.hardReset()
    addLog('✅ 设备已重启！', 'success')
    ElMessage.success('设备已重启')
  } catch (error) {
    addLog(`❌ 重启失败: ${error.message}`, 'error')
    addLog('💡 提示：请手动按一下设备上的 RESET 按钮', 'info')
    ElMessage.error('重启失败，请手动按 RESET 按钮')
  }
}

// 检查浏览器支持
onMounted(() => {
  // 检查是否为安全上下文（HTTPS 或 localhost）
  const isSecureContext = window.isSecureContext
  const protocol = window.location.protocol
  const hostname = window.location.hostname
  
  addLog(`🌐 当前协议: ${protocol}`, 'info')
  addLog(`🏠 当前主机: ${hostname}`, 'info')
  addLog(`🔒 安全上下文: ${isSecureContext ? '是' : '否'}`, isSecureContext ? 'success' : 'error')
  
  if (!('serial' in navigator)) {
    addLog('❌ 检测失败：浏览器不支持 Web Serial API', 'error')
    
    // 提供详细的诊断信息
    if (!isSecureContext) {
      addLog('⚠️ 原因：当前页面不是安全上下文（HTTPS）', 'error')
      addLog('💡 解决方案：', 'info')
      
      if (hostname === 'localhost' || hostname === '127.0.0.1') {
        addLog('   - 当前是 localhost，但使用了 HTTP 协议', 'info')
        addLog('   - 请确保服务器配置正确', 'info')
      } else {
        addLog('   - 必须通过 HTTPS 访问本页面', 'info')
        addLog('   - 或者在 localhost 环境下运行', 'info')
        addLog(`   - 当前地址: ${window.location.href}`, 'info')
        addLog(`   - 建议地址: https://${hostname}${window.location.port ? ':' + window.location.port : ''}${window.location.pathname}`, 'info')
      }
      
      ElMessage({
        message: 'Web Serial API 需要 HTTPS 协议！请使用 HTTPS 访问或在 localhost 运行。',
        type: 'error',
        duration: 8000,
        showClose: true
      })
    } else {
      addLog('⚠️ 请使用 Chrome (≥89)、Edge (≥89) 或 Opera 浏览器', 'error')
      addLog(`   当前浏览器: ${navigator.userAgent}`, 'info')
      
      ElMessage({
        message: '您的浏览器不支持 Web Serial API，请使用 Chrome 或 Edge 浏览器',
        type: 'error',
        duration: 5000,
        showClose: true
      })
    }
  } else {
    addLog('✅ Web Serial API 可用', 'success')
    addLog('✅ 准备就绪，请连接 ESP32 设备并点击"连接设备"', 'success')
    addLog(`📋 已加载 ${firmwareList.value.length} 个固件版本`, 'success')
  }
})
</script>

<style scoped lang="scss">
.firmware-flasher-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.flasher-card {
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

.status-section {
  margin-bottom: 20px;
  
  .status-card {
    background: #f5f7fa;
    border: 2px solid #e4e7ed;
    transition: all 0.3s;
    
    &.connected {
      background: #f0f9ff;
      border-color: #67c23a;
    }
    
    :deep(.el-card__body) {
      padding: 15px;
    }
    
    .status-indicator {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .status-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #f56c6c;
        animation: pulse 2s infinite;
      }
      
      .status-text {
        font-size: 15px;
        font-weight: 500;
        color: #606266;
      }
    }
    
    &.connected .status-dot {
      background: #67c23a;
    }
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.control-section {
  margin-bottom: 20px;
}

.firmware-selector-card {
  margin-bottom: 20px;
  
  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }
  
  .firmware-info {
    margin-top: 15px;
  }
}

.action-section {
  margin-bottom: 20px;
}

.progress-section {
  margin-bottom: 20px;
}

.log-panel {
  margin-bottom: 20px;
  
  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }
  
  .log-container {
    max-height: 300px;
    overflow-y: auto;
    background: #f5f7fa;
    border-radius: 4px;
    padding: 10px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    
    .log-item {
      padding: 5px 0;
      border-bottom: 1px solid #e4e7ed;
      
      &:last-child {
        border-bottom: none;
      }
      
      .log-time {
        color: #909399;
        margin-right: 10px;
      }
      
      .log-message {
        color: #606266;
      }
      
      &.log-success .log-message {
        color: #67c23a;
      }
      
      &.log-error .log-message {
        color: #f56c6c;
      }
      
      &.log-warning .log-message {
        color: #e6a23c;
      }
    }
    
    .log-empty {
      text-align: center;
      color: #909399;
      padding: 20px;
    }
  }
}

.tips-panel {
  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }
  
  .tips-content {
    .tip-item {
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .tip-icon {
        flex-shrink: 0;
        margin-top: 2px;
      }
      
      strong {
        display: block;
        margin-bottom: 5px;
        color: #303133;
      }
      
      p {
        margin: 0;
        color: #606266;
        font-size: 14px;
        line-height: 1.6;
      }
    }
  }
}
</style>

