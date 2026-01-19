<template>
  <div class="server-config-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>服务器信息配置</h2>
      <el-button
        type="primary"
        :icon="Refresh"
        @click="loadConfig"
        :loading="loading"
      >
        刷新配置
      </el-button>
    </div>

    <el-alert
      title="配置说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 20px"
    >
      <p><strong>重要提示：</strong>所有服务器地址必须是设备可以访问的外部地址（域名或公网IP），不能使用localhost。</p>
      <p>修改配置后，需要点击底部的"应用配置"按钮使配置立即生效。</p>
    </el-alert>

    <!-- MQTT服务器配置 -->
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <el-icon><Connection /></el-icon>
            <span>MQTT服务器配置</span>
          </div>
        </div>
      </template>

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
            设备将连接到此MQTT服务器进行消息通信
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
            标准端口：1883（无SSL）、8883（SSL）
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
    </el-card>

    <!-- 配置服务器 -->
    <el-card class="config-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <el-icon><Setting /></el-icon>
            <span>设备配置服务器</span>
          </div>
        </div>
      </template>

      <el-form
        :model="config"
        :rules="rules"
        label-width="160px"
        :disabled="!isEditing"
      >
        <el-form-item label="配置服务器地址" prop="device_config_server_url">
          <el-input
            v-model="config.device_config_server_url"
            placeholder="例如: http://config.example.com:8001"
            clearable
          >
            <template #prepend>
              <el-icon><Link /></el-icon>
            </template>
          </el-input>
          <div class="form-item-tip">
            设备配网时填写此地址，自动获取MQTT等配置信息
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作按钮区 -->
    <el-card class="action-card" style="margin-top: 20px">
      <div class="action-buttons">
        <template v-if="!isEditing">
          <el-button
            type="primary"
            :icon="Edit"
            @click="startEdit"
            size="large"
          >
            编辑配置
          </el-button>
        </template>
        <template v-else>
          <el-button
            type="success"
            :icon="Check"
            @click="saveAndApplyConfig"
            :loading="saving"
            size="large"
          >
            保存并应用配置
          </el-button>
          <el-button
            :icon="Close"
            @click="cancelEdit"
            size="large"
          >
            取消
          </el-button>
        </template>
        
        <el-divider direction="vertical" style="height: 32px; margin: 0 16px" />
        
        <el-button
          :icon="View"
          @click="checkConfigServiceStatus"
          :loading="checking"
          size="large"
        >
          查看服务状态
        </el-button>
      </div>

      <el-alert
        v-if="lastApplyTime"
        type="success"
        :closable="false"
        style="margin-top: 16px"
      >
        <template #title>
          <span>✓ 配置已应用，最后更新时间：{{ formatTime(lastApplyTime) }}</span>
        </template>
      </el-alert>
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
  View,
  Setting
} from '@element-plus/icons-vue'
import request from '@/utils/request'

// 表单引用
const formRef = ref(null)

// 加载状态
const loading = ref(false)
const saving = ref(false)
const checking = ref(false)

// 编辑状态
const isEditing = ref(false)

// 最后应用时间
const lastApplyTime = ref(null)

// 配置数据
const config = reactive({
  device_mqtt_broker: '',
  device_mqtt_port: 1883,
  device_mqtt_use_ssl: false,
  device_config_server_url: ''
})

// 备份原始数据
const originalConfig = reactive({})

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
  ],
  device_config_server_url: [
    { required: true, message: '请输入配置服务器地址', trigger: 'blur' },
    { min: 3, max: 255, message: '地址长度在3-255个字符之间', trigger: 'blur' },
    {
      pattern: /^https?:\/\/.+/,
      message: '请输入有效的HTTP/HTTPS地址',
      trigger: 'blur'
    },
    {
      pattern: /^(?!.*localhost).*$/,
      message: '不能使用localhost，请使用设备可访问的外部地址',
      trigger: 'blur'
    }
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

// 保存并应用配置
const saveAndApplyConfig = async () => {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  try {
    await ElMessageBox.confirm(
      '保存配置后将立即应用到config-service，设备下次连接时将获取新配置。确定要保存吗？',
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
    // 1. 保存配置到数据库
    const response = await request.put('/system-config/device-mqtt', config)
    Object.assign(config, response.data)
    Object.assign(originalConfig, response.data)
    
    // 2. 刷新config-service缓存
    try {
      const refreshResponse = await fetch('http://localhost:8001/admin/refresh-config', {
        method: 'POST'
      })
      
      if (refreshResponse.ok) {
        lastApplyTime.value = new Date().toISOString()
        ElMessage.success('配置已保存并应用，立即生效')
      } else {
        ElMessage.warning('配置已保存，但应用失败，请检查config-service服务')
      }
    } catch (refreshError) {
      console.error('应用配置失败:', refreshError)
      ElMessage.warning('配置已保存，但应用失败，请手动检查config-service服务')
    }
    
    isEditing.value = false
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error(error.message || '保存配置失败')
  } finally {
    saving.value = false
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
        <div style="line-height: 1.8;">
          <p><strong>服务状态：</strong>${result.status || '运行中'}</p>
          <p><strong>服务版本：</strong>${result.version || '-'}</p>
          <hr style="margin: 12px 0; border: none; border-top: 1px solid #eee;">
          <p style="margin-top: 12px;"><strong>当前MQTT配置：</strong></p>
          <p style="padding-left: 20px;">• Broker：${result.mqtt_config?.broker || '-'}</p>
          <p style="padding-left: 20px;">• 端口：${result.mqtt_config?.port || '-'}</p>
          <p style="padding-left: 20px;">• SSL：${result.mqtt_config?.use_ssl ? '已启用' : '未启用'}</p>
          <p style="padding-left: 20px;">• 来源：${result.mqtt_config?.source || '-'}</p>
        </div>
      `,
      'Config Service 服务状态',
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
.server-config-container {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.config-card,
.action-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-item-tip {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-top: 4px;
}

.action-card {
  background: #f9fafb;
}

.action-buttons {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 0;
}

:deep(.el-alert__description) {
  margin: 0;
}

:deep(.el-alert__description p) {
  margin: 4px 0;
}
</style>
