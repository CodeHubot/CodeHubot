<template>
  <div class="login-container">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="floating-shape shape-1"></div>
      <div class="floating-shape shape-2"></div>
      <div class="floating-shape shape-3"></div>
    </div>
    
    <!-- 主要内容 -->
    <div class="login-content">
      <!-- 左侧品牌区域 -->
      <div class="brand-section">
        <div class="brand-content">
          <div class="logo">
            <el-icon size="48" color="#FFFFFF">
              <Monitor />
            </el-icon>
          </div>
          <h1 class="brand-title">CODEHUBOT</h1>
          <p class="brand-subtitle">CodeHubot智能体开发</p>
          <div class="feature-list">

            <div class="feature-item">
              <el-icon color="#67C23A"><CircleCheck /></el-icon>
              <span>AI智能设备管理</span>
            </div>
            <div class="feature-item">
              <el-icon color="#67C23A"><CircleCheck /></el-icon>
              <span>MQTT 实时通信</span>
            </div>
            <div class="feature-item">
              <el-icon color="#67C23A"><CircleCheck /></el-icon>
              <span>智能体构建</span>
            </div>

          </div>
        </div>
      </div>
      
      <!-- 右侧登录表单 -->
      <div class="form-section">
        <div class="form-container">
          <div class="form-header">
            <h2>欢迎回来</h2>
          </div>

          <!-- 登录表单 -->
          <el-form
            ref="generalFormRef"
            :model="generalForm"
            :rules="generalRules"
            class="login-form"
            autocomplete="off"
            @submit.prevent="handleGeneralLogin"
          >
            <el-form-item prop="username">
              <el-input
                v-model="generalForm.username"
                placeholder="请输入用户名"
                size="large"
                prefix-icon="User"
                class="form-input"
                autocomplete="off"
              />
            </el-form-item>
            
            <el-form-item prop="password">
              <el-input
                v-model="generalForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                prefix-icon="Lock"
                show-password
                class="form-input"
                autocomplete="off"
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
                  class="captcha-input form-input"
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
            
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="login-btn"
                :loading="loading"
                @click="handleGeneralLogin"
              >
                <span v-if="!loading">登录</span>
                <span v-else>登录中...</span>
              </el-button>
            </el-form-item>
          </el-form>
          
          <div class="form-footer" v-if="canRegister">
            <p>还没有账户？ <el-link type="primary" @click="$router.push('/register')">立即注册</el-link></p>
          </div>
          
          <!-- 用户协议和隐私政策 -->
          <div class="form-policies">
            <span class="policy-text">登录即表示您已阅读并同意</span>
            <el-link type="info" :underline="false" @click="showUserAgreement">
              《用户协议》
            </el-link>
            <span class="policy-divider">和</span>
            <el-link type="info" :underline="false" @click="showPrivacyPolicy">
              《隐私政策》
            </el-link>
          </div>
        </div>
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
import { Refresh, Monitor, CircleCheck } from '@element-plus/icons-vue'
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
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.floating-shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 6s ease-in-out infinite;
}

.shape-1 {
  width: 200px;
  height: 200px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 150px;
  height: 150px;
  top: 60%;
  right: 15%;
  animation-delay: 2s;
}

.shape-3 {
  width: 100px;
  height: 100px;
  bottom: 20%;
  left: 20%;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(180deg); }
}

/* 主要内容布局 */
.login-content {
  display: flex;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

/* 左侧品牌区域 */
.brand-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
}

.brand-content {
  text-align: center;
  color: white;
  max-width: 400px;
}

.logo {
  margin-bottom: 30px;
  
  .el-icon {
    filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));
  }
}

.brand-title {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 16px;
  color: white;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.brand-subtitle {
  font-size: 1.2rem;
  margin-bottom: 40px;
  opacity: 0.95;
  font-weight: 300;
}

.feature-list {
  text-align: left;
}

.feature-item {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  font-size: 1rem;
  opacity: 0.9;
  
  .el-icon {
    margin-right: 12px;
    font-size: 1.3rem;
  }
}

/* 右侧表单区域 */
.form-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  background: #f5f5f5;
}

.form-container {
  width: 100%;
  max-width: 420px;
  background: white;
  border-radius: 24px;
  padding: 48px 40px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
}

.form-header {
  text-align: center;
  margin-bottom: 32px;
  
  h2 {
    font-size: 2rem;
    font-weight: 600;
    color: #1a1a1a;
    margin-bottom: 8px;
  }
  
  p {
    color: #666;
    font-size: 1rem;
  }
}

.login-form {
  margin-bottom: 20px;
}

.form-input {
  height: 50px;
  
  :deep(.el-input__wrapper) {
    border-radius: 12px;
    background-color: #f8f9fa;
    border: 1px solid #e8e8e8;
    box-shadow: none;
    transition: all 0.3s ease;
    padding: 0 16px;
    
    &:hover {
      border-color: #409eff;
      background-color: white;
    }
    
    &.is-focus {
      border-color: #409eff;
      background-color: white;
      box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
    }
  }
  
  :deep(.el-input__inner) {
    height: 48px;
    line-height: 48px;
  }
  
  :deep(.el-input__prefix) {
    display: flex;
    align-items: center;
  }
}

.login-btn {
  width: 100%;
  height: 50px;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #409eff 0%, #667eea 100%);
  border: none;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(64, 158, 255, 0.35);
  }
  
  &:active {
    transform: translateY(0);
  }
}

.form-footer {
  text-align: center;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
  
  p {
    color: #666;
    font-size: 0.9rem;
    margin: 0;
  }
}

.form-policies {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
  font-size: 13px;
  color: #999;
  
  .policy-text {
    margin-right: 5px;
  }
  
  .policy-divider {
    margin: 0 5px;
  }
  
  .el-link {
    font-size: 13px;
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
  height: 50px;
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e8e8e8;
  background: #f8f9fa;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: #409eff;
    box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
  }
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
  background: rgba(255, 255, 255, 0.95);
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
  
  :deep(ul),
  :deep(ol) {
    margin: 10px 0;
    padding-left: 40px;
  }
  
  :deep(li) {
    margin: 5px 0;
  }
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .login-content {
    flex-direction: column;
  }
  
  .brand-section {
    padding: 40px 20px;
    min-height: 40vh;
  }
  
  .form-section {
    padding: 40px 20px;
    min-height: 60vh;
  }
  
  .brand-title {
    font-size: 2.5rem;
  }
  
  .form-header h2 {
    font-size: 1.75rem;
  }
}

@media (max-width: 768px) {
  .brand-section,
  .form-section {
    padding: 30px 20px;
  }
  
  .brand-title {
    font-size: 2rem;
  }
  
  .form-container {
    padding: 36px 28px;
  }
  
  .form-header h2 {
    font-size: 1.5rem;
  }
}

@media (max-width: 480px) {
  .brand-section,
  .form-section {
    padding: 20px;
  }
  
  .brand-title {
    font-size: 1.8rem;
  }
  
  .form-container {
    max-width: 100%;
    padding: 28px 20px;
    border-radius: 16px;
  }
}

.login-bg {
  display: none;
}
</style>
