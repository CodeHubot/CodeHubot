<template>
  <div class="mqtt-config-container">
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span>
            <el-icon><Connection /></el-icon>
            MQTT服务器配置
          </span>
          <el-button
            type="primary"
            :icon="Refresh"
            @click="loadConfig"
            :loading="loading"
          >
            刷新
          </el-button>
        </div>
      </template>

      <el-alert
        title="配置说明"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 24px"
      >
        <p>此配置用于设备连接MQTT服务器，修改后请点击"刷新config-service缓存"按钮使配置生效。</p>
        <p><strong>重要：</strong>MQTT Broker地址必须是设备可以访问的外部地址（域名或公网IP），不能使用localhost。</p>
      </el-alert>

      <el-form
        ref="formRef"
        :model="config"
        :rules="rules"
        label-width="160px"
        :disabled="!isEditing"
      >
        <el-form-item label="MQTT Broker地址" prop="device_mqtt_broker">
          <el-input
            v-model="config.device_mqtt_broker"
            placeholder="例如: mqtt.example.com 或 192.168.1.100"
            clearable
          >
            <template #prepend>
              <el-icon><Link /></el-icon>
            </template>
          </el-input>
          <div class="form-item-tip">
            设备将连接到此MQTT服务器地址
          </div>
        </el-form-item>

        <el-form-item label="MQTT端口" prop="device_mqtt_port">
          <el-input-number
            v-model="config.device_mqtt_port"
            :min="1"
            :max="65535"
            :step="1"
            style="width: 200px"
          />
          <div class="form-item-tip">
            标准MQTT端口：1883（无SSL）或 8883（SSL）
          </div>
        </el-form-item>

        <el-form-item label="启用SSL/TLS" prop="device_mqtt_use_ssl">
          <el-switch
            v-model="config.device_mqtt_use_ssl"
            active-text="启用"
            inactive-text="禁用"
          />
          <div class="form-item-tip">
            启用后设备将使用加密连接，建议生产环境启用
          </div>
        </el-form-item>
      </el-form>

      <!-- 操作按钮放在表单外面，避免被表单的disabled影响 -->
      <div style="margin-top: 20px; padding-left: 160px">
        <el-button
          v-if="!isEditing"
          type="primary"
          :icon="Edit"
          @click="startEdit"
        >
          编辑配置
        </el-button>
        <template v-else>
          <el-button
            type="primary"
            :icon="Check"
            @click="saveConfig"
            :loading="saving"
          >
            保存配置
          </el-button>
          <el-button
            :icon="Close"
            @click="cancelEdit"
          >
            取消
          </el-button>
        </template>
      </div>
    </el-card>

    <!-- Config Service 缓存刷新 -->
    <el-card class="config-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>
            <el-icon><RefreshRight /></el-icon>
            配置缓存管理
          </span>
        </div>
      </template>

      <el-alert
        title="配置更新流程"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 24px"
      >
        <ol style="margin: 8px 0; padding-left: 20px">
          <li>修改MQTT配置并保存</li>
          <li>点击下方"刷新config-service缓存"按钮</li>
          <li>配置立即生效，设备下次请求时获取新配置</li>
        </ol>
      </el-alert>

      <div class="cache-status" v-if="cacheStatus">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="当前Broker">
            {{ cacheStatus.current_mqtt_config?.broker || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="当前端口">
            {{ cacheStatus.current_mqtt_config?.port || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="SSL状态">
            <el-tag :type="cacheStatus.current_mqtt_config?.use_ssl ? 'success' : 'info'">
              {{ cacheStatus.current_mqtt_config?.use_ssl ? '已启用' : '未启用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="上次刷新时间">
            {{ cacheStatus.timestamp ? formatTime(cacheStatus.timestamp) : '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <div style="margin-top: 20px">
        <el-button
          type="success"
          :icon="RefreshRight"
          @click="refreshConfigCache"
          :loading="refreshing"
        >
          刷新config-service缓存
        </el-button>
        <el-button
          :icon="View"
          @click="checkConfigServiceStatus"
          :loading="checking"
        >
          查看config-service状态
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Connection,
  Link,
  Edit,
  Check,
  Close,
  Refresh,
  RefreshRight,
  View
} from '@element-plus/icons-vue'
import request from '@/utils/request'

// 表单引用
const formRef = ref(null)

// 加载状态
const loading = ref(false)
const saving = ref(false)
const refreshing = ref(false)
const checking = ref(false)

// 编辑状态
const isEditing = ref(false)

// 配置数据
const config = reactive({
  device_mqtt_broker: '',
  device_mqtt_port: 1883,
  device_mqtt_use_ssl: false
})

// 备份原始数据
const originalConfig = reactive({})

// 缓存状态
const cacheStatus = ref(null)

// 表单验证规则
const rules = {
  device_mqtt_broker: [
    { required: true, message: '请输入MQTT Broker地址', trigger: 'blur' },
    { min: 3, max: 255, message: '地址长度在3-255个字符之间', trigger: 'blur' },
    {
      pattern: /^(?!.*localhost).*$/,
      message: '不能使用localhost，请使用设备可访问的外部地址',
      trigger: 'blur'
    }
  ],
  device_mqtt_port: [
    { required: true, message: '请输入MQTT端口', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口范围：1-65535', trigger: 'blur' }
  ]
}

// 加载配置
const loadConfig = async () => {
  loading.value = true
  try {
    const response = await request.get('/system-config/device-mqtt')
    Object.assign(config, response.data)
    Object.assign(originalConfig, response.data)
    ElMessage.success('配置加载成功')
  } catch (error) {
    console.error('加载配置失败:', error)
    ElMessage.error(error.message || '加载配置失败')
  } finally {
    loading.value = false
  }
}

// 开始编辑
const startEdit = () => {
  isEditing.value = true
}

// 取消编辑
const cancelEdit = () => {
  Object.assign(config, originalConfig)
  isEditing.value = false
  formRef.value?.clearValidate()
}

// 保存配置
const saveConfig = async () => {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  try {
    await ElMessageBox.confirm(
      '确定要保存MQTT配置吗？保存后需要刷新config-service缓存才能生效。',
      '确认保存',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }

  saving.value = true
  try {
    const response = await request.put('/system-config/device-mqtt', config)
    Object.assign(config, response.data)
    Object.assign(originalConfig, response.data)
    isEditing.value = false
    ElMessage.success('配置保存成功，请刷新config-service缓存使配置生效')
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error(error.message || '保存配置失败')
  } finally {
    saving.value = false
  }
}

// 刷新config-service缓存
const refreshConfigCache = async () => {
  refreshing.value = true
  try {
    // 调用config-service的刷新接口
    const response = await fetch('http://localhost:8001/admin/refresh-config', {
      method: 'POST'
    })
    
    if (!response.ok) {
      throw new Error('刷新失败')
    }
    
    const result = await response.json()
    cacheStatus.value = result
    
    ElMessage.success({
      message: '配置缓存已刷新，新配置立即生效',
      duration: 3000
    })
  } catch (error) {
    console.error('刷新缓存失败:', error)
    ElMessage.error('刷新缓存失败，请检查config-service是否正常运行')
  } finally {
    refreshing.value = false
  }
}

// 查看config-service状态
const checkConfigServiceStatus = async () => {
  checking.value = true
  try {
    const response = await fetch('http://localhost:8001/')
    
    if (!response.ok) {
      throw new Error('服务异常')
    }
    
    const result = await response.json()
    
    await ElMessageBox.alert(
      `
        <p><strong>服务状态：</strong>${result.status}</p>
        <p><strong>服务版本：</strong>${result.version}</p>
        <p><strong>MQTT Broker：</strong>${result.mqtt_config?.broker}</p>
        <p><strong>MQTT端口：</strong>${result.mqtt_config?.port}</p>
        <p><strong>SSL状态：</strong>${result.mqtt_config?.use_ssl ? '已启用' : '未启用'}</p>
        <p><strong>配置来源：</strong>${result.mqtt_config?.source}</p>
      `,
      'Config Service 状态',
      {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '确定'
      }
    )
  } catch (error) {
    console.error('检查服务状态失败:', error)
    ElMessage.error('无法连接到config-service，请检查服务是否正常运行')
  } finally {
    checking.value = false
  }
}

// 格式化时间
const formatTime = (isoString) => {
  if (!isoString) return '-'
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 初始化
onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.mqtt-config-container {
  padding: 24px;
}

.config-card {
  max-width: 800px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.card-header span {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-item-tip {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-top: 4px;
}

.cache-status {
  margin-bottom: 20px;
}

:deep(.el-descriptions__label) {
  width: 150px;
}

:deep(.el-alert__description) {
  margin: 0;
}

:deep(.el-alert__description p) {
  margin: 4px 0;
}

:deep(.el-alert__description ol) {
  line-height: 1.8;
}
</style>
