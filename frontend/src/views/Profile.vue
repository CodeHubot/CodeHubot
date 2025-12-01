<template>
  <div class="profile-content">
    <!-- 用户信息卡片 -->
    <div class="profile-header">
      <div class="profile-banner">
        <div class="banner-bg"></div>
        <div class="profile-info">
          <el-avatar :size="120" :src="userAvatar" class="profile-avatar">
            <el-icon size="48"><User /></el-icon>
          </el-avatar>
          <div class="user-details">
            <h1>{{ userStore.userInfo?.username || '用户' }}</h1>
            <p>{{ userStore.userInfo?.email }}</p>
            <div class="user-stats">
              <div class="stat-item">
                <span class="stat-number">{{ userStats.deviceCount }}</span>
                <span class="stat-label">设备数量</span>
              </div>
              <div class="stat-item">
                <span class="stat-number">{{ userStats.onlineCount }}</span>
                <span class="stat-label">在线设备</span>
              </div>
              <div class="stat-item">
                <span class="stat-number">{{ userStats.loginDays }}</span>
                <span class="stat-label">登录天数</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="profile-main">
      <el-row :gutter="24">
        <!-- 个人信息 -->
        <el-col :xs="24" :md="12">
          <el-card class="info-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon size="20" color="#409EFF"><User /></el-icon>
                <span>个人信息</span>
              </div>
            </template>
            <el-form :model="userForm" label-width="80px" class="profile-form">
              <el-form-item label="用户名">
                <el-input v-model="userForm.username" placeholder="请输入用户名" />
              </el-form-item>
              <el-form-item label="昵称">
                <el-input v-model="userForm.nickname" placeholder="请输入昵称（可选）" />
              </el-form-item>
              <el-form-item label="邮箱">
                <el-input v-model="userForm.email" placeholder="请输入邮箱（可选）" />
              </el-form-item>
              <el-form-item label="注册时间">
                <el-input v-model="userForm.created_at" disabled />
              </el-form-item>
              <el-form-item label="最后登录">
                <el-input v-model="userForm.last_login" disabled />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="updateProfile" :loading="updateLoading">
                  <el-icon><Check /></el-icon>
                  更新信息
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>

        <!-- 修改密码 -->
        <el-col :xs="24" :md="12">
          <el-card class="info-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon size="20" color="#E6A23C"><Lock /></el-icon>
                <span>修改密码</span>
              </div>
            </template>
            <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="80px" class="profile-form">
              <el-form-item label="当前密码" prop="currentPassword">
                <el-input v-model="passwordForm.currentPassword" type="password" show-password placeholder="请输入当前密码" />
              </el-form-item>
              <el-form-item label="新密码" prop="newPassword">
                <el-input v-model="passwordForm.newPassword" type="password" show-password placeholder="请输入新密码" />
              </el-form-item>
              <el-form-item label="确认密码" prop="confirmPassword">
                <el-input v-model="passwordForm.confirmPassword" type="password" show-password placeholder="请再次输入新密码" />
              </el-form-item>
              <el-form-item>
                <el-button type="warning" @click="changePassword" :loading="passwordLoading">
                  <el-icon><Key /></el-icon>
                  修改密码
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="24" style="margin-top: 24px;">
        <!-- 账户安全 -->
        <el-col :xs="24" :md="12">
          <el-card class="info-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon size="20" color="#67C23A"><Lock /></el-icon>
                <span>账户安全</span>
              </div>
            </template>
            <div class="security-info">
              <div class="security-item">
                <div class="security-icon">
                  <el-icon color="#67C23A"><CircleCheck /></el-icon>
                </div>
                <div class="security-content">
                  <span class="security-label">登录状态</span>
                  <span class="security-value">已登录</span>
                </div>
              </div>
              <div class="security-item">
                <div class="security-icon">
                  <el-icon color="#67C23A"><CircleCheck /></el-icon>
                </div>
                <div class="security-content">
                  <span class="security-label">密码强度</span>
                  <span class="security-value">强</span>
                </div>
              </div>
              <div class="security-item">
                <div class="security-icon">
                  <el-icon color="#E6A23C"><Warning /></el-icon>
                </div>
                <div class="security-content">
                  <span class="security-label">两步验证</span>
                  <span class="security-value">未启用</span>
                </div>
                <el-button type="text" size="small">启用</el-button>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 系统偏好 -->
        <el-col :xs="24" :md="12">
          <el-card class="info-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon size="20" color="#909399"><Setting /></el-icon>
                <span>系统偏好</span>
              </div>
            </template>
            <div class="preferences">
              <div class="preference-item">
                <div class="preference-label">
                  <span>邮件通知</span>
                  <p>接收系统通知和设备警报</p>
                </div>
                <el-switch v-model="preferences.emailNotification" />
              </div>
              <div class="preference-item">
                <div class="preference-label">
                  <span>短信通知</span>
                  <p>接收重要警报的短信通知</p>
                </div>
                <el-switch v-model="preferences.smsNotification" />
              </div>
              <div class="preference-item">
                <div class="preference-label">
                  <span>深色模式</span>
                  <p>使用深色主题界面</p>
                </div>
                <el-switch v-model="preferences.darkMode" />
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 活动日志 -->
      <el-row style="margin-top: 24px;">
        <el-col :span="24">
          <el-card class="info-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <el-icon size="20" color="#909399"><Document /></el-icon>
                <span>最近活动</span>
              </div>
            </template>
            <div class="activity-log">
              <div v-for="activity in activities" :key="activity.id" class="activity-item">
                <div class="activity-icon">
                  <el-icon :color="activity.color">
                    <component :is="activity.icon" />
                  </el-icon>
                </div>
                <div class="activity-content">
                  <div class="activity-title">{{ activity.title }}</div>
                  <div class="activity-time">{{ activity.time }}</div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User, Lock, Key, Setting, Check, CircleCheck, Warning, Document,
  Monitor, UserFilled, Edit
} from '@element-plus/icons-vue'
import { getUserInfo, updateProfile as updateUserProfile, changePassword as changeUserPassword, getUserStats } from '@/api/auth'
import logger from '@/utils/logger'

