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
            <el-icon size="48" color="#409EFF">
              <Monitor />
            </el-icon>
          </div>
          <h1 class="brand-title">AIOT Admin</h1>
          <p class="brand-subtitle">智能物联网设备管理平台</p>
          <div class="feature-list">
            <div class="feature-item">
              <el-icon color="#67C23A"><CircleCheck /></el-icon>
              <span>设备实时监控</span>
            </div>
            <div class="feature-item">
              <el-icon color="#67C23A"><CircleCheck /></el-icon>
              <span>智能数据分析</span>
            </div>
            <div class="feature-item">
              <el-icon color="#67C23A"><CircleCheck /></el-icon>
              <span>云端管理</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧登录表单 -->
      <div class="form-section">
        <div class="form-container">
          <div class="form-header">
            <h2>欢迎回来</h2>
            <p>请登录您的账户</p>
          </div>

          <!-- 登录方式切换 -->
          <div class="login-type-switch">
            <el-radio-group v-model="loginType" @change="handleLoginTypeChange">
              <el-radio-button label="normal">普通登录</el-radio-button>
              <el-radio-button label="institution">机构登录</el-radio-button>
            </el-radio-group>
          </div>
          
          <!-- 普通登录表单 -->
          <el-form
            v-if="loginType === 'normal'"
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            class="login-form"
            autocomplete="off"
            @submit.prevent="handleLogin"
          >
            <el-form-item prop="email">
              <el-input
                v-model="loginForm.email"
                placeholder="请输入用户名"
                size="large"
                prefix-icon="User"
                class="form-input"
                autocomplete="off"
              />
            </el-form-item>
            
            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                prefix-icon="Lock"
                show-password
                class="form-input"
                autocomplete="off"
                @keyup.enter="handleLogin"
              />
            </el-form-item>
            
            <el-form-item>
              <div class="form-options">
                <el-checkbox v-model="rememberMe">记住我</el-checkbox>
                <el-link type="primary" @click="$router.push('/forgot-password')">
                  忘记密码？
                </el-link>
              </div>
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="login-btn"
                :loading="loading"
                @click="handleLogin"
              >
                <span v-if="!loading">登录</span>
                <span v-else>登录中...</span>
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 机构登录表单 -->
          <el-form
            v-else
            ref="institutionFormRef"
            :model="institutionForm"
            :rules="institutionRules"
            class="login-form"
            autocomplete="off"
            @submit.prevent="handleInstitutionLogin"
          >
            <el-form-item prop="school_code">
              <el-input
                v-model="institutionForm.school_code"
                placeholder="学校代码（如：BJ-YCZX）"
                size="large"
                prefix-icon="School"
                class="form-input"
                autocomplete="off"
              />
            </el-form-item>

            <el-form-item prop="number">
              <el-input
                v-model="institutionForm.number"
                placeholder="工号/学号"
                size="large"
                prefix-icon="Tickets"
                class="form-input"
                autocomplete="off"
              />
            </el-form-item>
            
            <el-form-item prop="password">
              <el-input
                v-model="institutionForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                prefix-icon="Lock"
                show-password
                class="form-input"
                autocomplete="off"
                @keyup.enter="handleInstitutionLogin"
              />
            </el-form-item>
            
            <el-form-item>
              <div class="form-options">
                <el-checkbox v-model="rememberMe">记住我</el-checkbox>
                <span style="color: #999; font-size: 12px;">使用学校代码+工号/学号登录</span>
              </div>
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="login-btn"
                :loading="loading"
                @click="handleInstitutionLogin"
              >
                <span v-if="!loading">登录</span>
                <span v-else>登录中...</span>
              </el-button>
            </el-form-item>
          </el-form>
          
          <div class="form-footer">
            <p>还没有账户？ <el-link type="primary" @click="$router.push('/register')">立即注册</el-link></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import { ElMessage } from 'element-plus'
import logger from '../utils/logger'
import { institutionLogin } from '@/api/userManagement'

const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref()
const institutionFormRef = ref()
const loading = ref(false)
const rememberMe = ref(false)
const loginType = ref('normal') // normal | institution

