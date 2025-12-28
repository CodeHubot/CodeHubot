<template>
  <el-container class="pbl-layout pbl-school-layout">
    <el-aside width="240px" class="layout-aside">
      <div class="logo-container">
        <el-icon :size="28" color="white"><School /></el-icon>
        <span class="logo-text">学校管理平台</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :router="true"
        class="layout-menu"
      >
        <!-- 学校管理员功能 -->
        <template v-if="authStore.isSchoolAdmin">
          <el-menu-item index="/pbl/school/dashboard">
            <el-icon><HomeFilled /></el-icon>
            <span>概览</span>
          </el-menu-item>
          
          <el-menu-item index="/pbl/school/users">
            <el-icon><UserFilled /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          
          <el-menu-item index="/pbl/school/classes">
            <el-icon><School /></el-icon>
            <span>项目式课程管理</span>
          </el-menu-item>
          
          <el-menu-item index="/pbl/school/available-templates">
            <el-icon><Files /></el-icon>
            <span>课程模板库</span>
          </el-menu-item>
          
          <el-menu-item index="/pbl/school/learning-assistant">
            <el-icon><ChatDotRound /></el-icon>
            <span>AI学习助手</span>
          </el-menu-item>
        </template>
        
        <!-- 教师功能 -->
        <template v-else-if="authStore.isTeacher">
          <el-menu-item index="/pbl/school/dashboard">
            <el-icon><HomeFilled /></el-icon>
            <span>教师工作台</span>
          </el-menu-item>
          
          <el-menu-item index="/pbl/school/classes">
            <el-icon><School /></el-icon>
            <span>我的班级课程</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header class="layout-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>学校管理平台</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <el-button text @click="backToPortal">
            <el-icon><Grid /></el-icon> 切换系统
          </el-button>
          
          <el-dropdown @command="handleCommand">
            <span class="user-dropdown">
              <el-avatar :size="32" :style="{ background: '#fcb69f' }">
                {{ authStore.userName?.charAt(0) || 'U' }}
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
  School, HomeFilled, User, UserFilled, Files, Grid, Lock, SwitchButton, Reading, EditPen, ChatDotRound
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
.pbl-school-layout {
  height: 100vh;
  overflow: hidden;
  
  .layout-aside {
    background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
    color: white;
    height: 100vh;
    position: fixed;
    left: 0;
    top: 0;
    overflow-y: auto;
    overflow-x: hidden;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
    z-index: 1000;
    
    &::-webkit-scrollbar {
      width: 6px;
    }
    
    &::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.2);
      border-radius: 3px;
    }
    
    &::-webkit-scrollbar-thumb:hover {
      background: rgba(255, 255, 255, 0.3);
    }
    
    .logo-container {
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      padding: 0 20px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      background: rgba(255, 255, 255, 0.05);
      
      .logo-text {
        font-size: 20px;
        font-weight: 600;
        color: white;
        letter-spacing: 1px;
      }
    }
    
    .layout-menu {
      border: none;
      background: transparent;
      padding: 10px 0;
      
      :deep(.el-menu-item) {
        color: rgba(255, 255, 255, 0.75);
        margin: 4px 12px;
        border-radius: 8px;
        transition: all 0.3s ease;
        
        &:hover {
          background: rgba(64, 158, 255, 0.15);
          color: #409eff;
        }
        
        &.is-active {
          background: linear-gradient(90deg, #409eff 0%, #66b1ff 100%);
          color: white;
          font-weight: 500;
          box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
        }
      }
    }
  }
  
  // 主内容容器（包含 header 和 main）
  > .el-container {
    margin-left: 240px;
  }
  
  .layout-header {
    height: 60px;
    background: white;
    border-bottom: 1px solid #e4e7ed;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 24px;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
    
    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;
      
      :deep(.el-breadcrumb__item) {
        .el-breadcrumb__inner {
          color: #606266;
          font-weight: 500;
          
          &:hover {
            color: #409eff;
          }
        }
        
        &:last-child .el-breadcrumb__inner {
          color: #303133;
        }
      }
    }
    
    .header-right {
      display: flex;
      align-items: center;
      gap: 16px;
      
      .user-dropdown {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        padding: 8px 12px;
        border-radius: 8px;
        transition: all 0.3s ease;
        
        &:hover {
          background: #f5f7fa;
        }
        
        .user-name {
          font-size: 14px;
          color: #303133;
          font-weight: 500;
        }
      }
    }
  }
  
  .layout-main {
    background: #f5f7fa;
    padding: 24px;
    height: calc(100vh - 60px);
    overflow-y: auto;
  }
}

.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.3s ease;
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
