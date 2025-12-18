<template>
  <div class="register-container">
    <!-- 注册功能已关闭提示 -->
    <div v-if="registrationClosed" class="registration-closed">
      <el-result
        icon="warning"
        title="用户注册功能已关闭"
        sub-title="当前系统不开放用户注册，请联系管理员为您创建账号"
      >
        <template #extra>
          <el-button type="primary" @click="$router.push('/login')">
            返回登录
          </el-button>
        </template>
      </el-result>
    </div>

    <!-- 注册表单 -->
    <div v-else class="register-box">
      <div class="register-header">
        <h2>注册账户</h2>
        <p>创建您的 {{ platformName }} 账户</p>
      </div>
      
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        class="register-form"
        autocomplete="off"
        @submit.prevent="handleRegister"
      >
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="请输入用户名（3-20位字母数字）"
            prefix-icon="User"
            maxlength="20"
            autocomplete="off"
          />
        </el-form-item>

        <el-form-item prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="请输入邮箱（可选）"
            prefix-icon="Message"
            autocomplete="off"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="密码（至少8位，包含字母和数字）"
            prefix-icon="Lock"
            show-password
            autocomplete="new-password"
          />
        </el-form-item>
        
        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码确认"
            prefix-icon="Lock"
            show-password
            autocomplete="new-password"
          />
        </el-form-item>
        
        <!-- 用户协议勾选 -->
        <el-form-item prop="agreePolicy">
          <el-checkbox v-model="registerForm.agreePolicy">
            <span class="agreement-text">
              我已阅读并同意
              <el-link type="primary" :underline="false" @click.stop="showUserAgreement">
                《用户协议》
              </el-link>
              和
              <el-link type="primary" :underline="false" @click.stop="showPrivacyPolicy">
                《隐私政策》
              </el-link>
            </span>
          </el-checkbox>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            class="register-btn"
            :loading="loading"
            :disabled="!registerForm.agreePolicy"
            @click="handleRegister"
          >
            注册
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="register-footer">
        <el-link type="primary" @click="$router.push('/login')">
          已有账户？立即登录
        </el-link>
      </div>
    </div>
    
    <!-- 用户协议对话框 -->
    <el-dialog
      v-model="userAgreementVisible"
      title="用户协议"
      width="70%"
      :close-on-click-modal="false"
    >
      <div class="policy-content" v-html="userAgreementContent"></div>
      <template #footer>
        <el-button type="primary" @click="userAgreementVisible = false">
          我已阅读
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 隐私政策对话框 -->
    <el-dialog
      v-model="privacyPolicyVisible"
      title="个人信息及隐私保护政策"
      width="70%"
      :close-on-click-modal="false"
    >
      <div class="policy-content" v-html="privacyPolicyContent"></div>
      <template #footer>
        <el-button type="primary" @click="privacyPolicyVisible = false">
          我已阅读
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { usePlatformStore } from '@/stores/platform'
import request from '@/utils/request'

const router = useRouter()
const platformStore = usePlatformStore()

const registerFormRef = ref()
const loading = ref(false)
const registrationClosed = ref(false)
const userAgreementVisible = ref(false)
const privacyPolicyVisible = ref(false)

// 平台配置
const platformName = computed(() => platformStore.platformName)
const userAgreementContent = computed(() => platformStore.userAgreement || '<p style="color: #999;">暂无用户协议内容</p>')
const privacyPolicyContent = computed(() => platformStore.privacyPolicy || '<p style="color: #999;">暂无隐私政策内容</p>')

// 显示用户协议
const showUserAgreement = () => {
  userAgreementVisible.value = true
}

// 显示隐私政策
const showPrivacyPolicy = () => {
  privacyPolicyVisible.value = true
}

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  agreePolicy: false
})

const validateEmail = (rule, value, callback) => {
  if (!value) {
    callback() // 邮箱可选
    return
  }
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailPattern.test(value)) {
    callback(new Error('请输入有效的邮箱地址'))
  } else {
    callback()
  }
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度必须在3-20位之间', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '用户名只能包含字母、数字、下划线和连字符', trigger: 'blur' }
  ],
  email: [
    { validator: validateEmail, trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' },
    { 
      pattern: /^(?=.*[a-zA-Z])(?=.*\d)[a-zA-Z\d@$!%*?&_-]{8,}$/, 
      message: '密码必须包含字母和数字', 
      trigger: 'blur' 
    }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  agreePolicy: [
    {
      validator: (rule, value, callback) => {
        if (!value) {
          callback(new Error('请阅读并同意用户协议和隐私政策'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

// 检查注册功能是否开启
const checkRegistrationStatus = async () => {
  try {
    // 加载平台配置
    await platformStore.loadConfig()
    
    // 检查是否开启注册
    if (!platformStore.enableUserRegistration) {
      registrationClosed.value = true
    }
  } catch (error) {
    console.error('加载配置失败:', error)
    // 加载失败时默认允许注册
    registrationClosed.value = false
  }
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const response = await request({
        url: '/auth/register',
        method: 'post',
        data: {
          username: registerForm.username,
          email: registerForm.email || null,
          password: registerForm.password
        }
      })

      ElMessage.success('注册成功！请登录')
      
      // 跳转到登录页
      setTimeout(() => {
        router.push('/login')
      }, 1500)
    } catch (error) {
      console.error('注册失败:', error)
      const errorMsg = error.response?.data?.detail || error.message || '注册失败，请稍后重试'
      ElMessage.error(errorMsg)
    } finally {
      loading.value = false
    }
  })
}

onMounted(() => {
  checkRegistrationStatus()
})
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.registration-closed {
  width: 100%;
  max-width: 600px;
  padding: 40px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.register-box {
  width: 100%;
  max-width: 420px;
  padding: 40px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
}

.register-header h2 {
  color: #333;
  margin: 0 0 10px 0;
  font-size: 24px;
  font-weight: 600;
}

.register-header p {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.register-form {
  margin-bottom: 20px;
}

.register-btn {
  width: 100%;
  height: 45px;
  font-size: 16px;
  font-weight: 500;
}

.register-footer {
  text-align: center;
}

.agreement-text {
  font-size: 14px;
  color: #606266;
  
  .el-link {
    font-size: 14px;
    margin: 0 2px;
  }
}

.policy-content {
  max-height: 60vh;
  overflow-y: auto;
  padding: 20px;
  line-height: 1.8;
  color: #333;
  background: #f9f9f9;
  border-radius: 4px;
}

.policy-content :deep(h1) {
  font-size: 24px;
  margin: 20px 0 15px;
  color: #2c3e50;
}

.policy-content :deep(h2) {
  font-size: 20px;
  margin: 18px 0 12px;
  color: #34495e;
}

.policy-content :deep(h3) {
  font-size: 16px;
  margin: 15px 0 10px;
  color: #34495e;
}

.policy-content :deep(p) {
  margin: 10px 0;
}

.policy-content :deep(ul),
.policy-content :deep(ol) {
  margin: 10px 0;
  padding-left: 40px;
}

.policy-content :deep(li) {
  margin: 5px 0;
}

:deep(.el-result) {
  padding: 20px 0;
}

:deep(.el-result__icon svg) {
  width: 80px;
  height: 80px;
}

:deep(.el-result__title) {
  font-size: 20px;
  margin-top: 20px;
}

:deep(.el-result__subtitle) {
  margin-top: 10px;
}
</style>
