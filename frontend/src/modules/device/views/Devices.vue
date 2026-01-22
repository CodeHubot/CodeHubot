<template>
  <div class="devices-content">
    <!-- 页面标题和统计 -->
    <div class="page-header">
      <div class="header-info">
        <h1>
          <el-icon size="28" style="margin-right: 12px; vertical-align: middle;"><Monitor /></el-icon>
          设备管理中心
        </h1>
        <p>统一管理和监控所有物联网设备，实时掌握设备状态</p>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <div class="stat-icon">
            <el-icon size="20"><Monitor /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ deviceStats.total_devices || devices.length }}</div>
            <div class="stat-label">设备总数</div>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon online">
            <el-icon size="20"><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ deviceStats.online_devices || onlineDevicesCount }}</div>
            <div class="stat-label">在线设备</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button type="primary" @click="$router.push('/device/device-register')" class="action-btn">
          <el-icon><Plus /></el-icon>
          添加设备
        </el-button>
      </div>
      <div class="toolbar-right">
        <el-select v-model="productFilter" placeholder="选择产品" style="width: 140px; margin-right: 12px;" @change="handleFilter" clearable>
          <el-option label="全部产品" value="" />
          <el-option
            v-for="product in products"
            :key="product.id"
            :label="product.name"
            :value="product.id"
          />
        </el-select>

        <el-select v-model="statusFilter" placeholder="在线状态" style="width: 120px; margin-right: 12px;" @change="handleFilter">
          <el-option label="全部状态" value="" />
          <el-option label="在线设备" value="online" />
          <el-option label="离线设备" value="offline" />
        </el-select>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索设备名称、UUID、位置..."
          style="width: 280px"
          @input="handleSearch"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>
    
    <!-- 设备网格视图 -->
    <div class="devices-grid" v-loading="loading">
      <div 
        v-for="device in filteredDevices" 
        :key="device.id" 
        class="device-card"
      >
        <!-- 设备名称和在线状态在最上方 -->
        <div class="device-title">
          <h3 class="device-name">{{ device.name }}</h3>
          <div class="device-status">
            <el-tag :type="device.is_online ? 'success' : 'danger'" size="small">
              {{ device.is_online ? '在线' : '离线' }}
            </el-tag>
          </div>
        </div>
        

        <div class="device-info">
          <div class="device-meta">
            <div class="meta-item">
              <span class="meta-label">产品:</span>
              <span class="meta-value">{{ device.product_name || '未分配' }}</span>
              <!-- 显示产品绑定状态 -->
              <el-tag 
                v-if="device.device_status" 
                :type="getDeviceStatusType(device.device_status)" 
                size="small" 
                style="margin-left: 8px;"
              >
                {{ getDeviceStatusText(device.device_status) }}
              </el-tag>
            </div>

            <div class="meta-item">
              <span class="meta-label">所有者:</span>
              <span class="meta-value">{{ device.owner_name || '未设置' }}</span>
            </div>
            
            <div class="meta-item">
              <span class="meta-label">最后上线:</span>
              <span class="meta-value">{{ formatLastSeen(device.last_seen) }}</span>
            </div>
          </div>
          <div class="device-uuid">
            <div class="uuid-row">
              <span class="uuid-label">UUID:</span>
              <span 
                class="uuid-value" 
                :title="device.uuid ? '点击复制UUID' : '未生成'"
                @click.stop="copyUUID(device)"
                :class="{ 'clickable': device.uuid }"
              >
                {{ device.uuid || '未生成' }}
              </span>
              <div class="uuid-actions">
                <el-button 
                  type="text" 
                  size="small" 
                  @click.stop="copyUUID(device)"
                  class="uuid-copy-btn"
                  :title="'复制UUID'"
                  v-if="device.uuid"
                >
                  <el-icon><DocumentCopy /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>
        <div class="device-footer">
          <div class="device-actions">
            <!-- 主要操作按钮 -->
            <div class="primary-actions">
              <el-button 
                type="primary" 
                size="small" 
                @click.stop="navigateToRealtime(device)"
                :disabled="!device.is_online"
                class="action-btn monitor-btn"
              >
                <el-icon><TrendCharts /></el-icon>
                实时数据
              </el-button>
              <el-button 
                type="success" 
                size="small" 
                @click.stop="navigateToRemoteControl(device)"
                :disabled="!device.is_online"
                class="action-btn control-btn"
              >
                <el-icon><Operation /></el-icon>
                远程控制
              </el-button>
            </div>
            
            <!-- 次要操作按钮 -->
            <div class="secondary-actions">
              <el-button 
                v-if="canViewDeviceDetail(device)"
                type="primary" 
                size="small" 
                @click.stop="navigateToDeviceDetail(device)"
                class="action-btn detail-btn"
              >
                <el-icon><View /></el-icon>
                设备详情
              </el-button>
              <el-button 
                v-if="canConfigDevice(device)"
                type="info" 
                size="small" 
                @click.stop="navigateToDeviceConfig(device)"
                class="action-btn plugin-btn"
              >
                <el-icon><Setting /></el-icon>
                设备配置
              </el-button>
              <el-button 
                v-if="userStore.isTeamAdmin && !device.team_id"
                type="warning" 
                size="small" 
                @click.stop="setAsTeamDevice(device)"
                class="action-btn team-btn"
              >
                <el-icon><OfficeBuilding /></el-icon>
                设为团队设备
              </el-button>
              <el-tag 
                v-if="device.team_id"
                type="success"
                size="small"
                style="margin-left: 8px;"
              >
                <el-icon><OfficeBuilding /></el-icon>
                团队设备
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>



    <!-- 编辑设备对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑设备" width="600px">
      <el-form :model="editDeviceForm" :rules="deviceRules" ref="editDeviceFormRef" label-width="100px">
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="editDeviceForm.name" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="设备类型" prop="device_type">
          <el-select v-model="editDeviceForm.device_type" placeholder="请选择设备类型" style="width: 100%">
            <el-option label="温度传感器" value="temperature" />
            <el-option label="湿度传感器" value="humidity" />
            <el-option label="压力传感器" value="pressure" />
            <el-option label="烟雾探测器" value="smoke" />
            <el-option label="门禁控制器" value="access" />
          </el-select>
        </el-form-item>
        <el-form-item label="设备ID" prop="device_id">
          <el-input v-model="editDeviceForm.device_id" placeholder="请输入设备ID" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="editDeviceForm.description" type="textarea" placeholder="请输入设备描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="updateDevice">确定</el-button>
      </template>
    </el-dialog>




  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getDevices, getDevicesWithProductInfo, getDevicesStatistics, setDeviceTeam } from '@/api/device'
