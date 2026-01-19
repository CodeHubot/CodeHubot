<template>
  <div class="device-register">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">设备注册</h1>
      <p class="page-subtitle">将您的设备注册到系统中，开始享受智能物联网服务</p>
    </div>

    <!-- 说明文档区域 -->
    <el-card class="info-card" shadow="never">
      <template #header>
        <div class="card-header">
          <el-icon class="header-icon"><InfoFilled /></el-icon>
          <span>设备注册说明</span>
        </div>
      </template>
      
      <div class="info-content">
        <div class="info-section">
          <h3>什么是设备注册？</h3>
          <p>设备注册是一种白名单机制，只有注册的设备才能使用系统的各项服务。通过注册，您可以：</p>
          <ul>
            <li>确保设备安全接入系统</li>
            <li>对设备进行统一管理和监控</li>
            <li>享受个性化的设备服务</li>
            <li>获得设备状态实时反馈</li>
          </ul>
        </div>

        <div class="info-section">
          <h3>注册流程</h3>
          <div class="steps">
            <div class="step">
              <div class="step-number">1</div>
              <div class="step-content">
                <h4>获取设备MAC地址</h4>
                <p>设备开机后在LCD显示屏幕上可看到</p>
              </div>
            </div>
            <div class="step">
              <div class="step-number">2</div>
              <div class="step-content">
                <h4>填写注册信息</h4>
                <p>输入设备MAC地址和设备名称</p>
              </div>
            </div>
            <div class="step">
              <div class="step-number">3</div>
              <div class="step-content">
                <h4>设备配网</h4>
                <p>注册成功后按提示进行设备配网</p>
              </div>
            </div>
          </div>
        </div>

        <div class="info-section">
          <h3>设备配网信息</h3>
          <p>设备注册成功后，首次上电配网时需要填写以下配置服务器地址，设备将自动从该服务器获取MQTT等配置信息：</p>
          <div class="config-info-box">
            <div class="config-label">配置服务器地址：</div>
            <div class="config-value-row">
              <el-input
                :model-value="configServerUrl"
                readonly
                size="large"
              >
                <template #prepend>
                  <el-icon><Link /></el-icon>
                </template>
              </el-input>
              <el-button 
                type="primary" 
                size="large"
                @click="copyConfigUrl"
                :icon="CopyDocument"
              >
                复制地址
              </el-button>
            </div>
            <div class="config-tip">
              💡 建议现在就复制保存此地址，以便设备配网时使用
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 注册表单区域 -->
    <el-card class="register-card" shadow="never">
      <template #header>
        <div class="card-header">
          <el-icon class="header-icon"><Plus /></el-icon>
          <span>注册新设备</span>
        </div>
      </template>

      <el-form 
        ref="registerForm" 
        :model="registerData" 
        :rules="rules" 
        label-width="120px"
        class="register-form"
      >
        <!-- 设备名称 -->
        <el-form-item label="设备名称" prop="deviceName">
          <el-input
            v-model="registerData.deviceName"
            placeholder="请输入设备名称，便于识别管理"
            clearable
            maxlength="50"
            show-word-limit
          />
        </el-form-item>

        <!-- 产品选择 -->
        <el-form-item label="产品名称" prop="productId">
          <!-- 共享产品开关（仅普通用户显示） -->
          <div v-if="!isAdmin" style="margin-bottom: 12px; display: flex; align-items: center;">
            <span style="margin-right: 12px; color: #606266; font-size: 14px;">显示范围：</span>
            <el-radio-group v-model="includeSharedProducts" @change="handleSharedProductsChange" size="small">
              <el-radio-button :label="false">仅我的产品</el-radio-button>
              <el-radio-button :label="true">包含共享产品</el-radio-button>
            </el-radio-group>
          </div>
          
          <el-select
            v-model="registerData.productId"
            placeholder="请选择产品"
            filterable
            clearable
            style="width: 100%"
            :loading="productsLoading"
            @focus="loadProducts"
          >
            <el-option
              v-for="product in products"
              :key="product.id"
              :label="`${product.name} (${product.product_code})`"
              :value="product.id"
            >
              <div style="display: flex; align-items: center; width: 100%;">
                <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                  {{ product.name }}
                </span>
                <span style="color: #8492a6; font-size: 12px; margin: 0 8px;">
                  {{ product.product_code }}
                </span>
                <el-tag 
                  v-if="product.is_system" 
                  type="warning" 
                  size="small"
                  style="flex-shrink: 0;"
                >
                  系统内建
                </el-tag>
                <el-tag 
                  v-else-if="product.is_shared" 
                  type="success" 
                  size="small"
                  style="flex-shrink: 0;"
                >
                  共享
                </el-tag>
              </div>
            </el-option>
          </el-select>
          <div class="form-item-tip">
            <el-icon><InfoFilled /></el-icon>
            <div>
              <div>选择产品后，设备将自动绑定该产品的传感器和控制端口配置</div>
              <div style="margin-top: 4px; color: #E6A23C;">
                ⚠️ 重要：选择的产品编码（括号内）必须与设备固件 DEVICE_PRODUCT_ID 完全一致
              </div>
            </div>
          </div>
        </el-form-item>

        <!-- MAC地址输入 -->
        <el-form-item label="MAC地址" prop="macAddress">
          <div class="mac-input-container">
            <div class="mac-input-group">
              <template v-for="(segment, index) in macSegments" :key="index">
                <el-input
                  v-model="macSegments[index]"
                  :ref="el => macInputRefs[index] = el"
                  class="mac-segment"
                  maxlength="2"
                  placeholder="00"
                  @input="handleMacInput(index, $event)"
                  @keydown="handleMacKeydown(index, $event)"
                  @paste="handleMacPaste($event)"
                />
                <span v-if="index < macSegments.length - 1" class="mac-colon">:</span>
              </template>
            </div>
            <div class="mac-display">
              <span class="mac-label">完整MAC地址：</span>
              <span class="mac-value">{{ fullMacAddress || 'XX:XX:XX:XX:XX:XX' }}</span>
            </div>
            <div class="mac-tips">
              <el-icon><InfoFilled /></el-icon>
              <span>您可以直接粘贴完整的MAC地址，系统会自动分割到各个输入框中</span>
            </div>
          </div>
        </el-form-item>

        <!-- 设备描述 -->
        <el-form-item label="设备描述" prop="description">
          <el-input
            v-model="registerData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入设备描述信息（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <!-- 操作按钮 -->
        <el-form-item>
          <el-button 
            type="primary" 
            size="large"
            :loading="loading"
            @click="handleRegister"
          >
            <el-icon><Check /></el-icon>
            注册设备
          </el-button>
          <el-button 
            size="large"
            @click="handleReset"
          >
            <el-icon><RefreshLeft /></el-icon>
            重置表单
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 注册成功提示 -->
    <el-dialog
      v-model="successDialogVisible"
      title="注册成功"
      width="550px"
      :before-close="handleSuccessDialogClose"
    >
      <div class="success-content">
        <el-icon class="success-icon"><SuccessFilled /></el-icon>
        <h3>设备注册成功！</h3>
        <p>设备 <strong>{{ registerData.deviceName }}</strong> 已成功注册到您的账户下</p>
        <p v-if="selectedProductName">产品：<strong>{{ selectedProductName }}</strong></p>
        <p>MAC地址：<code>{{ fullMacAddress }}</code></p>
        
        <!-- 设备配网信息 -->
        <el-divider content-position="left">配网信息</el-divider>
        <el-alert
          title="下一步：设备配网"
          type="info"
          :closable="false"
          show-icon
          style="margin-top: 16px"
        >
          <p style="margin: 8px 0;">在设备首次上电配网时，请填写以下配置服务器地址：</p>
          <div class="config-server-url">
            <el-input
              :model-value="configServerUrl"
              readonly
              style="margin-top: 8px"
            >
              <template #prepend>配置服务器</template>
              <template #append>
                <el-button @click="copyConfigUrl" :icon="CopyDocument">复制</el-button>
              </template>
            </el-input>
          </div>
          <p style="margin: 8px 0 0 0; font-size: 12px; color: var(--el-text-color-secondary);">
            💡 提示：设备将通过此地址自动获取MQTT服务器等配置信息
          </p>
        </el-alert>
        
        <p style="margin-top: 16px;">您现在可以在设备列表中查看和管理该设备。</p>
      </div>
      <template #footer>
        <el-button @click="handleSuccessDialogClose">关闭</el-button>
        <el-button type="primary" @click="goToDeviceList">查看设备列表</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import logger from '../utils/logger'
