<template>
  <el-container class="platform-layout">
    <el-aside :width="isCollapse ? '64px' : '240px'" class="layout-aside">
      <div class="logo-container">
        <el-icon :size="28"><Setting /></el-icon>
        <span v-if="!isCollapse" class="logo-text">平台管理</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :router="true"
        class="layout-menu"
      >
        <el-menu-item index="/platform/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <span>控制台</span>
        </el-menu-item>
        
        <el-menu-item index="/platform/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        
        <el-menu-item index="/platform/products">
          <el-icon><Box /></el-icon>
          <span>产品管理</span>
        </el-menu-item>
        
        <el-menu-item index="/platform/platform-config">
          <el-icon><Setting /></el-icon>
          <span>平台配置</span>
        </el-menu-item>
        
        <el-menu-item index="/platform/module-config">
          <el-icon><Grid /></el-icon>
          <span>模块配置</span>
        </el-menu-item>
        
        <el-menu-item index="/platform/mqtt-config">
          <el-icon><Connection /></el-icon>
          <span>MQTT服务器配置</span>
        </el-menu-item>
        
        <!-- 系统日志和数据概览暂时隐藏 -->
        <!-- <el-menu-item index="/platform/system-logs">
          <el-icon><Document /></el-icon>
          <span>系统日志</span>
        </el-menu-item>
        
        <el-menu-item index="/platform/data-overview">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据概览</span>
        </el-menu-item> -->
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon class="collapse-icon" @click="toggleCollapse">
            <Expand v-if="isCollapse" />
            <Fold v-else />
          </el-icon>
          
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>平台管理</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <el-button type="success" plain @click="goToDeviceSystem">
            <el-icon><Cpu /></el-icon> 设备管理
          </el-button>
          
          <el-button type="primary" plain @click="goToAISystem">
            <el-icon><MagicStick /></el-icon> AI系统
          </el-button>
          
          <el-dropdown @command="handleCommand">
            <span class="user-dropdown">
              <el-avatar :size="32">{{ authStore.userName.charAt(0) }}</el-avatar>
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

    <!-- 个人信息对话框 -->
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
  HomeFilled, Cpu, Box, Document, Tools, DataAnalysis,
  Expand, Fold, Grid, Setting, User, Lock, SwitchButton, MagicStick, Connection
} from '@element-plus/icons-vue'
import UserProfileDialog from '@/components/UserProfileDialog.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isCollapse = ref(false)
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

function toggleCollapse() {
  isCollapse.value = !isCollapse.value
}

// 跳转到设备管理系统
function goToDeviceSystem() {
  router.push('/device/dashboard')
}

// 跳转到AI智能体系统
function goToAISystem() {
  router.push('/ai/dashboard')
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
      }).catch(() => {})
      break
  }
}

function handlePasswordChanged() {
  forceChangePassword.value = false
  profileDialogVisible.value = false
  ElMessage.success('密码修改成功')
}
</script>

<style scoped>
.platform-layout {
  height: 100vh;
  background-color: #f5f7fa;
}

.layout-aside {
  background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);
  transition: width 0.3s;
  overflow: hidden;
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  gap: 8px;
}

.logo-text {
  white-space: nowrap;
}

.layout-menu {
  border: none;
  background: transparent;
}

.layout-menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.85);
  transition: all 0.3s;
}

.layout-menu :deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
}

.layout-menu :deep(.el-menu-item.is-active) {
  background-color: rgba(255, 255, 255, 0.15);
  color: white;
}

.layout-header {
  background: white;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.collapse-icon {
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s;
}

.collapse-icon:hover {
  color: #409eff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.3s;
}

.user-dropdown:hover {
  background-color: #f5f7fa;
}

.user-name {
  font-size: 14px;
  color: #606266;
}

.layout-main {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

/* 页面切换动画 */
.fade-transform-enter-active,
.fade-transform-leave-active {
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
