<template>
  <div class="dashboard-content">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="banner-content">
        <div class="banner-text">
          <h1>设备管理控制台</h1>
        </div>
        <div class="banner-actions">
          <el-button type="primary" @click="$router.push('/device/device-register')">
            <el-icon><Plus /></el-icon>
            注册设备
          </el-button>
          <el-button type="primary" @click="$router.push('/device/devices')">
            <el-icon><Monitor /></el-icon>
            设备列表
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="24" class="stats-row">
      <el-col :xs="24" :sm="12">
        <el-card class="stat-card total-devices" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon size="32"><Monitor /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.totalDevices }}</div>
              <div class="stat-label">总设备数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12">
        <el-card class="stat-card online-devices" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon size="32"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.onlineDevices }}</div>
              <div class="stat-label">在线设备</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近设备 -->
    <el-card class="recent-devices" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>最近设备</span>
          <el-button type="text" @click="$router.push('/device/devices')">查看全部</el-button>
        </div>
      </template>
      <el-table :data="recentDevices" style="width: 100%">
        <el-table-column prop="name" label="设备名称" />
        <el-table-column prop="type" label="产品类型" />
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'online' ? 'success' : 'danger'" size="small">
              {{ scope.row.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lastSeen" label="最后上报" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { getDashboardStats, getRecentDevices, getRecentInteractions } from '../api/dashboard'
import { ElMessage } from 'element-plus'
import logger from '../utils/logger'
import {
  House, Monitor, User, Bell, Setting, ArrowRight, ArrowDown, SwitchButton,
  Plus, Refresh, CircleCheck, CircleClose, Warning, TrendCharts, DataAnalysis,
  Timer, Upload, Download, Connection, Message
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const stats = reactive({
  totalDevices: 0,
  onlineDevices: 0,
  offlineDevices: 0,
  alerts: 0
})

const recentDevices = ref([])
const loading = ref(false)
const refreshTimer = ref(null)

// 交互数据相关
const interactionStats = reactive({
  todayTotal: 0,
  successRate: 0,
  avgResponseTime: 0,
  todayUpload: 0,
  todayDownload: 0,
  totalTransfer: 0,
  transferProgress: 0
})

const recentInteractions = ref([])

// 计算属性
const currentDate = computed(() => {
  return new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
})

// 方法
const refreshData = () => {
  loadDashboardData()
}

// 防抖函数
const debounce = (func, wait) => {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// 加载仪表盘数据
const loadDashboardData = async (showLoading = true) => {
  if (showLoading) {
    loading.value = true
  }
  
  try {
    // 获取仪表盘统计数据
    const statsResponse = await getDashboardStats()
    // API可能直接返回对象，也可能包装在data中
    const statsData = statsResponse.data || statsResponse
    if (statsData) {
      stats.totalDevices = statsData.total_devices || 0
      stats.onlineDevices = statsData.online_devices || 0
      stats.offlineDevices = statsData.offline_devices || 0
      stats.alerts = statsData.alerts || 0
    }

    // 获取最近设备列表
    const devicesResponse = await getRecentDevices(5)
    // API可能直接返回数组，也可能包装在data中
    const devicesData = Array.isArray(devicesResponse) ? devicesResponse : (devicesResponse.data || [])
    if (devicesData && Array.isArray(devicesData) && devicesData.length > 0) {
      recentDevices.value = devicesData.map(device => ({
        id: device.id,
        name: device.name,
        type: device.product_name || '未分配',
        status: device.is_online ? 'online' : 'offline',
        lastSeen: device.last_seen ? new Date(device.last_seen).toLocaleString('zh-CN') : '未知',
        value: device.is_online ? '正常' : '离线',
        location: device.location || '未设置'
      }))
    } else {
      // 如果没有数据，清空列表
      recentDevices.value = []
    }
  } catch (error) {
    logger.error('加载仪表盘数据失败:', error)
    ElMessage.error('加载仪表盘数据失败')
  } finally {
    loading.value = false
  }
}

// 防抖的刷新函数
const debouncedRefresh = debounce(() => {
  loadDashboardData(false)
}, 300)

// 自动刷新
const startAutoRefresh = () => {
  refreshTimer.value = setInterval(() => {
    loadDashboardData(false)
  }, 30000) // 30秒刷新一次
}

const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// 手动刷新
const handleRefresh = () => {
  debouncedRefresh()
}

// 加载交互数据
const loadInteractionData = async () => {
  try {
    // 获取最近交互记录
    const interactionsResponse = await getRecentInteractions(10)
    // API可能直接返回数组，也可能包装在data中
    const interactionsData = Array.isArray(interactionsResponse) ? interactionsResponse : (interactionsResponse.data || [])
    if (interactionsData && Array.isArray(interactionsData) && interactionsData.length > 0) {
      recentInteractions.value = interactionsData.map(interaction => ({
        id: interaction.id,
        deviceName: interaction.device_name,
        type: interaction.type,
        description: interaction.description,
        timestamp: formatTimestamp(interaction.timestamp),
        status: interaction.status
      }))
      
      // 计算统计数据
      const total = recentInteractions.value.length
      const successCount = recentInteractions.value.filter(i => i.status === 'success').length
      
      // 如果没有数据，所有统计都设为0
      if (total === 0) {
        interactionStats.todayTotal = 0
        interactionStats.successRate = 0
        interactionStats.avgResponseTime = 0
        interactionStats.todayUpload = 0
        interactionStats.todayDownload = 0
        interactionStats.totalTransfer = 0
        interactionStats.transferProgress = 0
      } else {
        interactionStats.todayTotal = total
        interactionStats.successRate = Math.round((successCount / total) * 100)
        interactionStats.avgResponseTime = 0 // 暂时设为0，后续可以从API获取真实数据
        interactionStats.todayUpload = 0 // 暂时设为0，后续可以从API获取真实数据
        interactionStats.todayDownload = 0 // 暂时设为0，后续可以从API获取真实数据
        interactionStats.totalTransfer = 0 // 暂时设为0，后续可以从API获取真实数据
        interactionStats.transferProgress = 0 // 暂时设为0，后续可以从API获取真实数据
      }
    } else {
      // 如果没有数据，清空列表和统计
      recentInteractions.value = []
      interactionStats.todayTotal = 0
      interactionStats.successRate = 0
      interactionStats.avgResponseTime = 0
      interactionStats.todayUpload = 0
      interactionStats.todayDownload = 0
      interactionStats.totalTransfer = 0
      interactionStats.transferProgress = 0
    }
  } catch (error) {
    logger.error('加载交互数据失败:', error)
    ElMessage.error('加载交互数据失败')
  }
}

// 刷新交互数据
const refreshInteractionData = () => {
  loadInteractionData()
}

// 格式化时间戳
const formatTimestamp = (timestamp) => {
  if (!timestamp) return '未知'
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) { // 小于1分钟
    return '刚刚'
  } else if (diff < 3600000) { // 小于1小时
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) { // 小于1天
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return date.toLocaleString('zh-CN')
  }
}

// 格式化数据大小
const formatDataSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 获取进度条颜色
const getProgressColor = (percentage) => {
  if (percentage < 30) return '#67c23a'
  if (percentage < 70) return '#e6a23c'
  return '#f56c6c'
}

// 获取交互类型图标
const getInteractionIcon = (type) => {
  const iconMap = {
    'data_upload': Upload,
    'data_download': Download,
    'command': Setting,
    'heartbeat': Connection,
    'message': Message
  }
  return iconMap[type] || DataAnalysis
}

// 获取交互图标颜色
const getInteractionIconColor = (type) => {
  const colorMap = {
    'data_upload': '#67c23a',
    'data_download': '#409eff',
    'command': '#e6a23c',
    'heartbeat': '#909399',
    'message': '#f56c6c'
  }
  return colorMap[type] || '#409eff'
}

onMounted(async () => {
  await nextTick()
  await loadDashboardData()
  await loadInteractionData()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.dashboard-content {
  max-width: 1400px;
  margin: 0 auto;
}

/* 欢迎横幅 */
.welcome-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 24px;
  color: white;
  position: relative;
  overflow: hidden;
}

.welcome-banner::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 200px;
  height: 200px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  transform: translate(50%, -50%);
}

.banner-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
}

.banner-text h1 {
  margin: 0 0 8px 0;
  font-size: 2rem;
  font-weight: 700;
}

.banner-text p {
  margin: 0;
  opacity: 0.9;
  font-size: 1rem;
}

.banner-actions {
  display: flex;
  gap: 12px;
}

/* 统计卡片 */
.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 16px;
  border: none;
  transition: all 0.3s ease;
  overflow: hidden;
  position: relative;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
}

.stat-card.total-devices::before {
  background: linear-gradient(90deg, #3b82f6, #1d4ed8);
}

.stat-card.online-devices::before {
  background: linear-gradient(90deg, #10b981, #059669);
}

.stat-card.offline-devices::before {
  background: linear-gradient(90deg, #ef4444, #dc2626);
}

.stat-card.alerts::before {
  background: linear-gradient(90deg, #f59e0b, #d97706);
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 24px;
  height: 100%;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
}

.stat-card.total-devices .stat-icon {
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  color: #1d4ed8;
}

.stat-card.online-devices .stat-icon {
  background: linear-gradient(135deg, #d1fae5, #a7f3d0);
  color: #059669;
}

.stat-card.offline-devices .stat-icon {
  background: linear-gradient(135deg, #fee2e2, #fecaca);
  color: #dc2626;
}

.stat-card.alerts .stat-icon {
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  color: #d97706;
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
}

.stat-label {
  color: #64748b;
  font-size: 0.9rem;
  margin-bottom: 8px;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8rem;
}

.trend-text {
  font-weight: 600;
}

/* 设备列表 */
.recent-devices {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #1e293b;
}

/* 交互数据小组件样式 */
.interaction-widgets {
  margin-bottom: 24px;
}

.interaction-card {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  height: 100%;
}

.interaction-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #1e293b;
}

/* 今日交互统计样式 */
.interaction-stats {
  padding: 16px 0;
}

.stat-item {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.stat-item:last-child {
  margin-bottom: 0;
}

.stat-item .stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 20px;
}

.stat-icon.primary {
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  color: #1d4ed8;
}

.stat-icon.success {
  background: linear-gradient(135deg, #d1fae5, #a7f3d0);
  color: #059669;
}

.stat-icon.warning {
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  color: #d97706;
}

.stat-item .stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
}

.stat-item .stat-label {
  color: #64748b;
  font-size: 0.9rem;
}

/* 数据传输统计样式 */
.data-transfer-stats {
  padding: 16px 0;
}

.transfer-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.transfer-label {
  color: #64748b;
  font-size: 0.9rem;
}

.transfer-value {
  font-weight: 600;
  font-size: 1rem;
}

.transfer-value.upload {
  color: #059669;
}

.transfer-value.download {
  color: #1d4ed8;
}

.transfer-value.total {
  color: #1e293b;
}

.transfer-progress {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.progress-label {
  color: #64748b;
  font-size: 0.9rem;
  margin-bottom: 8px;
}

/* 最近交互记录样式 */
.recent-interactions {
  padding: 16px 0;
  max-height: 300px;
  overflow-y: auto;
}

.interaction-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
}

.interaction-item:last-child {
  border-bottom: none;
}

.interaction-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  background: #f8fafc;
  font-size: 16px;
}

.interaction-content {
  flex: 1;
  min-width: 0;
}

.interaction-device {
  font-weight: 600;
  color: #1e293b;
  font-size: 0.9rem;
  margin-bottom: 2px;
}

.interaction-desc {
  color: #64748b;
  font-size: 0.8rem;
  margin-bottom: 2px;
}

.interaction-time {
  color: #94a3b8;
  font-size: 0.75rem;
}

.interaction-status {
  margin-left: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .banner-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .banner-text h1 {
    font-size: 1.5rem;
  }
  
  .stat-content {
    padding: 16px;
  }
  
  .stat-number {
    font-size: 1.5rem;
  }

  .interaction-widgets .el-col {
    margin-bottom: 16px;
  }

  .stat-item {
    margin-bottom: 12px;
  }

  .stat-value {
    font-size: 1.25rem;
  }

  .interaction-item {
    padding: 8px 0;
  }

  .interaction-icon {
    width: 36px;
    height: 36px;
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .banner-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .banner-actions .el-button {
    width: 100%;
  }
}
</style>