import { getProductsSummary } from '@/api/product'
import {
  Monitor, Plus, Search,
  TrendCharts, Operation, View, Edit, Setting, Document, Delete, DocumentCopy,
  CircleCheck, CircleClose, OfficeBuilding
} from '@element-plus/icons-vue'
import logger from '@/utils/logger'


const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const devices = ref([])
const products = ref([])
const deviceStats = ref({})
const loading = ref(false)
const searchKeyword = ref('')
const statusFilter = ref('')
const productFilter = ref('')
const activeFilter = ref('')
const deviceStatusFilter = ref('')
const showEditDialog = ref(false)
const editDeviceForm = reactive({
  id: null,
  name: '',
  device_type: '',
  device_id: '',
  description: ''
})

const currentDevice = ref(null)

// 表单验证规则
const deviceRules = {
  name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' }
  ],
  device_type: [
    { required: true, message: '请选择设备类型', trigger: 'change' }
  ],
  device_id: [
    { required: true, message: '请输入设备ID', trigger: 'blur' }
  ]
}

// 格式化数据大小
const formatDataSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// 计算属性
const onlineDevicesCount = computed(() => {
  return devices.value.filter(device => device.is_online).length
})

const offlineDevicesCount = computed(() => {
  return devices.value.filter(device => !device.is_online).length
})