const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const updateLoading = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref()

// 用户统计数据
const userStats = reactive({
  deviceCount: 15,
  onlineCount: 12,
  loginDays: 45
})

// 用户表单
const userForm = reactive({
  username: '',
  nickname: '',
  email: '',
  created_at: '',
  last_login: ''
})

// 密码表单
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 系统偏好
const preferences = reactive({
  emailNotification: true,
  smsNotification: false,
  darkMode: false
})

// 活动日志
const activities = ref([
  {
    id: 1,
    title: '登录系统',
    time: '2024-01-15 14:30:25',
    icon: 'UserFilled',
    color: '#67C23A'
  },
  {
    id: 2,
    title: '查看设备详情',
    time: '2024-01-15 14:25:10',
    icon: 'Monitor',
    color: '#409EFF'
  },
  {
    id: 3,
    title: '修改个人信息',
    time: '2024-01-15 10:15:30',
    icon: 'Edit',
    color: '#E6A23C'
  }
])

// 密码验证规则
const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' },
    { 
      pattern: /^(?=.*[A-Za-z])(?=.*\d).+$/,
      message: '密码必须包含字母和数字',
      trigger: 'blur'
    }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 计算属性
const userAvatar = computed(() => {
  return `https://api.dicebear.com/7.x/avataaars/svg?seed=${userStore.userInfo?.username || 'user'}`
})

// 方法
const loadUserInfo = async () => {
  try {
    // 获取用户信息
    const userResponse = await getUserInfo()
    if (userResponse.data) {
      userForm.username = userResponse.data.username
      userForm.nickname = userResponse.data.nickname || ''
      userForm.email = userResponse.data.email
      userForm.created_at = userResponse.data.created_at ? new Date(userResponse.data.created_at).toLocaleString() : '未知'
      userForm.last_login = userResponse.data.last_login ? new Date(userResponse.data.last_login).toLocaleString() : '未知'
    }

    // 获取用户统计信息
    const statsResponse = await getUserStats()
    if (statsResponse.data) {
      userStats.deviceCount = statsResponse.data.device_count || 0
      userStats.onlineCount = statsResponse.data.online_count || 0
      userStats.loginDays = statsResponse.data.login_days || 0
    }
  } catch (error) {
    logger.error('加载用户信息失败:', error)
    ElMessage.error('加载用户信息失败')
    
    // 使用备用数据
    userForm.username = userStore.userInfo?.username || '管理员'
    userForm.email = userStore.userInfo?.email || 'admin@example.com'
    userForm.created_at = '2023-06-15 10:30:00'
    userForm.last_login = '2024-01-15 14:30:25'
    
    userStats.deviceCount = 5
    userStats.onlineCount = 3
    userStats.loginDays = 30
  }
}

