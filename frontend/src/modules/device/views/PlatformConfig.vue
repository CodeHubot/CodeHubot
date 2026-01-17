<template>
  <div class="platform-config-container">
    <div class="page-header">
      <h2>系统配置管理</h2>
      <el-button type="primary" @click="initConfig" :loading="initializing">
        <el-icon><Setting /></el-icon>
        初始化配置
      </el-button>
    </div>

    <el-alert
      title="提示"
      type="info"
      description="配置平台基础信息和功能开关。修改后可能需要刷新页面生效。"
      :closable="false"
      style="margin-bottom: 20px;"
    />

    <!-- 平台基础配置 -->
    <el-card class="config-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <el-icon><Setting /></el-icon>
            <span>平台基础配置</span>
          </div>
          <el-button type="success" @click="savePlatformConfig" :loading="saving">
            <el-icon><Check /></el-icon>
            保存配置
          </el-button>
        </div>
      </template>

      <el-form :model="platformConfig" label-width="140px" class="config-form">
        <!-- 平台名称 -->
        <el-form-item label="平台名称">
          <el-input
            v-model="platformConfig.platform_name"
            placeholder="请输入平台名称（如：CodeHubot）"
            maxlength="50"
            show-word-limit
            clearable
          >
            <template #prepend>
              <el-icon><Shop /></el-icon>
            </template>
          </el-input>
          <div class="form-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>将显示在登录页、导航栏等位置，建议不超过20个字符</span>
          </div>
        </el-form-item>

        <!-- 平台描述 -->
        <el-form-item label="平台描述">
          <el-input
            v-model="platformConfig.platform_description"
            placeholder="请输入平台描述"
            maxlength="200"
            show-word-limit
            type="textarea"
            :rows="3"
          />
          <div class="form-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>平台简介，将显示在登录页等位置</span>
          </div>
        </el-form-item>

        <el-divider />

        <!-- 用户注册开关 -->
        <el-form-item label="用户注册功能">
          <div class="switch-control">
            <el-switch
              v-model="platformConfig.enable_user_registration"
              active-text="开启"
              inactive-text="关闭"
              size="large"
            />
            <div class="switch-description">
              <el-icon><UserFilled /></el-icon>
              <span>控制是否允许新用户通过注册页面注册账号</span>
            </div>
          </div>
          <el-alert
            v-if="!platformConfig.enable_user_registration"
            title="注册功能已关闭"
            type="warning"
            description="关闭后，普通用户无法自主注册，只能由管理员创建账号"
            :closable="false"
            style="margin-top: 10px;"
          />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户协议和隐私政策配置 -->
    <el-card class="config-card" style="margin-top: 20px;" v-loading="loading">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <el-icon><Document /></el-icon>
            <span>用户协议与隐私政策</span>
          </div>
          <el-button type="success" @click="savePoliciesConfig" :loading="policiesSaving">
            <el-icon><Check /></el-icon>
            保存配置
          </el-button>
        </div>
      </template>

      <el-form :model="policiesConfig" label-width="140px" class="config-form">
        <!-- 用户协议 -->
        <el-form-item label="用户协议">
          <el-input
            v-model="policiesConfig.user_agreement"
            type="textarea"
            :rows="10"
            placeholder="请输入用户协议内容（支持HTML格式）"
          />
          <div class="form-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>支持HTML格式，将在用户登录页面底部显示</span>
          </div>
        </el-form-item>

        <el-divider />

        <!-- 隐私政策 -->
        <el-form-item label="隐私政策">
          <el-input
            v-model="policiesConfig.privacy_policy"
            type="textarea"
            :rows="10"
            placeholder="请输入隐私政策内容（支持HTML格式）"
          />
          <div class="form-tip">
            <el-icon><InfoFilled /></el-icon>
            <span>支持HTML格式，将在用户登录页面底部显示</span>
          </div>
        </el-form-item>

        <!-- 预览按钮 -->
        <el-form-item>
          <el-button @click="previewUserAgreement" :disabled="!policiesConfig.user_agreement">
            <el-icon><View /></el-icon>
            预览用户协议
          </el-button>
          <el-button @click="previewPrivacyPolicy" :disabled="!policiesConfig.privacy_policy">
            <el-icon><View /></el-icon>
            预览隐私政策
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 模块功能配置 -->
    <el-card class="config-card" style="margin-top: 20px;" v-loading="loading">
      <template #header>
        <div class="card-header">
          <div class="header-title">
            <el-icon><Grid /></el-icon>
            <span>功能模块配置</span>
          </div>
          <el-button type="success" @click="saveModuleConfig" :loading="moduleSaving">
            <el-icon><Check /></el-icon>
            保存配置
          </el-button>
        </div>
      </template>

      <el-form :model="moduleConfig" label-width="140px" class="config-form">
        <!-- 设备管理模块 -->
        <el-form-item label="设备管理模块">
          <div class="switch-control">
            <el-switch
              v-model="moduleConfig.enable_device_module"
              active-text="开启"
              inactive-text="关闭"
              size="large"
            />
            <div class="switch-description">
              <el-icon><Monitor /></el-icon>
              <span>包含设备管理、产品管理、固件管理等功能</span>
            </div>
          </div>
        </el-form-item>

        <el-divider />

        <!-- AI模块 -->
        <el-form-item label="AI智能模块">
          <div class="switch-control">
            <el-switch
              v-model="moduleConfig.enable_ai_module"
              active-text="开启"
              inactive-text="关闭"
              size="large"
            />
            <div class="switch-description">
              <el-icon><MagicStick /></el-icon>
              <span>包含AI智能体、知识库、LLM模型、插件、工作流等功能</span>
            </div>
          </div>
        </el-form-item>

      </el-form>
    </el-card>

    <!-- 当前配置状态 -->
    <el-card class="status-card" style="margin-top: 20px;">
      <template #header>
        <div class="header-title">
          <el-icon><View /></el-icon>
          <span>当前配置状态</span>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="平台名称">
          <el-tag type="info">{{ platformConfig.platform_name || '未设置' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="用户注册">
          <el-tag :type="platformConfig.enable_user_registration ? 'success' : 'danger'">
            {{ platformConfig.enable_user_registration ? '已开启' : '已关闭' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="设备管理模块">
          <el-tag :type="moduleConfig.enable_device_module ? 'success' : 'danger'">
            {{ moduleConfig.enable_device_module ? '已开启' : '已关闭' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="AI智能模块" :span="2">
          <el-tag :type="moduleConfig.enable_ai_module ? 'success' : 'danger'">
            {{ moduleConfig.enable_ai_module ? '已开启' : '已关闭' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 操作说明 -->
    <el-card class="help-card" style="margin-top: 20px;">
      <template #header>
        <div class="header-title">
          <el-icon><QuestionFilled /></el-icon>
          <span>配置说明</span>
        </div>
      </template>
      <el-timeline>
        <el-timeline-item timestamp="第一步" placement="top">
          <el-text>首次使用请点击"初始化配置"按钮，创建默认配置项</el-text>
        </el-timeline-item>
        <el-timeline-item timestamp="第二步" placement="top">
          <el-text>修改平台名称和描述，自定义您的平台品牌信息</el-text>
        </el-timeline-item>
        <el-timeline-item timestamp="第三步" placement="top">
          <el-text>根据实际需求开启或关闭用户注册功能和各功能模块</el-text>
        </el-timeline-item>
        <el-timeline-item timestamp="第四步" placement="top">
          <el-text>点击对应的"保存配置"按钮使配置生效</el-text>
        </el-timeline-item>
        <el-timeline-item timestamp="注意事项" placement="top">
          <el-text type="warning">配置保存后建议刷新页面以完全生效</el-text>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <!-- 用户协议预览对话框 -->
    <el-dialog
      v-model="userAgreementPreviewVisible"
      title="用户协议预览"
      width="70%"
      :close-on-click-modal="false"
    >
      <div class="policy-preview" v-html="policiesConfig.user_agreement"></div>
      <template #footer>
        <el-button type="primary" @click="userAgreementPreviewVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>

    <!-- 隐私政策预览对话框 -->
    <el-dialog
      v-model="privacyPolicyPreviewVisible"
      title="隐私政策预览"
      width="70%"
      :close-on-click-modal="false"
    >
      <div class="policy-preview" v-html="policiesConfig.privacy_policy"></div>
      <template #footer>
        <el-button type="primary" @click="privacyPolicyPreviewVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Setting,
  Check,
  Shop,
  InfoFilled,
  UserFilled,
  Grid,
  Monitor,
  MagicStick,
  Reading,
  View,
  QuestionFilled,
  Document
} from '@element-plus/icons-vue'
import {
  getPlatformConfig,
  updatePlatformConfig,
  getModuleConfig,
  updateModuleConfig,
  initSystemConfig,
  getPoliciesConfig,
  updatePoliciesConfig
} from '../api/systemConfig'

const loading = ref(false)
const saving = ref(false)
const moduleSaving = ref(false)
const policiesSaving = ref(false)
const initializing = ref(false)
const userAgreementPreviewVisible = ref(false)
const privacyPolicyPreviewVisible = ref(false)

// 平台配置
const platformConfig = reactive({
  platform_name: 'CodeHubot',
  platform_description: '智能物联网管理平台',
  enable_user_registration: false
})

// 模块配置
const moduleConfig = reactive({
  enable_device_module: true,
  enable_ai_module: true
})

// 协议配置
const policiesConfig = reactive({
  user_agreement: '',
  privacy_policy: ''
})

// 获取平台配置
const fetchPlatformConfig = async () => {
  loading.value = true
  try {
    const response = await getPlatformConfig()
    Object.assign(platformConfig, response.data)
  } catch (error) {
    console.error('获取平台配置失败:', error)
    ElMessage.error(error.response?.data?.detail || '获取平台配置失败')
  } finally {
    loading.value = false
  }
}

// 获取模块配置
const fetchModuleConfig = async () => {
  loading.value = true
  try {
    const response = await getModuleConfig()
    Object.assign(moduleConfig, response.data)
  } catch (error) {
    console.error('获取模块配置失败:', error)
    ElMessage.error(error.response?.data?.detail || '获取模块配置失败')
  } finally {
    loading.value = false
  }
}

// 获取协议配置
const fetchPoliciesConfig = async () => {
  loading.value = true
  try {
    const response = await getPoliciesConfig()
    Object.assign(policiesConfig, response.data)
  } catch (error) {
    console.error('获取协议配置失败:', error)
    // 失败时不显示错误，因为可能是第一次使用
  } finally {
    loading.value = false
  }
}

// 保存平台配置
const savePlatformConfig = async () => {
  // 验证平台名称
  if (!platformConfig.platform_name || platformConfig.platform_name.trim().length < 2) {
    ElMessage.warning('平台名称至少需要2个字符')
    return
  }

  try {
    await ElMessageBox.confirm(
      '确定要保存平台配置吗？修改后将影响所有用户看到的平台信息。',
      '确认保存',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    saving.value = true
    const response = await updatePlatformConfig(platformConfig)
    Object.assign(platformConfig, response.data)
    ElMessage.success('平台配置保存成功')

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
      console.error('保存平台配置失败:', error)
      ElMessage.error(error.response?.data?.detail || '保存平台配置失败')
    }
  } finally {
    saving.value = false
  }
}

// 保存模块配置
const saveModuleConfig = async () => {
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

    moduleSaving.value = true
    const response = await updateModuleConfig(moduleConfig)
    Object.assign(moduleConfig, response.data)
    ElMessage.success('模块配置保存成功')

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
      console.error('保存模块配置失败:', error)
      ElMessage.error(error.response?.data?.detail || '保存模块配置失败')
    }
  } finally {
    moduleSaving.value = false
  }
}

// 保存协议配置
const savePoliciesConfig = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要保存用户协议和隐私政策吗？',
      '确认保存',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    policiesSaving.value = true
    const response = await updatePoliciesConfig(policiesConfig)
    Object.assign(policiesConfig, response.data)
    ElMessage.success('协议配置保存成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('保存协议配置失败:', error)
      ElMessage.error(error.response?.data?.detail || '保存协议配置失败')
    }
  } finally {
    policiesSaving.value = false
  }
}

// 预览用户协议
const previewUserAgreement = () => {
  userAgreementPreviewVisible.value = true
}

// 预览隐私政策
const previewPrivacyPolicy = () => {
  privacyPolicyPreviewVisible.value = true
}

// 初始化配置
const initConfig = async () => {
  try {
    await ElMessageBox.confirm(
      '此操作将创建默认的系统配置（如果不存在）。已存在的配置不会被覆盖。',
      '确认初始化',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    initializing.value = true
    const response = await initSystemConfig()
    ElMessage.success(response.data.message || '配置初始化成功')

    // 重新获取配置
    await fetchPlatformConfig()
    await fetchModuleConfig()
    await fetchPoliciesConfig()
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
  fetchPlatformConfig()
  fetchModuleConfig()
  fetchPoliciesConfig()
})
</script>

<style scoped>
.platform-config-container {
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
  font-weight: 600;
}

.card-header,
.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-header {
  justify-content: space-between;
}

.header-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.config-form {
  padding: 20px 0;
}

.form-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  color: #909399;
  font-size: 13px;
}

.form-tip .el-icon {
  font-size: 14px;
}

.switch-control {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.switch-description {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 14px;
  padding-left: 4px;
}

.switch-description .el-icon {
  font-size: 16px;
  color: #909399;
}

.config-card,
.status-card,
.help-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

:deep(.el-card__header) {
  border-bottom: 1px solid #ebeef5;
  padding: 18px 20px;
}

:deep(.el-divider) {
  margin: 24px 0;
}

:deep(.el-form-item) {
  margin-bottom: 22px;
}

:deep(.el-switch.is-checked .el-switch__core) {
  background-color: #67c23a;
}

:deep(.el-input-group__prepend) {
  padding: 0 15px;
}

.policy-preview {
  max-height: 60vh;
  overflow-y: auto;
  padding: 20px;
  line-height: 1.8;
  color: #333;
  background: #f9f9f9;
  border-radius: 4px;
}

.policy-preview :deep(h1) {
  font-size: 24px;
  margin: 20px 0 15px;
  color: #2c3e50;
}

.policy-preview :deep(h2) {
  font-size: 20px;
  margin: 18px 0 12px;
  color: #34495e;
}

.policy-preview :deep(h3) {
  font-size: 16px;
  margin: 15px 0 10px;
  color: #34495e;
}

.policy-preview :deep(p) {
  margin: 10px 0;
}

.policy-preview :deep(ul),
.policy-preview :deep(ol) {
  margin: 10px 0;
  padding-left: 40px;
}

.policy-preview :deep(li) {
  margin: 5px 0;
}
</style>
