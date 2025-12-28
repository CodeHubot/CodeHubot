<template>
  <div class="pbl-student-layout">
    <!-- 顶部导航栏 -->
    <el-header class="header">
      <div class="header-left">
        <div class="logo">
          <el-icon :size="28" color="#3b82f6"><Reading /></el-icon>
          <h2>PBL 学习平台</h2>
        </div>
      </div>
      
      <div class="header-right">
        <!-- 切换系统按钮 -->
        <el-button text class="switch-system-btn" @click="backToPortal">
          <el-icon :size="18"><Grid /></el-icon>
          <span>切换系统</span>
        </el-button>
        
        <!-- 消息通知 -->
        <el-tooltip content="消息通知" placement="bottom">
          <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
            <el-button text class="action-btn">
              <el-icon :size="20"><Bell /></el-icon>
            </el-button>
          </el-badge>
        </el-tooltip>
        
        <!-- 用户信息下拉菜单 -->
        <el-dropdown @command="handleCommand" trigger="click">
          <div class="user-info">
            <el-avatar :size="32" :style="{ background: '#3b82f6' }">
              {{ userName.charAt(0) }}
            </el-avatar>
            <div class="user-details">
              <div class="user-name">{{ userName }}</div>
              <div class="user-role">学生</div>
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
    </el-header>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 侧边导航 -->
      <el-aside 
        v-if="!$route.meta.hideSidebar" 
        :width="isCollapsed ? '64px' : '250px'" 
        class="sidebar"
      >
        <div class="menu-toggle">
          <el-button 
            :icon="isCollapsed ? Expand : Fold" 
            @click="toggleSidebar"
            text
            class="toggle-btn"
          />
        </div>
        
        <el-menu
          :default-active="$route.path"
          class="sidebar-menu"
          router
          :collapse="isCollapsed"
          background-color="transparent"
          text-color="#374151"
          active-text-color="#3b82f6"
        >
          <el-menu-item index="/pbl/student/courses" class="menu-item">
            <el-icon><Reading /></el-icon>
            <template #title>我的课程</template>
          </el-menu-item>
          
          <el-menu-item index="/pbl/student/tasks" class="menu-item">
            <el-icon><Document /></el-icon>
            <template #title>我的任务</template>
          </el-menu-item>
          
          <el-menu-item index="/pbl/student/learning-assistant" class="menu-item">
            <el-icon><ChatDotRound /></el-icon>
            <template #title>AI学习助手</template>
          </el-menu-item>
          
          <el-menu-item index="/pbl/student/portfolio" class="menu-item">
            <el-icon><Collection /></el-icon>
            <template #title>学习档案</template>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <!-- 主内容 -->
      <el-main class="main-content" :class="{ 'full-width': $route.meta.hideSidebar }">
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Reading,
  Grid,
  User,
  Lock,
  SwitchButton,
  ArrowDown,
  Bell,
  Expand,
  Fold,
  Document,
  Folder,
  Collection,
  ChatDotRound
} from '@element-plus/icons-vue'
import UserProfileDialog from '@/components/UserProfileDialog.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// ===== 响应式数据 =====
const isCollapsed = ref(false)
const unreadCount = ref(0)

// 对话框状态
const profileDialogVisible = ref(false)
const profileDialogTab = ref('profile')
const forceChangePassword = ref(false)

// ===== 计算属性 =====
const userName = computed(() => {
  return authStore.userName || authStore.userInfo?.full_name || authStore.userInfo?.username || '学生用户'
})

// ===== 生命周期 =====
onMounted(() => {
  checkForceChangePassword()
  loadUnreadCount()
})

// ===== 方法 =====

/**
 * 检查是否需要强制修改密码
 */
function checkForceChangePassword() {
  if (authStore.userInfo?.need_change_password) {
    forceChangePassword.value = true
    profileDialogVisible.value = true
    profileDialogTab.value = 'password'
    ElMessage.warning('检测到您是首次登录，请先修改密码')
  }
}

/**
 * 加载未读消息数量
 */
function loadUnreadCount() {
  // TODO: 实现获取未读消息数量的API调用
  // 示例: unreadCount.value = 5
}