const updateProfile = async () => {
  updateLoading.value = true
  try {
    // 调用API更新用户信息
    const response = await updateUserProfile({
      username: userForm.username,
      nickname: userForm.nickname || null,
      email: userForm.email || null
    })
    
    if (response.data) {
      // 更新store中的用户信息
      userStore.userInfo.username = response.data.username
      userStore.userInfo.nickname = response.data.nickname
      userStore.userInfo.email = response.data.email
      ElMessage.success('个人信息更新成功')
    }
  } catch (error) {
    logger.error('更新个人信息失败:', error)
    const errorMsg = error.response?.data?.detail || '更新失败，请重试'
    ElMessage.error(errorMsg)
  } finally {
    updateLoading.value = false
  }
}

const changePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      passwordLoading.value = true
      try {
        // 调用API修改密码
        const response = await changeUserPassword({
          old_password: passwordForm.currentPassword,
          new_password: passwordForm.newPassword
        })
        
        if (response.data) {
          // 重置表单
          passwordForm.currentPassword = ''
          passwordForm.newPassword = ''
          passwordForm.confirmPassword = ''
          passwordFormRef.value.resetFields()
          
          ElMessage.success('密码修改成功')
        }
      } catch (error) {
        logger.error('密码修改失败:', error)
        const errorMsg = error.response?.data?.detail || '密码修改失败，请重试'
        ElMessage.error(errorMsg)
      } finally {
        passwordLoading.value = false
      }
    }
  })
}

onMounted(() => {
  loadUserInfo()
})
</script>

<style scoped>
.profile-content {
  max-width: 1200px;
  margin: 0 auto;
}

/* 用户信息头部 */
.profile-header {
  margin-bottom: 24px;
}

.profile-banner {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.banner-bg {
  height: 200px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.profile-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 24px;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.8), transparent);
  color: white;
  display: flex;
  align-items: flex-end;
  gap: 24px;
}

.profile-avatar {
  border: 4px solid white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.user-details h1 {
  margin: 0 0 8px 0;
  font-size: 2rem;
  font-weight: 700;
}

.user-details p {
  margin: 0 0 16px 0;
  opacity: 0.9;
  font-size: 1.1rem;
}

.user-stats {
  display: flex;
  gap: 32px;
}

.stat-item {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
}

/* 主要内容区域 */
.profile-main {
  padding: 0;
}

.info-card {
  border-radius: 16px;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.info-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #1e293b;
}

.profile-form {
  padding: 8px 0;
}

/* 安全信息 */
.security-info {
  padding: 8px 0;
}

.security-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
}

.security-item:last-child {
  border-bottom: none;
}

.security-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  border-radius: 8px;
}

.security-content {
  flex: 1;
}

.security-label {
  display: block;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 2px;
}

.security-value {
  font-size: 0.9rem;
  color: #64748b;
}

/* 系统偏好 */
.preferences {
  padding: 8px 0;
}

.preference-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
  border-bottom: 1px solid #f1f5f9;
}

.preference-item:last-child {
  border-bottom: none;
}

.preference-label span {
  display: block;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.preference-label p {
  margin: 0;
  font-size: 0.9rem;
  color: #64748b;
}

/* 活动日志 */
.activity-log {
  padding: 8px 0;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f1f5f9;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  border-radius: 8px;
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 2px;
}

.activity-time {
  font-size: 0.9rem;
  color: #64748b;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .profile-info {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 16px;
  }
  
  .user-stats {
    gap: 16px;
  }
  
  .stat-number {
    font-size: 1.2rem;
  }
}

@media (max-width: 480px) {
  .user-stats {
    flex-direction: column;
    gap: 12px;
  }
  
  .security-item,
  .preference-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .preference-item {
    align-items: stretch;
  }
  
  .preference-item .el-switch {
    align-self: flex-end;
  }
}
</style>