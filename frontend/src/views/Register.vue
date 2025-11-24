<template>
  <div class="register-container">
    <div class="register-box">
      <div class="register-header">
        <h2>注册账户</h2>
        <p>创建您的物联网设备管理账户</p>
      </div>
      
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        class="register-form"
        @submit.prevent="handleRegister"
      >
        <el-form-item prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="请输入邮箱地址（用于接收通知）"
            prefix-icon="Message"
            type="email"
            autocomplete="off"
          />
        </el-form-item>
        
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="请输入用户名（登录时使用，3-20位字母数字）"
            prefix-icon="User"
            maxlength="20"
            autocomplete="off"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="至少8位，需包含大小写字母、数字和特殊字符"
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
        
        <el-form-item>
          <el-button
            type="primary"
            class="register-btn"
            :loading="loading"
            @click="handleRegister"
          >
            注册
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="register-footer">
        <el-link @click="$router.push('/login')">已有账户？立即登录</el-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()

const registerFormRef = ref()
const loading = ref(false)
const codeDisabled = ref(false)
const codeText = ref('发送验证码')
const countdown = ref(0)

const registerForm = reactive({
  email: '',
  username: '',
  password: '',
  confirmPassword: ''
})

const registerRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '请输入用户名（登录时使用）', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度必须在3-20位之间', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '用户名只能包含字母、数字、下划线和连字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' },
    { 
      pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/, 
      message: '密码必须包含大写字母、小写字母、数字和特殊字符(!@#$%^&*等)', 
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
  ]
}


const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        await userStore.registerUser(registerForm.email, registerForm.username, registerForm.password)
        // 注册成功，跳转到登录页面
        // registerUser 内部已经显示了成功消息，这里直接跳转
        router.push('/login')
      } catch (error) {
        // 错误消息已经在 registerUser 中显示，这里只记录日志
        console.error('注册失败:', error)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-box {
  width: 400px;
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
  margin-bottom: 10px;
}

.register-header p {
  color: #666;
  font-size: 14px;
}

.register-form {
  margin-bottom: 20px;
}

.code-input {
  display: flex;
  gap: 10px;
}

.code-input .el-input {
  flex: 1;
}

.register-btn {
  width: 100%;
  height: 45px;
  font-size: 16px;
}

.register-footer {
  text-align: center;
}
</style>