import { 
  InfoFilled, 
  Plus, 
  Check, 
  RefreshLeft, 
  SuccessFilled,
  CopyDocument,
  Link
} from '@element-plus/icons-vue'
import { preRegisterDevice } from '@/api/device'
import { getProductsSummary } from '@/api/product'
import { useUserStore } from '@/store/user'
import request from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()

// 用户角色判断
const isAdmin = computed(() => userStore.isAdmin)

// 响应式数据
const loading = ref(false)
const productsLoading = ref(false)
const successDialogVisible = ref(false)
const registerForm = ref(null)
const macInputRefs = ref([])
const includeSharedProducts = ref(false)  // 是否包含共享产品（默认不包含）
const configServerUrl = ref('http://config.example.com:8001')  // 配置服务器地址

// MAC地址分段
const macSegments = ref(['', '', '', '', '', ''])

// 产品列表
const products = ref([])

// 表单数据
const registerData = reactive({
  deviceName: '',
  productId: null,
  macAddress: '',
  description: ''
})

// 计算完整MAC地址
const fullMacAddress = computed(() => {
  const segments = macSegments.value.filter(segment => segment.length === 2)
  return segments.length === 6 ? segments.join(':').toUpperCase() : ''
})

// 获取选中的产品名称
const selectedProductName = computed(() => {
  if (!registerData.productId) return null
  const product = products.value.find(p => p.id === registerData.productId)
  return product ? product.name : null
})