const filteredDevices = computed(() => {
  let filtered = devices.value

  // 产品筛选
  if (productFilter.value) {
    filtered = filtered.filter(device => device.product_id === productFilter.value)
  }

  // 在线状态筛选
  if (statusFilter.value) {
    filtered = filtered.filter(device => {
      if (statusFilter.value === 'online') return device.is_online
      if (statusFilter.value === 'offline') return !device.is_online
      return true
    })
  }

  // 激活状态筛选
  if (activeFilter.value) {
    filtered = filtered.filter(device => {
      if (activeFilter.value === 'active') return device.is_active
      if (activeFilter.value === 'inactive') return !device.is_active
      return true
    })
  }

  // 设备状态筛选
  if (deviceStatusFilter.value) {
    filtered = filtered.filter(device => device.device_status === deviceStatusFilter.value)
  }

  // 搜索筛选
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(device => 
      device.name.toLowerCase().includes(keyword) ||
      (device.uuid && device.uuid.toLowerCase().includes(keyword)) ||
      (device.location && device.location.toLowerCase().includes(keyword)) ||
      (device.group_name && device.group_name.toLowerCase().includes(keyword)) ||
      (device.product_name && device.product_name.toLowerCase().includes(keyword))
    )
  }

  return filtered
})

// 方法
const loadDevices = async () => {
  loading.value = true
  try {
    // 从API获取包含产品信息的设备列表
    const response = await getDevicesWithProductInfo()
    if (response.data) {
      devices.value = response.data
    }
  } catch (error) {
    logger.error('加载设备列表失败:', error)
    ElMessage.error('加载设备列表失败')
    // 如果API失败，尝试使用普通设备列表
    try {
      const fallbackResponse = await getDevices()
      if (fallbackResponse.data) {
        devices.value = fallbackResponse.data
      }
    } catch (fallbackError) {
      logger.error('加载备用设备列表也失败:', fallbackError)
    }
  } finally {
    loading.value = false
  }
}

const loadProducts = async () => {
  try {
    const response = await getProductsSummary({ is_active: true })
    products.value = response.data || []
  } catch (error) {
    logger.error('加载产品列表失败:', error)
  }
}



const loadDeviceStats = async () => {
  try {
    const response = await getDevicesStatistics()
    deviceStats.value = response.data || {}
  } catch (error) {
    logger.error('加载设备统计失败:', error)
  }
}



const handleSearch = () => {
  // 搜索逻辑已在计算属性中处理
}

const handleFilter = () => {
  // 筛选逻辑已在计算属性中处理
}

const viewDevice = (device) => {
  router.push(`/device/${device.uuid}/detail`)
}

const viewDeviceDetail = (device) => {
  router.push(`/device/${device.uuid}/detail`)
}

const handleDeviceAction = (command, device) => {
  if (command === 'detail') {
    viewDevice(device)
  } else if (command === 'edit') {
    editDeviceForm.id = device.id
    editDeviceForm.name = device.name
    editDeviceForm.device_type = device.device_type
    editDeviceForm.device_id = device.device_id
    editDeviceForm.description = device.description
    showEditDialog.value = true
  } else if (command === 'config') {
    ElMessage.info('设备配置功能开发中...')
  } else if (command === 'logs') {
    router.push(`/device/${device.uuid}/logs`)
  } else if (command === 'delete') {
    ElMessageBox.confirm('确定要删除这个设备吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      deleteDevice(device.uuid)
    })
  }
}

// UUID复制功能
const copyUUID = async (device) => {
  if (!device.uuid) {
    ElMessage.warning('该设备尚未生成UUID')
    return
  }
  
  try {
    await navigator.clipboard.writeText(device.uuid)
    ElMessage.success('UUID已复制到剪贴板')
  } catch (error) {
    // 降级方案：使用传统的复制方法
    const textArea = document.createElement('textarea')
    textArea.value = device.uuid
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      ElMessage.success('UUID已复制到剪贴板')
    } catch (fallbackError) {
      ElMessage.error('复制失败，请手动复制UUID')
    }
    document.body.removeChild(textArea)
  }
}

// 页面跳转方法
const navigateToRealtime = (device) => {
  if (!device.is_online) {
    ElMessage.warning('设备离线，无法进行实时监控')
    return
  }
  if (!device.uuid) {
    ElMessage.warning('设备UUID未生成，无法访问实时数据页面')
    return
  }
  router.push(`/device/${device.uuid}/realtime`)
}

const navigateToRemoteControl = (device) => {
  if (!device.is_online) {
    ElMessage.warning('设备离线，无法进行远程控制')
    return
  }
  if (!device.uuid) {
    ElMessage.warning('设备UUID未生成，无法访问远程控制页面')
    return
  }
  router.push(`/device/${device.uuid}/remote-control`)
}

