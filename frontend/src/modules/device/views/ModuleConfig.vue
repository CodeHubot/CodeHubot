<template>
  <div class="module-config-container">
    <div class="page-header">
      <h2>模块配置管理</h2>
      <el-button type="primary" @click="initConfig" :loading="initializing">
        <el-icon><Setting /></el-icon>
        初始化配置
      </el-button>
    </div>

    <el-alert
      title="提示"
      type="info"
      description="管理系统各个功能模块的启用状态，关闭的模块将在系统中隐藏相关功能入口。"
      :closable="false"
      style="margin-bottom: 20px;"
    />

    <el-card class="module-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>功能模块配置</span>
          <el-button type="success" @click="saveConfig" :loading="saving">
            <el-icon><Check /></el-icon>
            保存配置
          </el-button>
        </div>
      </template>

      <el-form :model="moduleConfig" label-width="180px" class="module-form">
        <!-- 用户注册 -->
        <el-form-item>
          <template #label>
            <div class="form-label">
              <el-icon><UserFilled /></el-icon>
              <span>用户注册功能</span>
            </div>
          </template>
          <div class="form-control">
            <el-switch
              v-model="moduleConfig.enable_user_registration"
              active-text="开启"
              inactive-text="关闭"
              size="large"
            />
            <span class="description">控制是否允许新用户注册账号</span>
          </div>
        </el-form-item>

        <el-divider />

        <!-- 设备管理模块 -->
        <el-form-item>
          <template #label>
            <div class="form-label">
              <el-icon><Monitor /></el-icon>
              <span>设备管理模块</span>
            </div>
          </template>
          <div class="form-control">
            <el-switch
              v-model="moduleConfig.enable_device_module"
              active-text="开启"
              inactive-text="关闭"
              size="large"
            />
            <span class="description">包含设备管理、产品管理、固件管理等功能</span>
          </div>
        </el-form-item>

        <el-divider />

        <!-- AI模块 -->
        <el-form-item>
          <template #label>
            <div class="form-label">
              <el-icon><MagicStick /></el-icon>
              <span>AI智能模块</span>
            </div>
          </template>
          <div class="form-control">
            <el-switch
              v-model="moduleConfig.enable_ai_module"
              active-text="开启"
              inactive-text="关闭"
              size="large"
            />
            <span class="description">包含AI智能体、知识库、LLM模型、插件、工作流等功能</span>
          </div>
        </el-form-item>

      </el-form>
    </el-card>

    <!-- 当前配置状态 -->
    <el-card class="status-card" style="margin-top: 20px;">
      <template #header>
        <span>当前配置状态</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用户注册">
          <el-tag :type="moduleConfig.enable_user_registration ? 'success' : 'danger'">
            {{ moduleConfig.enable_user_registration ? '已开启' : '已关闭' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="设备管理模块">
          <el-tag :type="moduleConfig.enable_device_module ? 'success' : 'danger'">
            {{ moduleConfig.enable_device_module ? '已开启' : '已关闭' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="AI智能模块">
          <el-tag :type="moduleConfig.enable_ai_module ? 'success' : 'danger'">
            {{ moduleConfig.enable_ai_module ? '已开启' : '已关闭' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 操作说明 -->
    <el-card class="help-card" style="margin-top: 20px;">
      <template #header>
        <span>配置说明</span>
      </template>
      <el-timeline>
        <el-timeline-item timestamp="第一步" placement="top">
          <el-text>首次使用请点击"初始化配置"按钮，创建默认配置项</el-text>
        </el-timeline-item>
        <el-timeline-item timestamp="第二步" placement="top">
          <el-text>根据实际需求开启或关闭相应的功能模块</el-text>
        </el-timeline-item>
        <el-timeline-item timestamp="第三步" placement="top">
          <el-text>点击"保存配置"按钮使配置生效</el-text>
        </el-timeline-item>
        <el-timeline-item timestamp="第四步" placement="top">
          <el-text type="warning">部分配置可能需要刷新页面或重新登录后生效</el-text>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Setting, Check, UserFilled, Monitor, MagicStick, Reading 
} from '@element-plus/icons-vue'
import request from '@/utils/request'

const loading = ref(false)
const saving = ref(false)
const initializing = ref(false)

const moduleConfig = reactive({
  enable_user_registration: true,
  enable_device_module: true,
  enable_ai_module: true
})

// 获取模块配置
const fetchConfig = async () => {
  loading.value = true
  try {
    const response = await request.get('/system-config/modules')
    Object.assign(moduleConfig, response.data)
  } catch (error) {
    console.error('获取模块配置失败:', error)
    ElMessage.error(error.response?.data?.detail || '获取模块配置失败')
  } finally {
    loading.value = false
  }
}

// 保存配置
const saveConfig = async () => {
  try {
    await ElMessageBox.confirm(
      '修改模块配置可能会影响系统功能的可用性，确定要保存吗？',
      '确认保存',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    saving.value = true
    const response = await request.put('/system-config/modules', moduleConfig)
    Object.assign(moduleConfig, response.data)
    ElMessage.success('配置保存成功')
    
    // 提示用户刷新页面
    ElMessageBox.alert(
      '配置已保存，建议刷新页面以使配置完全生效。',
      '提示',
      {
        confirmButtonText: '刷新页面',
        callback: () => {
          window.location.reload()
        }
      }
    )
  } catch (error) {
    if (error !== 'cancel') {
      console.error('保存配置失败:', error)
      ElMessage.error(error.response?.data?.detail || '保存配置失败')
    }
  } finally {
    saving.value = false
  }
}

// 初始化配置
const initConfig = async () => {
  try {
    await ElMessageBox.confirm(
      '此操作将创建默认的模块配置（如果不存在）。已存在的配置不会被覆盖。',
      '确认初始化',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    initializing.value = true
    const response = await request.post('/system-config/modules/init')
    ElMessage.success(response.data.message || '配置初始化成功')
    
    // 重新获取配置
    await fetchConfig()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('初始化配置失败:', error)
      ElMessage.error(error.response?.data?.detail || '初始化配置失败')
    }
  } finally {
    initializing.value = false
  }
}

onMounted(() => {
  fetchConfig()
})
</script>

<style scoped>
.module-config-container {
  padding: 20px;
  max-width: 1200px;
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
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.module-form {
  padding: 20px 0;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
}

.form-control {
  display: flex;
  align-items: center;
  gap: 20px;
}

.form-control .description {
  color: #909399;
  font-size: 13px;
  flex: 1;
}

.module-card,
.status-card,
.help-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

:deep(.el-divider) {
  margin: 24px 0;
}

:deep(.el-form-item) {
  margin-bottom: 0;
}

:deep(.el-switch.is-checked .el-switch__core) {
  background-color: #67c23a;
}
</style>