// 监听MAC地址变化，更新表单数据
const updateMacAddress = () => {
  registerData.macAddress = fullMacAddress.value
}

// MAC地址验证规则
const validateMacAddress = (rule, value, callback) => {
  if (!value) {
    callback(new Error('请输入设备MAC地址'))
    return
  }
  
  const macRegex = /^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/
  if (!macRegex.test(value)) {
    callback(new Error('MAC地址格式不正确，请输入有效的MAC地址'))
    return
  }
  
  callback()
}

// 表单验证规则
const rules = {
  deviceName: [
    { required: true, message: '请输入设备名称', trigger: 'blur' },
    { min: 2, max: 50, message: '设备名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  productId: [
    { required: true, message: '请选择产品', trigger: 'change' }
  ],
  macAddress: [
    { required: true, validator: validateMacAddress, trigger: 'change' }
  ]
}

// 加载产品列表
const loadProducts = async (forceReload = false) => {
  if (products.value.length > 0 && !forceReload) {
    // 如果已经加载过，不再重复加载（除非强制刷新）
    return
  }
  
  productsLoading.value = true
  try {
    const params = {
      is_active: true,
      include_shared: isAdmin.value ? true : includeSharedProducts.value  // 管理员看全部，普通用户根据开关决定
    }
    const response = await getProductsSummary(params)
    products.value = response.data || response
    if (products.value.length === 0) {
      ElMessage.warning('暂无可用产品，请先创建产品')
    }
  } catch (error) {
    logger.error('加载产品列表失败:', error)
    ElMessage.error('加载产品列表失败，请稍后重试')
  } finally {
    productsLoading.value = false
  }
}

// 处理共享产品开关变化
const handleSharedProductsChange = () => {
  // 清空当前选择的产品
  registerData.productId = null
  // 重新加载产品列表
  loadProducts(true)
}

// 组件挂载时加载产品列表
// onMounted(() => {
//   loadProducts()
// })

// MAC地址输入处理
const handleMacInput = (index, value) => {
  // 只允许输入十六进制字符
  const hexValue = value.replace(/[^0-9A-Fa-f]/g, '').toUpperCase()
  macSegments.value[index] = hexValue.slice(0, 2)
  
  // 自动跳转到下一个输入框
  if (hexValue.length === 2 && index < 5) {
    nextTick(() => {
      const nextInput = macInputRefs.value[index + 1]
      if (nextInput && nextInput.focus) {
        nextInput.focus()
      }
    })
  }
  
  updateMacAddress()
}

// MAC地址键盘事件处理
const handleMacKeydown = (index, event) => {
  // 退格键处理
  if (event.key === 'Backspace' && !macSegments.value[index] && index > 0) {
    event.preventDefault()
    const prevInput = macInputRefs.value[index - 1]
    if (prevInput && prevInput.focus) {
      prevInput.focus()
      // 清空前一个输入框的内容
      macSegments.value[index - 1] = ''
      updateMacAddress()
    }
  }
  
  // 左右箭头键处理
  if (event.key === 'ArrowLeft' && index > 0) {
    event.preventDefault()
    const prevInput = macInputRefs.value[index - 1]
    if (prevInput && prevInput.focus) {
      prevInput.focus()
    }
  }
  
  if (event.key === 'ArrowRight' && index < 5) {
    event.preventDefault()
    const nextInput = macInputRefs.value[index + 1]
    if (nextInput && nextInput.focus) {
      nextInput.focus()
    }
  }
}

// MAC地址粘贴处理
const handleMacPaste = (event) => {
  event.preventDefault()
  const pastedText = event.clipboardData.getData('text')
  
  // 尝试解析粘贴的MAC地址
  let cleanText = pastedText.replace(/[^0-9A-Fa-f]/g, '')
  
  // 如果包含分隔符，先尝试按分隔符分割
  if (pastedText.includes(':') || pastedText.includes('-')) {
    const segments = pastedText.split(/[:-]/).filter(seg => seg.length > 0)
    if (segments.length === 6 && segments.every(seg => /^[0-9A-Fa-f]{1,2}$/i.test(seg))) {
      for (let i = 0; i < 6; i++) {
        macSegments.value[i] = segments[i].padStart(2, '0').toUpperCase()
      }
      updateMacAddress()
      
      // 聚焦到最后一个输入框
      nextTick(() => {
        const lastInput = macInputRefs.value[5]
        if (lastInput && lastInput.focus) {
          lastInput.focus()
        }
      })
      ElMessage.success('MAC地址已自动填入')
      return
    }
  }
  
  // 如果是连续的12位十六进制字符
  if (cleanText.length === 12) {
    for (let i = 0; i < 6; i++) {
      macSegments.value[i] = cleanText.substr(i * 2, 2).toUpperCase()
    }
    updateMacAddress()
    
    // 聚焦到最后一个输入框
    nextTick(() => {
      const lastInput = macInputRefs.value[5]
      if (lastInput && lastInput.focus) {
        lastInput.focus()
      }
    })
    ElMessage.success('MAC地址已自动填入')
  } else {
    ElMessage.warning('粘贴的内容不是有效的MAC地址格式')
  }
}

// 注册设备
const handleRegister = async () => {
  try {
    // 验证表单
    const valid = await registerForm.value.validate()
    if (!valid) return
    
    loading.value = true
    
    // 调用预注册API
    const requestData = {
      name: registerData.deviceName,
      device_type: 'ESP32',
      mac_address: registerData.macAddress,
      description: registerData.description || null,
      product_id: registerData.productId  // 添加产品ID
    }
    
    const response = await preRegisterDevice(requestData)
    
    // 显示成功对话框
    successDialogVisible.value = true
    
    ElMessage.success('设备注册成功！')
  } catch (error) {
    logger.error('设备注册失败:', error)
    
    // 处理不同类型的错误
    if (error.response && error.response.data && error.response.data.detail) {
      ElMessage.error(error.response.data.detail)
    } else if (error.message) {
      ElMessage.error(error.message)
    } else {
      ElMessage.error('设备注册失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

// 重置表单
const handleReset = () => {
  ElMessageBox.confirm('确定要重置表单吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    registerForm.value.resetFields()
    registerData.productId = null
    macSegments.value = ['', '', '', '', '', '']
    updateMacAddress()
    ElMessage.success('表单已重置')
  }).catch(() => {
    // 用户取消
  })
}

// 成功对话框关闭处理
const handleSuccessDialogClose = () => {
  successDialogVisible.value = false
  handleReset()
}

// 跳转到设备列表
const goToDeviceList = () => {
  successDialogVisible.value = false
  router.push('/device/devices')
}

// 复制配置服务器地址
const copyConfigUrl = async () => {
  try {
    await navigator.clipboard.writeText(configServerUrl.value)
    ElMessage.success('配置服务器地址已复制到剪贴板')
  } catch (error) {
    logger.error('复制失败:', error)
    ElMessage.error('复制失败，请手动复制')
  }
}

// 加载配置服务器地址
const loadConfigServerUrl = async () => {
  try {
    const response = await request.get('/system-config/configs/public', {
      params: { exclude_policies: true }
    })
    const configs = response.data || []
    const configItem = configs.find(c => c.config_key === 'device_config_server_url')
    if (configItem && configItem.config_value) {
      configServerUrl.value = configItem.config_value
    }
  } catch (error) {
    logger.error('加载配置服务器地址失败:', error)
    // 使用默认值，不显示错误消息
  }
}

// 组件挂载时加载产品列表和配置服务器地址
onMounted(() => {
  loadProducts()
  loadConfigServerUrl()
})
</script>

<style scoped>
.device-register {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 10px 0;
}

.page-subtitle {
  font-size: 16px;
  color: #606266;
  margin: 0;
}

.info-card, .register-card {
  margin-bottom: 30px;
}

.card-header {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-icon {
  margin-right: 8px;
  font-size: 18px;
  color: #409eff;
}

.info-content {
  line-height: 1.6;
}

.info-section {
  margin-bottom: 25px;
}

.info-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 10px 0;
}

.info-section p {
  color: #606266;
  margin: 0 0 10px 0;
}

.info-section ul {
  color: #606266;
  margin: 10px 0;
  padding-left: 20px;
}

.info-section li {
  margin-bottom: 5px;
}

.steps {
  display: flex;
  gap: 30px;
  margin-top: 20px;
}

.step {
  display: flex;
  align-items: flex-start;
  flex: 1;
}

.step-number {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  margin-right: 15px;
  flex-shrink: 0;
}

.step-content h4 {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 5px 0;
}

.step-content p {
  font-size: 13px;
  color: #606266;
  margin: 0;
}

.config-info-box {
  background: #f0f9ff;
  border: 1px solid #409eff;
  border-radius: 8px;
  padding: 16px;
  margin-top: 12px;
}

.config-label {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.config-value-row {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
}

.config-value-row .el-input {
  flex: 1;
}

.config-tip {
  font-size: 13px;
  color: #67c23a;
  margin: 0;
  font-weight: 500;
}

.register-form {
  max-width: 600px;
}

.mac-input-container {
  width: 100%;
}

.mac-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.mac-segment {
  width: 50px;
}

.mac-segment :deep(.el-input__inner) {
  text-align: center;
  font-family: 'Courier New', monospace;
  font-weight: 600;
  text-transform: uppercase;
}

.mac-segment:not(:last-child)::after {
  content: ':';
  color: #909399;
  font-weight: 600;
  font-size: 16px;
  margin-left: 8px;
  position: absolute;
  right: -12px;
  top: 50%;
  transform: translateY(-50%);
}

.mac-segment {
  position: relative;
}

.mac-display {
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  margin-bottom: 8px;
}

.mac-label {
  color: #606266;
  font-size: 14px;
}

.mac-value {
  color: #303133;
  font-family: 'Courier New', monospace;
  font-weight: 600;
  font-size: 14px;
}

.mac-tips {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #909399;
  font-size: 12px;
}

.mac-tips .el-icon {
  font-size: 14px;
}

.form-item-tip {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 5px;
  font-size: 12px;
  color: #909399;
}

.form-item-tip .el-icon {
  color: #909399;
  font-size: 14px;
}

.success-content {
  text-align: center;
  padding: 20px;
}

.success-icon {
  font-size: 48px;
  color: #67c23a;
  margin-bottom: 15px;
}

.success-content h3 {
  color: #303133;
  margin: 0 0 15px 0;
}

.success-content p {
  color: #606266;
  margin: 10px 0;
  line-height: 1.5;
}

.success-content code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  color: #e6a23c;
}

/* MAC输入布局 */
.mac-input-group {
  display: flex;
  align-items: center;
  gap: 6px;
  max-width: 450px;
}

.mac-input-group .mac-segment {
  width: 55px;
  flex-shrink: 0;
}

/* 冒号分隔符 */
.mac-colon {
  color: #409eff;
  font-weight: 600;
  font-size: 18px;
  line-height: 1;
  user-select: none;
  margin: 0 2px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .device-register {
    padding: 15px;
  }
  
  .steps {
    flex-direction: column;
    gap: 20px;
  }
  
  .mac-input-group {
    gap: 6px;
    max-width: 100%;
  }
  
  .mac-input-group .mac-segment {
    width: 50px;
  }
  
  .mac-colon {
    font-size: 16px;
    margin: 0 1px;
  }
}
</style>