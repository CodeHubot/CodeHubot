<template>
  <el-container class="pbl-layout pbl-student-layout">
    <el-header class="layout-header">
      <div class="header-left">
        <div class="logo-container">
          <el-icon :size="28" color="#f5576c"><Reading /></el-icon>
          <span class="logo-text">PBL学习平台</span>
        </div>
      </div>
      
      <div class="header-center">
        <el-menu :default-active="activeMenu" mode="horizontal" :router="true">
          <el-menu-item index="/pbl/student/courses">我的课程</el-menu-item>
          <el-menu-item index="/pbl/student/tasks">我的任务</el-menu-item>
          <el-menu-item index="/pbl/student/projects">项目学习</el-menu-item>
          <el-menu-item index="/pbl/student/portfolio">学习档案</el-menu-item>
        </el-menu>
      </div>
      
      <div class="header-right">
        <el-button text @click="backToPortal">
          <el-icon><Grid /></el-icon> 切换系统
        </el-button>
        
        <el-dropdown @command="handleCommand">
          <span class="user-dropdown">
            <el-avatar :size="32" :style="{ background: '#f5576c' }">
              {{ authStore.userName.charAt(0) }}
            </el-avatar>
            <span class="user-name">{{ authStore.userName }}</span>
          </span>
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
    </el-header>
    
    <el-main class="layout-main">
      <router-view v-slot="{ Component }">
        <transition name="fade-transform" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </el-main>
    
    <!-- 个人信息和修改密码对话框 -->
    <UserProfileDialog
      v-model="profileDialogVisible"
      :default-tab="profileDialogTab"
      :force-change-password="forceChangePassword"
      @password-changed="handlePasswordChanged"
    />
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Reading, Grid, User, Lock, SwitchButton } from '@element-plus/icons-vue'
import UserProfileDialog from '@/components/UserProfileDialog.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)

// 对话框状态
const profileDialogVisible = ref(false)
const profileDialogTab = ref('profile')
const forceChangePassword = ref(false)

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

function backToPortal() {
  router.push('/')
}

function handleCommand(command) {
  switch (command) {
    case 'profile':
      profileDialogTab.value = 'profile'
      forceChangePassword.value = false
      profileDialogVisible.value = true
      break
    case 'changePassword':
      profileDialogTab.value = 'password'
      forceChangePassword.value = false
      profileDialogVisible.value = true
      break
    case 'logout':
      ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        authStore.logout()
        router.push('/login')
        ElMessage.success('已退出登录')
      })
      break
  }
}

function handlePasswordChanged() {
  forceChangePassword.value = false
  ElMessage.success('密码修改成功')
}
</script>

<style scoped lang="scss">
.pbl-student-layout {
  height: 100vh;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 5%, white 5%);
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  padding: 0 24px;
  
  .header-left {
    .logo-container {
      display: flex;
      align-items: center;
      gap: 12px;
      
      .logo-text {
        font-size: 20px;
        font-weight: 600;
        color: #2c3e50;
      }
    }
  }
  
  .header-center {
    flex: 1;
    display: flex;
    justify-content: center;
    
    .el-menu {
      border-bottom: none;
      background: transparent;
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 20px;
    
    .user-dropdown {
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
      
      .user-name {
        font-size: 14px;
        color: #2c3e50;
      }
      
      &:hover .user-name {
        color: #f5576c;
      }
    }
  }
}

.layout-main {
  background: #f8f9fa;
  padding: 24px;
  overflow-y: auto;
}

.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