const navigateToDeviceDetail = (device) => {
  if (!device.uuid) {
    ElMessage.warning('设备UUID未生成，无法访问设备详情页面')
    return
  }
  
  // 再次检查权限
  if (!canViewDeviceDetail(device)) {
    ElMessage.warning('您没有权限查看此设备详情（授权设备仅供使用）')
    return
  }
  
  router.push(`/device/${device.uuid}/detail`)
}

// 判断用户是否有权限查看设备详情
const canViewDeviceDetail = (device) => {
  // 管理员可以查看所有设备详情
  if (userStore.isPlatformAdmin || userStore.isTeamAdmin) {
    return true
  }
  
  // 获取当前用户ID
  const currentUserId = userStore.userInfo?.id || userStore.user?.id
  
  // 学生只能查看自己注册的设备详情，不能查看授权获得的设备详情
  if (userStore.userInfo?.role === 'student') {
    return device.user_id === currentUserId
  }
  
  // 其他用户（教师等）可以查看自己的设备详情
  return device.user_id === currentUserId
}

// 判断用户是否有权限配置设备
const canConfigDevice = (device) => {
  // 管理员可以配置所有设备
  if (userStore.isPlatformAdmin || userStore.isTeamAdmin) {
    return true
  }
  
  // 获取当前用户ID
  const currentUserId = userStore.userInfo?.id || userStore.user?.id
  
  // 学生只能配置自己注册的设备，不能配置授权获得的设备
  if (userStore.userInfo?.role === 'student') {
    return device.user_id === currentUserId
  }
  
  // 其他用户（教师等）可以配置自己的设备
  return device.user_id === currentUserId
}

const navigateToDeviceConfig = (device) => {
  if (!device.uuid) {
    ElMessage.warning('设备UUID未生成，无法访问设备配置页面')
    return
  }
  
  // 再次检查权限
  if (!canConfigDevice(device)) {
    ElMessage.warning('您没有权限配置此设备')
    return
  }
  
  router.push(`/device/${device.uuid}/config`)
}

// 设置为团队设备
const setAsTeamDevice = async (device) => {
  try {
    await ElMessageBox.confirm(
      `确定要将设备"${device.name}"设置为团队设备吗？设置后，设备将可用于团队协作和设备分组。`,
      '设置为团队设备',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 调用API设置为团队设备
    await setDeviceTeam(device.uuid, userStore.userInfo?.team_id)
    
    ElMessage.success('设备已设置为团队设备')
    
    // 刷新设备列表
    loadDevices()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('设置团队设备失败:', error)
      ElMessage.error(error.message || '设置失败')
    }
  }
}



const updateDevice = () => {
  // 这里应该调用API更新设备
  const index = devices.value.findIndex(d => d.id === editDeviceForm.id)
  if (index !== -1) {
    devices.value[index] = {
      ...devices.value[index],
      name: editDeviceForm.name,
      device_type: editDeviceForm.device_type,
      device_id: editDeviceForm.device_id,
      description: editDeviceForm.description
    }
  }
  
  showEditDialog.value = false
  ElMessage.success('设备更新成功')
}

const deleteDevice = (deviceId) => {
  // 这里应该调用API删除设备
  const index = devices.value.findIndex(d => d.id === deviceId)
  if (index !== -1) {
    devices.value.splice(index, 1)
    ElMessage.success('设备删除成功')
  }
}

const handleOpenDetail = (device) => {
  router.push(`/device/${device.uuid}/detail`)
}

// 格式化最后上线时间（后端返回北京时间 ISO 8601 格式，带 +08:00 时区偏移）
const formatLastSeen = (dateString) => {
  if (!dateString) return '未知'
  
  try {
    // 后端返回的是北京时间的 ISO 8601 格式，例如：2025-11-15T13:30:00+08:00
    // JavaScript 的 Date 构造函数可以直接解析这种格式
    const date = new Date(dateString)
    
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      console.error('Invalid date string:', dateString)
      return '时间格式错误'
    }
    
    const now = new Date()
    const diff = now - date
    
    // 相对时间显示
    if (diff < 0) {
      return '刚刚' // 如果设备时间超前，显示"刚刚"
    } else if (diff < 60000) { // 1分钟内
      return '刚刚'
    } else if (diff < 3600000) { // 1小时内
      return `${Math.floor(diff / 60000)}分钟前`
    } else if (diff < 86400000) { // 24小时内
      return `${Math.floor(diff / 3600000)}小时前`
    } else {
      // 超过24小时，显示具体日期时间（北京时间）
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      })
    }
  } catch (error) {
    console.error('Error parsing date:', dateString, error)
    return '时间解析失败'
  }
}

