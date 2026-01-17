<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>{{ platformName }}</h1>
        <p>{{ platformDescription }}</p>
      </div>
      
      <el-form
        ref="generalFormRef"
        :model="generalForm"
        :rules="generalRules"
        @submit.prevent="handleGeneralLogin"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="generalForm.username"
            placeholder="用户名/邮箱"
            prefix-icon="User"
            size="large"
            clearable
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="generalForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleGeneralLogin"
            @blur="checkLoginAttempts"
          />
        </el-form-item>
        
        <!-- 验证码输入框（登录失败3次后显示） -->
        <el-form-item v-if="needsCaptcha" prop="captchaCode">
          <div class="captcha-container">
            <el-input
              v-model="generalForm.captchaCode"
              placeholder="请输入验证码"
              size="large"
              prefix-icon="Key"
              class="captcha-input"
              autocomplete="off"
              maxlength="4"
              @keyup.enter="handleGeneralLogin"
            />
            <div class="captcha-image-wrapper" @click="refreshCaptcha">
              <img 
                v-if="captchaUrl" 
                :src="captchaUrl" 
                alt="验证码"
                class="captcha-image"
              />
              <el-icon class="refresh-icon" title="点击刷新验证码">
                <Refresh />
              </el-icon>
            </div>
          </div>
        </el-form-item>
        
        <!-- 用户协议勾选 -->
        <el-form-item prop="agreePolicy">
          <el-checkbox v-model="generalForm.agreePolicy">
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
            size="large"
            style="width: 100%"
            :loading="loading"
            :disabled="!generalForm.agreePolicy"
            @click="handleGeneralLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer" v-if="canRegister">
        <el-link type="primary" :underline="false" @click="$router.push('/register')">
          没有账号？注册
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
    
    <div class="login-bg">
      <div class="bg-shape shape-1"></div>
      <div class="bg-shape shape-2"></div>
      <div class="bg-shape shape-3"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlatformStore } from '@/stores/platform'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { login } from '@shared/api/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const platformStore = usePlatformStore()

// 表单引用
const generalFormRef = ref()
const loading = ref(false)

// 平台配置
const platformName = computed(() => platformStore.platformName)
const platformDescription = computed(() => platformStore.platformDescription)
const canRegister = computed(() => platformStore.enableUserRegistration)

// 用户协议和隐私政策
const userAgreementVisible = ref(false)
const privacyPolicyVisible = ref(false)
const userAgreementContent = computed(() => platformStore.userAgreement || '<p style="color: #999;">暂无用户协议内容</p>')
const privacyPolicyContent = computed(() => platformStore.privacyPolicy || '<p style="color: #999;">暂无隐私政策内容</p>')

function showUserAgreement() {
  userAgreementVisible.value = true
}

function showPrivacyPolicy() {
  privacyPolicyVisible.value = true
}

// 通用登录表单
const generalForm = reactive({
  username: '',
  password: '',
  agreePolicy: false,
  captchaCode: ''
})

// 登录失败次数和验证码相关
const loginAttempts = ref(0)
const needsCaptcha = ref(false)
const captchaUrl = ref('')

const generalRules = {
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
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
  ],
  captchaCode: [
    { 
      validator: (rule, value, callback) => {
        if (needsCaptcha.value && !value) {
          callback(new Error('请输入验证码'))
        } else {
          callback()
        }
      }, 
      trigger: 'blur' 
    }
  ]
}

// 检查是否需要验证码
async function checkLoginAttempts() {
  if (!generalForm.username) return
  
  try {
    const response = await fetch(`/api/auth/login-attempts/${encodeURIComponent(generalForm.username)}`)
    const result = await response.json()
    
    if (result.code === 200) {
      loginAttempts.value = result.data.attempts
      needsCaptcha.value = result.data.needs_captcha
      
      if (needsCaptcha.value) {
        refreshCaptcha()
      }
    }
  } catch (error) {
    console.error('检查登录失败次数出错:', error)
  }
}