const loginForm = reactive({
  email: '',
  password: ''
})

const institutionForm = reactive({
  school_code: '',
  number: '',
  password: ''
})

const loginRules = {
  email: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' },
    { min: 3, message: '用户名或邮箱至少3个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

const institutionRules = {
  school_code: [
    { required: true, message: '请输入学校代码', trigger: 'blur' },
    { min: 2, message: '学校代码至少2个字符', trigger: 'blur' }
  ],
  number: [
    { required: true, message: '请输入工号/学号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

const handleLoginTypeChange = () => {
  // 清空表单
  if (loginType.value === 'normal') {
    institutionFormRef.value?.clearValidate()
  } else {
    loginFormRef.value?.clearValidate()
  }
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await userStore.loginUser(loginForm.email, loginForm.password)
        ElMessage.success('登录成功！')
        
        // 使用 nextTick 确保状态更新完成后再跳转
        await router.push('/agents')
      } catch (error) {
        logger.error('登录失败:', error)
        ElMessage.error('登录失败，请检查用户名/邮箱和密码')
      } finally {
        loading.value = false
      }
    }
  })
}

const handleInstitutionLogin = async () => {
  if (!institutionFormRef.value) return
  
  await institutionFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const response = await institutionLogin(institutionForm)
        if (response.data) {
          // 保存token和用户信息
          const { access_token, refresh_token, user } = response.data
          userStore.setToken(access_token)
          userStore.setRefreshToken(refresh_token)
          userStore.setUser(user)
          
          ElMessage.success('登录成功！')
          await router.push('/agents')
        }
      } catch (error) {
        logger.error('机构登录失败:', error)
        ElMessage.error('机构登录失败: ' + (error.response?.data?.message || '请检查学校代码、工号/学号和密码'))
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
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
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
}

.brand-content {
  text-align: center;
  color: white;
  max-width: 400px;
}

.logo {
  margin-bottom: 30px;
}

.brand-title {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 16px;
  background: linear-gradient(45deg, #fff, #e3f2fd);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-subtitle {
  font-size: 1.2rem;
  margin-bottom: 40px;
  opacity: 0.9;
  font-weight: 300;
}

.feature-list {
  text-align: left;
}

.feature-item {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  font-size: 1rem;
}

.feature-item .el-icon {
  margin-right: 12px;
  font-size: 1.2rem;
}

/* 右侧表单区域 */
.form-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
}

.form-container {
  width: 100%;
  max-width: 400px;
}

.form-header {
  text-align: center;
  margin-bottom: 30px;
}

.form-header h2 {
  font-size: 2rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 8px;
}

.form-header p {
  color: #666;
  font-size: 1rem;
}

.login-type-switch {
  margin-bottom: 30px;
  text-align: center;
}

.login-type-switch :deep(.el-radio-group) {
  width: 100%;
}

.login-type-switch :deep(.el-radio-button) {
  flex: 1;
}

.login-type-switch :deep(.el-radio-button__inner) {
  width: 100%;
  border-radius: 8px;
  padding: 12px 20px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.login-type-switch :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 8px 0 0 8px;
}

.login-type-switch :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 0 8px 8px 0;
}

.login-type-switch :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, #409eff 0%, #667eea 100%);
  border-color: #409eff;
}

.login-form {
  margin-bottom: 24px;
}

.form-input {
  height: 48px;
}

.form-input :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e0e0e0;
  transition: all 0.3s ease;
}

.form-input :deep(.el-input__wrapper:hover) {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.form-input :deep(.el-input__wrapper.is-focus) {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #409eff 0%, #667eea 100%);
  border: none;
  transition: all 0.3s ease;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(64, 158, 255, 0.3);
}

.form-footer {
  text-align: center;
  margin-bottom: 24px;
}

.form-footer p {
  color: #666;
  font-size: 0.9rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-content {
    flex-direction: column;
  }
  
  .brand-section {
    padding: 40px 20px;
    border-right: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .form-section {
    padding: 40px 20px;
  }
  
  .brand-title {
    font-size: 2rem;
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
  }
}
</style>
