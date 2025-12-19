<template>
  <el-container class="pbl-layout pbl-teacher-layout">
    <el-aside width="240px" class="layout-aside">
      <div class="logo-container">
        <el-icon :size="28" color="#fcb69f"><Notebook /></el-icon>
        <span class="logo-text">PBL教学平台</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :router="true"
        class="layout-menu"
      >
        <el-menu-item index="/pbl/teacher/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <span>教师工作台</span>
        </el-menu-item>
        
        <el-menu-item index="/pbl/teacher/courses">
          <el-icon><Reading /></el-icon>
          <span>课程管理</span>
        </el-menu-item>
        
        <el-menu-item index="/pbl/teacher/grading">
          <el-icon><EditPen /></el-icon>
          <span>作业批改</span>
        </el-menu-item>
        
        <el-menu-item index="/pbl/teacher/students">
          <el-icon><User /></el-icon>
          <span>学生管理</span>
        </el-menu-item>
        
        <el-menu-item index="/pbl/teacher/analytics">
          <el-icon><TrendCharts /></el-icon>
          <span>数据分析</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header class="layout-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>PBL教学平台</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <el-button text @click="backToPortal">
            <el-icon><Grid /></el-icon> 切换系统
          </el-button>
          
          <el-dropdown @command="handleCommand">
            <span class="user-dropdown">
              <el-avatar :size="32" :style="{ background: '#fcb69f' }">
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
    </el-container>
    
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
import {
  Notebook, HomeFilled, Reading, EditPen, User, TrendCharts, Grid, Lock, SwitchButton
} from '@element-plus/icons-vue'
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
.pbl-teacher-layout {
  height: 100vh;
}

.layout-aside {
  background: linear-gradient(180deg, #ffecd2 0%, #fcb69f 100%);
  
  .logo-container {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    
    .logo-text {
      font-size: 18px;
      font-weight: 600;
      color: #d35400;
    }
  }
  
  .layout-menu {
    border: none;
    background: transparent;
    
    :deep(.el-menu-item) {
      color: #d35400;
      
      &:hover {
        background: rgba(255, 255, 255, 0.3);
      }
      
      &.is-active {
        background: rgba(255, 255, 255, 0.5);
        font-weight: 600;
      }
    }
  }
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  border-bottom: 1px solid #f0f0f0;
  padding: 0 20px;
  
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
        color: #fcb69f;
      }
    }
  }
}

.layout-main {
  background: #f5f7fa;
  padding: 20px;
}

.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
