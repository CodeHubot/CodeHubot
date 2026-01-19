<template>
  <div class="module-config-container">
    <div class="page-header">
      <h2>模块配置管理</h2>
    </div>

    <el-alert
      title="提示"
      type="info"
      description="管理系统各个功能模块的启用状态，关闭的模块将在系统中隐藏相关功能入口。修改后需刷新页面生效。"
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

        <!-- AI模块子功能（仅在AI模块开启时显示） -->
        <template v-if="moduleConfig.enable_ai_module">
          <el-divider content-position="left">
            <el-text type="info" size="small">AI模块子功能配置</el-text>
          </el-divider>

          <!-- 知识库功能 -->
          <el-form-item>
            <template #label>
              <div class="form-label sub-label">
                <el-icon><Reading /></el-icon>
                <span>知识库功能</span>
              </div>
            </template>
            <div class="form-control">
              <el-switch
                v-model="featureConfig.ai_module_knowledge_base_enabled"
                active-text="开启"
                inactive-text="关闭"
                size="default"
              />
              <span class="description">RAG知识库功能（暂未开放）</span>
            </div>
          </el-form-item>

          <!-- 工作流功能 -->
          <el-form-item>
            <template #label>
              <div class="form-label sub-label">
                <el-icon><Connection /></el-icon>
                <span>工作流编排</span>
              </div>
            </template>
            <div class="form-control">
              <el-switch
                v-model="featureConfig.ai_module_workflow_enabled"
                active-text="开启"
                inactive-text="关闭"
                size="default"
              />
              <span class="description">工作流编排功能（暂未开放）</span>
            </div>
          </el-form-item>

          <!-- 对话功能 -->
          <el-form-item>
            <template #label>
              <div class="form-label sub-label">
                <el-icon><ChatDotRound /></el-icon>
                <span>对话功能</span>
              </div>
            </template>
            <div class="form-control">
              <el-switch
                v-model="featureConfig.ai_module_agent_enabled"
                active-text="开启"
                inactive-text="关闭"
                size="default"
              />
              <span class="description">AI智能体对话功能</span>
            </div>
          </el-form-item>

          <!-- 插件系统 -->
          <el-form-item>
            <template #label>
              <div class="form-label sub-label">
                <el-icon><Grid /></el-icon>
                <span>插件系统</span>
              </div>
            </template>
            <div class="form-control">
              <el-switch
                v-model="featureConfig.ai_module_prompt_template_enabled"
                active-text="开启"
                inactive-text="关闭"
                size="default"
              />
              <span class="description">提示词模板和插件功能</span>
            </div>
          </el-form-item>
        </template>

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

      <!-- AI子功能状态 -->
      <el-descriptions 
        v-if="moduleConfig.enable_ai_module" 
        :column="2" 
        border 
        style="margin-top: 16px"
        title="AI模块子功能状态"
      >
        <el-descriptions-item label="知识库功能">
          <el-tag :type="featureConfig.ai_module_knowledge_base_enabled ? 'success' : 'info'" size="small">
            {{ featureConfig.ai_module_knowledge_base_enabled ? '已开启' : '已关闭' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="工作流编排">
          <el-tag :type="featureConfig.ai_module_workflow_enabled ? 'success' : 'info'" size="small">
            {{ featureConfig.ai_module_workflow_enabled ? '已开启' : '已关闭' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="对话功能">
          <el-tag :type="featureConfig.ai_module_agent_enabled ? 'success' : 'info'" size="small">
            {{ featureConfig.ai_module_agent_enabled ? '已开启' : '已关闭' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="插件系统">
          <el-tag :type="featureConfig.ai_module_prompt_template_enabled ? 'success' : 'info'" size="small">
            {{ featureConfig.ai_module_prompt_template_enabled ? '已开启' : '已关闭' }}
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
        <el-timeline-item timestamp="功能说明" placement="top">
          <el-text>通过开关控制各功能模块的可见性和可用性</el-text>
        </el-timeline-item>
        <el-timeline-item timestamp="使用方法" placement="top">
          <el-text>根据实际需求开启或关闭相应的功能模块，然后点击"保存配置"按钮</el-text>
        </el-timeline-item>
        <el-timeline-item timestamp="生效方式" placement="top">
          <el-text type="warning">配置保存后需要刷新页面才能完全生效</el-text>
        </el-timeline-item>
        <el-timeline-item timestamp="注意事项" placement="top">
          <el-text type="danger">关闭模块后，相关功能入口将对所有用户隐藏</el-text>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Check, UserFilled, Monitor, MagicStick, Reading, Connection, ChatDotRound, Grid
} from '@element-plus/icons-vue'
import request from '@/utils/request'

const loading = ref(false)
const saving = ref(false)

const moduleConfig = reactive({
  enable_user_registration: true,
  enable_device_module: true,
  enable_ai_module: true
})

// AI功能配置
const featureConfig = reactive({
  ai_module_knowledge_base_enabled: false,
  ai_module_workflow_enabled: false,
  ai_module_agent_enabled: true,
  ai_module_prompt_template_enabled: true
})

// 获取模块配置
const fetchConfig = async () => {
  loading.value = true
  try {
    const response = await request.get('/system-config/modules')
    Object.assign(moduleConfig, response.data)
    
    // 获取AI功能配置
    const featureResponse = await request.get('/system-config/configs/public')
    const configs = featureResponse.data || []
    
    // 映射AI功能配置
    configs.forEach(config => {
      if (config.config_key in featureConfig) {
        featureConfig[config.config_key] = config.config_value === 'true'
      }
    })
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
    
    // 保存模块配置
    const response = await request.put('/system-config/modules', moduleConfig)
    Object.assign(moduleConfig, response.data)
    
    // 保存AI功能配置
    if (moduleConfig.enable_ai_module) {
      await Promise.all([
        request.put('/system-config/configs/ai_module_knowledge_base_enabled', {
          config_value: featureConfig.ai_module_knowledge_base_enabled.toString()
        }),
        request.put('/system-config/configs/ai_module_workflow_enabled', {
          config_value: featureConfig.ai_module_workflow_enabled.toString()
        }),
        request.put('/system-config/configs/ai_module_agent_enabled', {
          config_value: featureConfig.ai_module_agent_enabled.toString()
        }),
        request.put('/system-config/configs/ai_module_prompt_template_enabled', {
          config_value: featureConfig.ai_module_prompt_template_enabled.toString()
        })
      ])
    }
    
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

.form-label.sub-label {
  font-size: 14px;
  font-weight: normal;
  padding-left: 20px;
  color: #606266;
}

.form-label.sub-label .el-icon {
  font-size: 14px;
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
