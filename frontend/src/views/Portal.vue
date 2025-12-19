<template>
  <div class="portal-container">
    <!-- Loading 状态 -->
    <div v-if="loading" class="portal-loading">
      <el-icon class="loading-icon" :size="48"><Loading /></el-icon>
      <p>正在加载用户信息...</p>
    </div>
    
    <!-- 用户信息栏 -->
    <div v-else class="portal-user-bar">
      <div class="user-info">
        <el-dropdown @command="handleUserCommand" trigger="click">
          <div class="user-info-trigger">
            <el-avatar :size="36">{{ authStore.userName.charAt(0) }}</el-avatar>
            <div class="user-details">
              <span class="user-name">{{ authStore.userName }}</span>
              <span class="user-role">{{ getRoleText(authStore.userRole) }}</span>
            </div>
            <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon> 个人信息
              </el-dropdown-item>
              <el-dropdown-item command="changePassword">
                <el-icon><Lock /></el-icon> 修改密码
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <div v-if="!loading" class="portal-header">
      <h1>{{ platformName }}</h1>
      <p>{{ platformDescription }} - 欢迎，{{ authStore.userName }}！请选择您要进入的系统</p>
    </div>
    
    <div v-if="!loading" class="portal-cards">
      <!-- Device管理系统 -->
      <div v-if="canAccessDevice" class="portal-card device-card" @click="enterDevice">
        <div class="card-icon">
          <el-icon :size="40"><Setting /></el-icon>
        </div>
        <h2>设备管理系统</h2>
        <p class="card-description">管理物联网设备、查看实时数据、远程控制</p>
        <ul class="card-features">
          <li><el-icon><Check /></el-icon> 设备监控与管理</li>
          <li><el-icon><Check /></el-icon> 实时数据分析</li>
          <li><el-icon><Check /></el-icon> 远程控制</li>
          <li><el-icon><Check /></el-icon> 固件管理</li>
        </ul>
        <el-button type="primary" size="large" class="enter-btn">
          进入系统 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
        </el-button>
      </div>
      
      <!-- 智能体开发系统 -->
      <div v-if="authStore.isAuthenticated" class="portal-card ai-card" @click="enterAI">
        <div class="card-icon">
          <el-icon :size="40"><MagicStick /></el-icon>
        </div>
        <h2>智能体开发系统</h2>
        <p class="card-description">智能体开发、工作流编排、知识库管理、插件开发</p>
        <ul class="card-features">
          <li><el-icon><Check /></el-icon> AI对话与智能体</li>
          <li><el-icon><Check /></el-icon> 工作流编排</li>
          <li><el-icon><Check /></el-icon> 知识库管理</li>
          <li><el-icon><Check /></el-icon> 插件开发</li>
        </ul>
        <el-button type="primary" size="large" class="enter-btn" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none;">
          进入系统 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
        </el-button>
      </div>
      
      <!-- PBL学习平台 - 学习/教学入口（所有用户可见） -->
      <div v-if="authStore.isAuthenticated" class="portal-card pbl-card" @click="enterPBLLearning">
        <div class="card-icon">
          <el-icon :size="40"><Reading /></el-icon>
        </div>
        <h2>PBL学习系统</h2>
        <p class="card-description">项目式学习、课程管理、学习进度跟踪</p>
        <ul class="card-features">
          <li><el-icon><Check /></el-icon> 我的课程</li>
          <li><el-icon><Check /></el-icon> 项目学习</li>
          <li><el-icon><Check /></el-icon> 作业管理</li>
          <li><el-icon><Check /></el-icon> 学习档案</li>
        </ul>
        <el-button type="primary" size="large" class="enter-btn" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border: none;">
          进入系统 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
        </el-button>
      </div>
      
      <!-- 学校管理平台 - 学校级管理（教师和学校管理员） -->
      <div v-if="authStore.isTeacher || isSchoolAdmin" class="portal-card school-card" @click="enterSchoolManagement">
        <div class="card-icon">
          <el-icon :size="40"><School /></el-icon>
        </div>
        <h2>学校管理系统</h2>
        <p class="card-description">本校师生管理、班级管理、课程配置、数据统计</p>
        <ul class="card-features">
          <li><el-icon><Check /></el-icon> 教师管理</li>
          <li><el-icon><Check /></el-icon> 学生管理</li>
          <li><el-icon><Check /></el-icon> 班级管理</li>
          <li><el-icon><Check /></el-icon> 数据统计</li>
        </ul>
        <el-button type="warning" size="large" class="enter-btn">
          管理入口 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
        </el-button>
      </div>
      
      <!-- 系统管理平台 - 统一的管理后台（管理员和渠道管理员可见） -->
      <div 
        v-if="isAdmin || isChannelManager" 
        class="portal-card admin-card" 
        @click="enterManagement">
        <div class="card-icon">
          <el-icon :size="40"><User /></el-icon>
        </div>
        <h2>平台管理系统</h2>
        <p class="card-description">PBL系统管理、渠道管理、用户管理、数据统计</p>
        <ul class="card-features">
          <li><el-icon><Check /></el-icon> 用户与学校管理</li>
          <li><el-icon><Check /></el-icon> 课程模板配置</li>
          <li><el-icon><Check /></el-icon> 渠道商管理</li>
          <li><el-icon><Check /></el-icon> 数据统计分析</li>
        </ul>
        <el-button type="danger" size="large" class="enter-btn">
          管理入口 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
        </el-button>
      </div>
      
      <!-- 渠道商平台 -->
      <div 
        v-if="authStore.isAuthenticated && authStore.isChannelPartner" 
        class="portal-card channel-card" 
        @click="enterChannel">
        <div class="card-icon">
          <el-icon :size="40"><Connection /></el-icon>
        </div>
        <h2>渠道商系统</h2>
        <p class="card-description">合作学校管理、课程监控、数据查看</p>
        <ul class="card-features">
          <li><el-icon><Check /></el-icon> 学校管理</li>
          <li><el-icon><Check /></el-icon> 课程监控</li>
          <li><el-icon><Check /></el-icon> 数据统计</li>
          <li><el-icon><Check /></el-icon> 进度跟踪</li>
        </ul>
        <el-button 
          type="info" 
          size="large" 
          class="enter-btn">
          渠道商入口 
          <el-icon class="el-icon--right"><ArrowRight /></el-icon>
        </el-button>
      </div>
    </div>
    
    <!-- 个人信息和修改密码对话框 -->
    <UserProfileDialog
      v-model="profileDialogVisible"
      :default-tab="profileDialogTab"
      :force-change-password="forceChangePassword"
      @password-changed="handlePasswordChanged"
      @profile-updated="handleProfileUpdated"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Setting, Reading, User, Check, ArrowRight, SwitchButton, MagicStick, Connection, Loading, School, Lock, ArrowDown
} from '@element-plus/icons-vue'
import { useAuth, getRoleText } from '@/composables/useAuth'
import UserProfileDialog from '@/components/UserProfileDialog.vue'