// 设备状态处理函数
const getDeviceStatusText = (status) => {
  const statusMap = {
    'pending': '待绑定',
    'bound': '已绑定',
    'active': '激活',
    'offline': '离线',
    'error': '错误'
  }
  return statusMap[status] || status
}

const getDeviceStatusType = (status) => {
  const typeMap = {
    'pending': 'warning',
    'bound': 'info',
    'active': 'success',
    'offline': 'info',
    'error': 'danger'
  }
  return typeMap[status] || 'info'
}

onMounted(() => {
  loadDevices()
  loadProducts()
  loadDeviceStats()
})
</script>

<style scoped>
.devices-content {
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
}

.header-info h1 {
  margin: 0 0 8px 0;
  font-size: 2rem;
  font-weight: 700;
}

.header-info p {
  margin: 0;
  opacity: 0.9;
}

.header-stats {
  display: flex;
  gap: 32px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
  color: white;
}

/* 工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.toolbar-left {
  display: flex;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.action-btn {
  border-radius: 8px;
}

/* 设备网格 */
.devices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.device-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
  border: 2px solid transparent;
}

.device-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  border-color: #409EFF;
}

.device-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.device-title .device-name {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 600;
  color: #1e293b;
}

.device-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.device-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
}



.device-info {
  margin: 16px 0;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.device-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-label {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 500;
  min-width: 40px;
}

.meta-value {
  font-size: 0.75rem;
  color: #1e293b;
  font-weight: 600;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-status-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.status-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.status-label {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 500;
}

.status-value {
  font-size: 0.75rem;
  color: #1e293b;
  font-weight: 600;
}

.error-count {
  color: #ef4444;
  font-weight: 700;
}

.device-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.last-seen {
  font-size: 0.8rem;
  color: #64748b;
}

.device-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: stretch;
}

.primary-actions {
  display: flex;
  gap: 8px;
  justify-content: space-between;
}

.secondary-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  justify-content: space-between;
}

.action-btn {
  flex: 1;
  min-width: 0;
  font-size: 12px;
  padding: 6px 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.monitor-btn {
  background: linear-gradient(135deg, #409eff, #67c23a);
  border: none;
  color: white;
}

.monitor-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #337ecc, #529b2e);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.control-btn {
  background: linear-gradient(135deg, #67c23a, #e6a23c);
  border: none;
  color: white;
}

.control-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #529b2e, #cf9236);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
}

.plugin-btn {
  background: linear-gradient(135deg, #909399, #606266);
  border: none;
  color: white;
  flex: 0 0 auto;
  min-width: 80px;
}

.plugin-btn:hover {
  background: linear-gradient(135deg, #73767a, #4c4d4f);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(144, 147, 153, 0.3);
}

.detail-btn, .more-btn {
  flex: 0 0 auto;
  min-width: 60px;
  color: #ffffff;
  background-color: #409eff;
  border-color: #409eff;
}

.detail-btn:hover, .more-btn:hover {
  color: #ffffff;
  background-color: #66b1ff;
  border-color: #66b1ff;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

.action-btn .el-icon {
  margin-right: 4px;
  font-size: 14px;
}

/* UUID显示样式 */
.device-uuid {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.uuid-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
}

.uuid-label {
  color: #909399;
  font-weight: 500;
  flex-shrink: 0;
  font-size: 0.8rem;
}

.uuid-value {
  color: #606266;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: #f5f7fa;
  padding: 4px 6px;
  border-radius: 4px;
  flex: 1;
  word-break: break-all;
  line-height: 1.3;
  font-size: 10px;
  border: 1px solid #e4e7ed;
}

.uuid-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .header-stats {
    gap: 16px;
  }
  
  .toolbar {
    flex-direction: column;
    gap: 16px;
  }
  
  .toolbar-left,
  .toolbar-right {
    width: 100%;
    justify-content: center;
  }
  
  .devices-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .header-stats {
    flex-direction: column;
    gap: 12px;
  }
  
  .toolbar-left {
    flex-direction: column;
    gap: 8px;
  }
  
  .toolbar-right {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