/**
 * 切换侧边栏折叠状态
 */
function toggleSidebar() {
  isCollapsed.value = !isCollapsed.value
}

/**
 * 返回系统门户
 */
function backToPortal() {
  router.push('/')
}

/**
 * 处理用户下拉菜单命令
 */
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
      }).catch(() => {
        // 用户取消退出
      })
      break
  }
}

/**
 * 密码修改成功回调
 */
function handlePasswordChanged() {
  forceChangePassword.value = false
  ElMessage.success('密码修改成功')
}
</script>

<style scoped lang="scss">
.pbl-student-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #f5f7fa 0%, #e0f2fe 100%);
}

// ===== 顶部导航栏 =====
.header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
  position: relative;
  z-index: 100;
  height: 64px;
}

.header-left {
  flex: 0 0 auto;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #1e293b;
  cursor: pointer;
  
  h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    background: linear-gradient(45deg, #3b82f6, #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
}

.header-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.switch-system-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px !important;
  height: 36px;
  border-radius: 8px;
  color: #64748b !important;
  font-size: 14px;
  transition: all 0.3s ease;
  
  span {
    font-weight: 500;
  }
  
  &:hover {
    background: rgba(59, 130, 246, 0.08) !important;
    color: #3b82f6 !important;
  }
}

.action-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b !important;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(59, 130, 246, 0.08) !important;
    color: #3b82f6 !important;
  }
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background-color 0.3s;
  
  &:hover {
    background-color: rgba(59, 130, 246, 0.08);
  }
}

.user-details {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.user-name {
  font-weight: 500;
  color: #1e293b;
  font-size: 14px;
  line-height: 1.2;
}

.user-role {
  font-size: 12px;
  color: #64748b;
  line-height: 1.2;
}

.dropdown-icon {
  color: #94a3b8;
  transition: transform 0.3s ease;
}

.user-info:hover .dropdown-icon {
  transform: translateY(2px);
}

// ===== 主内容区 =====
.main-container {
  flex: 1;
  overflow: hidden;
}

.sidebar {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(0, 0, 0, 0.06);
  transition: width 0.3s ease;
  overflow: hidden;
}

.menu-toggle {
  padding: 16px;
  text-align: center;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.toggle-btn {
  color: #64748b !important;
  border: none !important;
  background: transparent !important;
}

.toggle-btn:hover {
  background: rgba(59, 130, 246, 0.08) !important;
  color: #3b82f6 !important;
}

.sidebar-menu {
  border: none;
  height: calc(100vh - 128px);
  overflow-y: auto;
  background: transparent !important;
}

:deep(.menu-item) {
  margin: 4px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

:deep(.menu-item:hover) {
  background: rgba(59, 130, 246, 0.08) !important;
  transform: translateX(4px);
}

:deep(.menu-item.is-active) {
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.15), rgba(59, 130, 246, 0.08)) !important;
  color: #3b82f6 !important;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
  border-left: 3px solid #3b82f6;
}

:deep(.menu-item.is-active .el-icon) {
  color: #3b82f6;
}

.main-content {
  padding: 24px;
  overflow-y: auto;
  background: transparent;
}

.main-content.full-width {
  padding: 0;
}

// ===== 页面切换动画 =====
.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.3s ease;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

// ===== 响应式设计 =====
@media (max-width: 768px) {
  .header {
    padding: 0 16px;
  }
  
  .user-details {
    display: none;
  }
  
  .main-content {
    padding: 16px;
  }
  
  .sidebar {
    width: 64px !important;
  }
}

// ===== 滚动条样式 =====
.sidebar-menu::-webkit-scrollbar {
  width: 6px;
}

.sidebar-menu::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.sidebar-menu::-webkit-scrollbar-thumb:hover {
  background: rgba(59, 130, 246, 0.3);
}

.main-content::-webkit-scrollbar {
  width: 8px;
}

.main-content::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
}

.main-content::-webkit-scrollbar-thumb:hover {
  background: rgba(59, 130, 246, 0.3);
}
</style>