const router = useRouter()
const { authStore, loading, isAdmin, isSchoolAdmin, isChannelManager, platformName, platformDescription } = useAuth()

// 对话框状态
const profileDialogVisible = ref(false)
const profileDialogTab = ref('profile')
const forceChangePassword = ref(false)

// 简化计算属性
const canAccessDevice = computed(() => authStore.isAuthenticated)

// 检查是否需要强制修改密码
onMounted(() => {
  checkForceChangePassword()
})

function checkForceChangePassword() {
  if (authStore.userInfo?.need_change_password) {
    forceChangePassword.value = true
    profileDialogVisible.value = true
    profileDialogTab.value = 'password'
    ElMessage.warning('检测到您是首次登录，请先修改密码')
  }
}

// 进入不同系统
function enterDevice() {
  router.push('/device/dashboard')
}

function enterAI() {
  router.push('/ai/dashboard')
}

// 进入 PBL 学习平台 - 学习/教学功能（根据角色跳转）
function enterPBLLearning() {
  const role = authStore.userInfo?.role
  
  // 根据角色跳转到学习或教学界面
  if (role === 'teacher') {
    // 教师 -> 教学平台
    router.push('/pbl/teacher/dashboard')
  } else if (role === 'student') {
    // 学生 -> 学习平台
    router.push('/pbl/student/courses')
  } else {
    // 其他角色（包括管理员）默认进入学生视角（浏览模式）
    router.push('/pbl/student/courses')
  }
}

// 进入学校管理平台 - 学校级管理
function enterSchoolManagement() {
  // 教师和学校管理员都进入学校管理平台
  // 内部通过权限控制显示不同的功能菜单
  router.push('/pbl/school/dashboard')
}

// 进入系统管理平台 - 统一的管理后台
function enterManagement() {
  // 统一进入管理后台，内部通过侧边栏菜单和权限控制显示不同模块
  router.push('/pbl/admin/schools')
}

function enterChannel() {
  router.push('/pbl/channel/schools')
}

