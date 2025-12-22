<template>
  <div class="device-detail-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" type="text" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回设备列表
        </el-button>
        <div class="page-title">
          <h2>{{ deviceInfo.name || '设备详情' }}</h2>
          <div class="device-tags" v-if="deviceInfo.device_id">
            <el-tag :type="deviceInfo.is_online ? 'success' : 'danger'" size="small">
              {{ deviceInfo.is_online ? '在线' : '离线' }}
            </el-tag>
            <el-tag type="info" size="small">{{ deviceInfo.device_type }}</el-tag>
            <el-tag type="warning" size="small">ID: {{ deviceInfo.device_id }}</el-tag>
          </div>
        </div>
      </div>
      <div class="header-controls">
        <el-button 
          v-if="isDeviceOwner"
          type="primary" 
          @click="editDialogVisible = true"
        >
          <el-icon><Edit /></el-icon>
          编辑设备
        </el-button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="page-content" v-if="!loading">
      <!-- 设备基本信息卡片 -->
      <div class="info-section">
        <h3>设备基本信息</h3>
        <div class="info-card">
          <div class="card-header">
            <el-icon><Cpu /></el-icon>
            <span>基本信息</span>
          </div>
          <div class="card-content">
            <div class="info-item">
              <span class="label">设备名称:</span>
              <span class="value">{{ deviceInfo.name || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">设备ID:</span>
              <span class="value">{{ deviceInfo.device_id || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">设备UUID:</span>
              <span class="value">{{ deviceInfo.uuid || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">设备描述:</span>
              <span class="value">{{ deviceInfo.description || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">产品ID:</span>
              <span class="value">{{ deviceInfo.product_id || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">设备类型:</span>
              <span class="value">{{ deviceInfo.device_type || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">制造商:</span>
              <span class="value">{{ deviceInfo.manufacturer || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">型号:</span>
              <span class="value">{{ deviceInfo.model || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">在线状态:</span>
              <el-tag :type="deviceInfo.is_online ? 'success' : 'danger'" size="small">
                {{ deviceInfo.is_online ? '在线' : '离线' }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="label">激活状态:</span>
              <el-tag :type="deviceInfo.is_active ? 'success' : 'info'" size="small">
                {{ deviceInfo.is_active ? '已激活' : '未激活' }}
              </el-tag>
            </div>
            <div class="info-item">
              <span class="label">注册时间:</span>
              <span class="value">{{ deviceInfo.created_at || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">更新时间:</span>
              <span class="value">{{ deviceInfo.updated_at || '-' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 硬件信息 -->
      <div class="info-section">
        <h3>硬件信息</h3>
        <div class="info-card">
          <div class="card-header">
            <el-icon><Setting /></el-icon>
            <span>硬件配置</span>
          </div>
          <div class="card-content">
            <div class="info-item">
              <span class="label">固件版本:</span>
              <span class="value">{{ deviceInfo.firmware_version || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">硬件版本:</span>
              <span class="value">{{ deviceInfo.hardware_version || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">序列号:</span>
              <span class="value">{{ deviceInfo.serial_number || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">MAC地址:</span>
              <span class="value">{{ deviceInfo.mac_address || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">IP地址:</span>
              <span class="value">{{ deviceInfo.ip_address || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">质量等级:</span>
              <span class="value">{{ deviceInfo.quality_grade || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">生产日期:</span>
              <span class="value">{{ deviceInfo.production_date || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="label">运行时长:</span>
              <span class="value">{{ deviceInfo.uptime || 0 }} 秒</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 位置信息 -->
      <div class="info-section" v-if="deviceInfo.location || deviceInfo.group_name || deviceInfo.room || deviceInfo.floor">
        <h3>位置信息</h3>
        <div class="info-card">
          <div class="card-header">
            <el-icon><Location /></el-icon>
            <span>部署位置</span>
          </div>
          <div class="card-content">
            <div class="info-item" v-if="deviceInfo.location">
              <span class="label">位置:</span>
              <span class="value">{{ deviceInfo.location }}</span>
            </div>
            <div class="info-item" v-if="deviceInfo.group_name">
              <span class="label">设备组:</span>
              <span class="value">{{ deviceInfo.group_name }}</span>
            </div>
            <div class="info-item" v-if="deviceInfo.room">
              <span class="label">房间:</span>
              <span class="value">{{ deviceInfo.room }}</span>
            </div>
            <div class="info-item" v-if="deviceInfo.floor">
              <span class="label">楼层:</span>
              <span class="value">{{ deviceInfo.floor }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 传感器配置 -->
      <div class="info-section" v-if="deviceInfo.device_sensor_config && Object.keys(deviceInfo.device_sensor_config).length > 0">
        <h3>传感器配置</h3>
        <div class="info-card">
          <div class="card-header">
            <el-icon><Monitor /></el-icon>
            <span>传感器列表</span>
          </div>
          <div class="card-content">
            <div class="sensor-list">
              <div class="sensor-item" v-for="(config, key) in deviceInfo.device_sensor_config" :key="key">
                <div class="sensor-name">
                  <el-tag :type="config.enabled ? 'success' : 'info'" size="small">
                    {{ config.enabled ? '启用' : '禁用' }}
                  </el-tag>
                  <span>{{ config.custom_name || key }}</span>
                </div>
                <span class="sensor-key">{{ key }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 控制配置 -->
      <div class="info-section" v-if="deviceInfo.device_control_config && Object.keys(deviceInfo.device_control_config).length > 0">
        <h3>控制配置</h3>
        <div class="info-card">
          <div class="card-header">
            <el-icon><Operation /></el-icon>
            <span>控制端口列表</span>
          </div>
          <div class="card-content">
            <div class="sensor-list">
              <div class="sensor-item" v-for="(config, key) in deviceInfo.device_control_config" :key="key">
                <div class="sensor-name">
                  <el-tag :type="config.enabled ? 'success' : 'info'" size="small">
                    {{ config.enabled ? '启用' : '禁用' }}
                  </el-tag>
                  <span>{{ config.custom_name || key }}</span>
                </div>
                <span class="sensor-key">{{ key }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 预设命令 -->
      <div class="info-section" v-if="deviceInfo.device_settings?.preset_commands && deviceInfo.device_settings.preset_commands.length > 0">
        <h3>预设命令</h3>
        <div class="info-card">
          <div class="card-header">
            <el-icon><DocumentCopy /></el-icon>
            <span>命令列表</span>
          </div>
          <div class="card-content">
            <div class="preset-list">
              <div class="preset-item" v-for="(preset, index) in deviceInfo.device_settings.preset_commands" :key="index">
                <div class="preset-header">
                  <span class="preset-name">{{ preset.name }}</span>
                  <el-tag type="info" size="small">{{ preset.preset_type }}</el-tag>
                </div>
                <div class="preset-desc">{{ preset.description || '-' }}</div>
                <div class="preset-info">
                  <span>设备类型: {{ preset.device_type }}</span>
                  <span v-if="preset.steps">步骤数: {{ preset.steps.length }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 维护信息 -->
      <div class="info-section" v-if="deviceInfo.installation_date || deviceInfo.warranty_expiry || deviceInfo.last_maintenance || deviceInfo.next_maintenance">
        <h3>维护信息</h3>
        <div class="info-card">
          <div class="card-header">
            <el-icon><Tools /></el-icon>
            <span>维护记录</span>
          </div>
          <div class="card-content">
            <div class="info-item" v-if="deviceInfo.installation_date">
              <span class="label">安装日期:</span>
              <span class="value">{{ deviceInfo.installation_date }}</span>
            </div>
            <div class="info-item" v-if="deviceInfo.warranty_expiry">
              <span class="label">保修到期:</span>
              <span class="value">{{ deviceInfo.warranty_expiry }}</span>
            </div>
            <div class="info-item" v-if="deviceInfo.last_maintenance">
              <span class="label">上次维护:</span>
              <span class="value">{{ deviceInfo.last_maintenance }}</span>
            </div>
            <div class="info-item" v-if="deviceInfo.next_maintenance">
              <span class="label">下次维护:</span>
              <span class="value">{{ deviceInfo.next_maintenance }}</span>
            </div>
            <div class="info-item">
              <span class="label">错误计数:</span>
              <span class="value">{{ deviceInfo.error_count || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-else class="loading-container" v-loading="loading" element-loading-text="加载设备信息中...">
      <div style="height: 200px;"></div>
    </div>

    <!-- 编辑设备对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑设备" width="600px">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="设备位置" prop="location">
          <el-input v-model="editForm.location" placeholder="请输入设备位置" />
        </el-form-item>
        <el-form-item label="设备描述">
          <el-input v-model="editForm.description" type="textarea" rows="3" placeholder="请输入设备描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveDevice" :loading="saveLoading">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import { 
  ArrowLeft,
  Edit,
  Monitor,
  Operation,
  Setting,
  Cpu,
  Location,
  DocumentCopy,
  Tools
} from '@element-plus/icons-vue'
import { getDevice, updateDevice, getDeviceProductInfo } from '../api/device'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const loading = ref(true)
const editDialogVisible = ref(false)
const saveLoading = ref(false)
const editFormRef = ref()

// 设备信息
const deviceInfo = reactive({
  id: '',
  device_id: '',
  uuid: '',
  name: '',
  description: '',
  product_id: null,
  device_type: '',
  manufacturer: '',
  model: '',
  is_online: false,
  is_active: false,
  created_at: '',
  updated_at: '',
  firmware_version: '',
  hardware_version: '',
  serial_number: '',
  mac_address: '',
  ip_address: '',
  quality_grade: '',
  production_date: '',
  uptime: 0,
  location: '',
  group_name: '',
  room: '',
  floor: '',
  device_sensor_config: {},
  device_control_config: {},
  device_settings: null,
  installation_date: '',
  warranty_expiry: '',
  last_maintenance: '',
  next_maintenance: '',
  error_count: 0,
  last_heartbeat: '',
  last_seen: '',
  last_report_data: null
})

// 编辑表单
const editForm = reactive({
  name: '',
  location: '',
  description: ''
})

// 编辑表单验证规则
const editRules = {
  name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' }
  ]
}

// 判断当前用户是否是设备所有者
const isDeviceOwner = computed(() => {
  // 管理员可以编辑所有设备
  if (userStore.isPlatformAdmin || userStore.isSchoolAdmin) {
    return true
  }
  
  // 检查是否是设备所有者
  if (!deviceInfo.user_id || !userStore.user?.id) {
    return false
  }
  
  return deviceInfo.user_id === userStore.user.id
})

// 返回设备列表
const goBack = () => {
  router.push('/device/devices')
}

// 加载设备信息
const loadDeviceInfo = async () => {
  try {
    const uuid = route.params.uuid
    if (!uuid) {
      ElMessage.error('设备UUID参数缺失')
      goBack()
      return
    }

    // 调用真实的API获取设备信息
    const res = await getDevice(uuid)
    const response = res.data // 获取响应数据
    
    console.log('设备详情数据:', response) // 添加调试日志
    
    // 尝试获取产品信息（如果设备有关联产品）
    let productInfo = null
    if (response.product_id) {
      try {
        const productRes = await getDeviceProductInfo(uuid)
        productInfo = productRes.data
      } catch (error) {
        console.warn('获取产品信息失败:', error)
      }
    }
    
    // 更新设备信息 - 直接使用后台返回的所有字段
    Object.assign(deviceInfo, {
      // 基本信息
      id: response.id,
      device_id: response.device_id,
      uuid: response.uuid,
      name: response.name,
      description: response.description,
      product_id: response.product_id,
      user_id: response.user_id,  // 添加用户ID用于权限判断
      
      // 从产品信息获取或使用默认值
      device_type: productInfo?.product_name || productInfo?.product_code || '未绑定产品',
      manufacturer: productInfo?.manufacturer || '未知',
      model: productInfo?.hardware_version || productInfo?.product_code || '未知',
      
      // 状态信息
      is_online: response.is_online,
      is_active: response.is_active,
      
      // 硬件信息
      firmware_version: response.firmware_version,
      hardware_version: response.hardware_version,
      serial_number: response.serial_number,
      mac_address: response.mac_address,
      ip_address: response.ip_address,
      quality_grade: response.quality_grade,
      production_date: response.production_date,
      uptime: response.uptime,
      
      // 位置信息
      location: response.location,
      group_name: response.group_name,
      room: response.room,
      floor: response.floor,
      
      // 配置信息
      device_sensor_config: response.device_sensor_config || {},
      device_control_config: response.device_control_config || {},
      device_settings: response.device_settings,
      
      // 时间信息
      created_at: response.created_at,
      updated_at: response.updated_at,
      last_heartbeat: response.last_heartbeat,
      last_seen: response.last_seen,
      
      // 维护信息
      installation_date: response.installation_date,
      warranty_expiry: response.warranty_expiry,
      last_maintenance: response.last_maintenance,
      next_maintenance: response.next_maintenance,
      
      // 其他
      error_count: response.error_count,
      last_report_data: response.last_report_data
    })
    
    // 填充编辑表单
    Object.assign(editForm, {
      name: deviceInfo.name,
      location: deviceInfo.location,
      description: deviceInfo.description
    })
    
  } catch (error) {
    ElMessage.error('加载设备信息失败: ' + (error.response?.data?.detail || error.message))
    console.error('Load device error:', error)
    // 如果设备不存在或无权限，返回列表页
    if (error.response?.status === 404 || error.response?.status === 403) {
      setTimeout(() => goBack(), 1500)
    }
  } finally {
    loading.value = false
  }
}

// 保存设备信息
const saveDevice = async () => {
  if (!editFormRef.value) return
  
  try {
    await editFormRef.value.validate()
    saveLoading.value = true
    
    // 调用真实的API更新设备信息
    const updateData = {
      name: editForm.name,
      location: editForm.location,
      description: editForm.description
    }
    
    await updateDevice(deviceInfo.uuid, updateData)
    
    // 更新本地设备信息
    Object.assign(deviceInfo, editForm)
    
    ElMessage.success('设备信息已更新')
    editDialogVisible.value = false
  } catch (error) {
    if (error !== false) { // 不是验证失败
      const errorMsg = error.response?.data?.detail || error.message || '保存设备信息失败'
      ElMessage.error(errorMsg)
      console.error('Save device error:', error)
    }
  } finally {
    saveLoading.value = false
  }
}


// 组件挂载
onMounted(() => {
  loadDeviceInfo()
})
</script>

<style scoped>
.device-detail-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.page-header {
  background: white;
  padding: 20px 24px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  color: #409eff;
  font-size: 14px;
}

.page-title h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 20px;
}

.device-tags {
  display: flex;
  gap: 8px;
}

.header-controls {
  display: flex;
  gap: 12px;
}

.page-content {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.info-section h3 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 18px;
  text-align: center;
}

.info-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #e4e7ed;
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label {
  color: #606266;
  font-size: 14px;
}

.value {
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}


.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 50vh;
}

/* 传感器和控制列表样式 */
.sensor-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sensor-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.sensor-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.sensor-key {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
}

/* 预设命令列表样式 */
.preset-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preset-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.preset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.preset-name {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.preset-desc {
  font-size: 13px;
  color: #606266;
  margin-bottom: 8px;
}

.preset-info {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #909399;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-controls {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .info-card {
    max-width: 100%;
  }
  
  .sensor-item,
  .preset-item {
    flex-direction: column;
    gap: 8px;
  }
}
</style>