// 刷新验证码
function refreshCaptcha() {
  if (!generalForm.username) return
  captchaUrl.value = `/api/auth/captcha?identifier=${encodeURIComponent(generalForm.username)}&t=${Date.now()}`
}

// 通用登录
async function handleGeneralLogin() {
  if (!generalFormRef.value) return
  
  await generalFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      const loginData = {
        email: generalForm.username.trim(),  // 去除前后空格
        password: generalForm.password.trim(),  // 去除前后空格
        captcha_code: generalForm.captchaCode
      }
      
      await authStore.login(login, loginData)
      
      ElMessage.success('登录成功')
      
      // 根据角色跳转到对应页面
      let targetPath = '/device/dashboard'
      if (route.query.redirect) {
        targetPath = route.query.redirect
      }
      router.push(targetPath)
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || '登录失败'
      
      // 检查是否需要显示验证码
      if (errorMsg.includes('验证码')) {
        await checkLoginAttempts()
      }
      
      ElMessage.error(errorMsg)
      
      // 如果显示了验证码，刷新验证码
      if (needsCaptcha.value) {
        refreshCaptcha()
        generalForm.captchaCode = ''
      }
    } finally {
      loading.value = false
    }
  })
}

// 页面加载时获取平台配置和用户协议
onMounted(async () => {
  await platformStore.loadConfig()
  // 登录页面需要显示用户协议和隐私政策，所以这里加载
  await platformStore.loadPolicies()
})
</script>

<style scoped lang="scss">
.login-container {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
}

.login-card {
  position: relative;
  z-index: 10;
  background: white;
  border-radius: 20px;
  padding: 50px 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 450px;
  max-width: 90vw;
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
  
  h1 {
    font-size: 36px;
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 10px;
  }
  
  p {
    font-size: 16px;
    color: #999;
  }
}

.login-form {
  margin-top: 30px;
  
  .el-form-item {
    margin-bottom: 24px;
  }
}

.login-footer {
  text-align: center;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
  
  .el-divider {
    margin: 0 15px;
  }
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
  
  :deep(h1) {
    font-size: 24px;
    margin: 20px 0 15px;
    color: #2c3e50;
  }
  
  :deep(h2) {
    font-size: 20px;
    margin: 18px 0 12px;
    color: #34495e;
  }
  
  :deep(h3) {
    font-size: 16px;
    margin: 15px 0 10px;
    color: #34495e;
  }
  
  :deep(p) {
    margin: 10px 0;
    text-indent: 2em;
  }
  
  :deep(ul), :deep(ol) {
    margin: 10px 0;
    padding-left: 40px;
  }
  
  :deep(li) {
    margin: 5px 0;
  }
}

/* 验证码容器样式 */
.captcha-container {
  display: flex;
  gap: 12px;
  align-items: center;
}

.captcha-input {
  flex: 1;
}

.captcha-image-wrapper {
  position: relative;
  width: 120px;
  height: 40px;
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #dcdfe6;
  transition: all 0.3s ease;
}

.captcha-image-wrapper:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.captcha-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.captcha-image-wrapper .refresh-icon {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  padding: 4px;
  font-size: 14px;
  color: #409eff;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.captcha-image-wrapper:hover .refresh-icon {
  opacity: 1;
}

.login-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  overflow: hidden;
}

.bg-shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  animation: float 20s infinite ease-in-out;
}

.shape-1 {
  width: 300px;
  height: 300px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 200px;
  height: 200px;
  bottom: 20%;
  right: 15%;
  animation-delay: 3s;
}

.shape-3 {
  width: 150px;
  height: 150px;
  top: 50%;
  right: 25%;
  animation-delay: 6s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  25% {
    transform: translateY(-30px) rotate(90deg);
  }
  50% {
    transform: translateY(0) rotate(180deg);
  }
  75% {
    transform: translateY(30px) rotate(270deg);
  }
}

@media (max-width: 768px) {
  .login-card {
    padding: 40px 30px;
  }
  
  .login-header h1 {
    font-size: 28px;
  }
}
</style>