// 用户下拉菜单命令处理
function handleUserCommand(command) {
  switch (command) {
    case 'profile':
      profileDialogTab.value = 'profile'
      profileDialogVisible.value = true
      break
    case 'changePassword':
      profileDialogTab.value = 'password'
      forceChangePassword.value = false
      profileDialogVisible.value = true
      break
    case 'logout':
      handleLogout()
      break
  }
}

// 退出登录
function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    authStore.logout()
    router.push('/login')
    ElMessage.success('已退出登录')
  }).catch(() => {
    // 取消退出
  })
}

// 密码修改成功回调
function handlePasswordChanged() {
  forceChangePassword.value = false
  ElMessage.success('密码修改成功，欢迎使用系统')
}

// 个人信息更新成功回调
function handleProfileUpdated() {
  ElMessage.success('个人信息更新成功')
}
</script>

<style scoped lang="scss">
.portal-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0 20px 40px;
  position: relative;
}

.portal-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  color: white;
  
  .loading-icon {
    animation: rotate 1.5s linear infinite;
    margin-bottom: 20px;
  }
  
  p {
    font-size: 18px;
    opacity: 0.9;
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.portal-user-bar {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
  
  .user-info {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 50px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
    backdrop-filter: blur(10px);
    
    .user-info-trigger {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 20px;
      cursor: pointer;
      transition: all 0.3s;
      
      &:hover {
        background: rgba(0, 0, 0, 0.03);
      }
      
      .user-details {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        
        .user-name {
          color: #2c3e50;
          font-weight: 600;
          font-size: 14px;
        }
        
        .user-role {
          color: #999;
          font-size: 12px;
          margin-top: 2px;
        }
      }
      
      .dropdown-icon {
        color: #999;
        font-size: 12px;
        transition: transform 0.3s;
      }
    }
  }
}

.portal-header {
  text-align: center;
  color: white;
  margin-bottom: 60px;
  padding-top: 80px;
  
  h1 {
    font-size: 48px;
    font-weight: bold;
    margin-bottom: 15px;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  }
  
  p {
    font-size: 20px;
    opacity: 0.95;
  }
}

.portal-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 30px;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
}

.portal-card {
  background: white;
  border-radius: 20px;
  padding: 30px 25px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  
  &:hover {
    transform: translateY(-10px);
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
  }
  
  // 禁用卡片样式
  &.card-disabled {
    opacity: 0.6;
    cursor: not-allowed;
    position: relative;
    
    &::after {
      content: '需要相应权限';
      position: absolute;
      top: 20px;
      right: 20px;
      background: rgba(245, 108, 108, 0.9);
      color: white;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
    }
    
    &:hover {
      transform: translateY(0);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
    }
  }
  
  .card-icon {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    margin: 0 auto 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
  }
  
  h2 {
    font-size: 24px;
    margin-bottom: 10px;
    color: #2c3e50;
    font-weight: 600;
  }
  
  .card-description {
    color: #666;
    margin-bottom: 18px;
    line-height: 1.5;
    font-size: 14px;
  }
  
  .card-features {
    list-style: none;
    padding: 0;
    margin: 18px 0;
    text-align: left;
    
    li {
      padding: 7px 0;
      color: #555;
      font-size: 14px;
      display: flex;
      align-items: center;
      gap: 8px;
      
      .el-icon {
        color: #67c23a;
        font-size: 15px;
      }
    }
  }
  
  .enter-btn {
    margin-top: 15px;
    width: 100%;
    font-size: 15px;
    height: 44px;
  }
}

.device-card .card-icon {
  background: linear-gradient(135deg, #409eff 0%, #1e88e5 100%);
}

.ai-card .card-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.pbl-card .card-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.school-card .card-icon {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
}

.admin-card .card-icon {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
}

.channel-card .card-icon {
  background: linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%);
}

@media (max-width: 768px) {
  .portal-user-bar {
    position: static;
    margin: 20px -20px 0;
    padding: 0 20px;
    
    .user-info {
      width: 100%;
      justify-content: space-between;
      padding: 12px 20px;
      gap: 10px;
      
      .user-details {
        .user-name {
          font-size: 13px;
        }
        
        .user-role {
          font-size: 11px;
        }
      }
      
      .logout-btn {
        font-size: 12px;
        padding: 6px 10px;
        margin-left: 5px;
      }
    }
  }
  
  .portal-header {
    padding-top: 30px;
    margin-bottom: 40px;
    
    h1 {
      font-size: 32px;
    }
    
    p {
      font-size: 16px;
    }
  }
  
  .portal-cards {
    grid-template-columns: 1fr;
  }
}
</style>
