<template>
  <el-container class="device-layout">
    <el-aside :width="isCollapse ? '64px' : '240px'" class="layout-aside">
      <div class="logo-container">
        <el-icon :size="28"><Cpu /></el-icon>
        <span v-if="!isCollapse" class="logo-text">设备管理</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :router="true"
        class="layout-menu"
      >
        <!-- 所有用户都可以看到的菜单 -->
        <el-menu-item index="/device/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <span>控制台</span>
        </el-menu-item>
        
        <el-menu-item index="/device/device-register">
          <el-icon><Plus /></el-icon>
          <span>设备注册</span>
        </el-menu-item>
        
        <el-menu-item index="/device/devices">
          <el-icon><Cpu /></el-icon>
          <span>设备列表</span>
        </el-menu-item>
        
        <!-- 教师、学校管理员、平台管理员可以看到设备授权 -->
        <el-menu-item 
          v-if="canAccessAuthorization"
          index="/device/device-pbl-authorization"
        >
          <el-icon><Key /></el-icon>
          <span>设备授权</span>
        </el-menu-item>
        
        <!-- 设备分组暂时隐藏 -->
        <!-- <el-menu-item index="/device/device-groups">
          <el-icon><FolderOpened /></el-icon>
          <span>设备分组</span>
        </el-menu-item> -->
        
        <!-- 只有平台管理员可以看到产品管理 -->
        <el-menu-item 
          v-if="isPlatformAdmin"
          index="/device/products"
        >
          <el-icon><Box /></el-icon>
          <span>产品管理</span>
        </el-menu-item>
        
        <!-- 固件管理暂时隐藏 -->
        <!-- <el-menu-item 
          v-if="isPlatformAdmin"
          index="/device/firmware"
        >
          <el-icon><Document /></el-icon>
          <span>固件管理</span>
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
            <el-breadcrumb-item>设备管理</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <el-button text @click="backToPortal">
            <el-icon><Grid /></el-icon> 切换系统
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
            <keep-alive>
              <component :is="Component" />
            </keep-alive>
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
      @profile-updated="handleProfileUpdated"
    />
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  HomeFilled, Cpu, FolderOpened, Box, Document, Key,
  Expand, Fold, Grid, Setting, Plus, User, Lock, SwitchButton
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

// 角色判断
const userRole = computed(() => authStore.userInfo?.role || 'individual')
const isPlatformAdmin = computed(() => userRole.value === 'platform_admin')
const isSchoolAdmin = computed(() => userRole.value === 'school_admin')
const isTeacher = computed(() => userRole.value === 'teacher')
const isStudent = computed(() => userRole.value === 'student')
const isIndividual = computed(() => userRole.value === 'individual')

// 权限判断
// 教师、学校管理员、平台管理员可以访问设备授权功能
const canAccessAuthorization = computed(() => 
  isPlatformAdmin.value || isSchoolAdmin.value || isTeacher.value
)

function toggleCollapse() {
  isCollapse.value = !isCollapse.value
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

// 密码修改成功回调
function handlePasswordChanged() {
  forceChangePassword.value = false
  ElMessage.success('密码修改成功')
}

// 个人信息更新成功回调
function handleProfileUpdated() {
  ElMessage.success('个人信息更新成功')
}
</script>

<style scoped lang="scss">
.device-layout {
  height: 100vh;
}

.layout-aside {
  background: #001529;
  transition: width 0.3s;
  overflow: hidden;
  
  .logo-container {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 0 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    color: white;
    
    .logo-text {
      font-size: 18px;
      font-weight: 600;
    }
  }
  
  .layout-menu {
    border: none;
    background: transparent;
    
    // 设置菜单项文字颜色
    :deep(.el-menu-item) {
      color: rgba(255, 255, 255, 0.85);
      
      &:hover {
        color: #fff;
        background-color: rgba(255, 255, 255, 0.1);
      }
      
      &.is-active {
        color: #409eff;
        background-color: rgba(64, 158, 255, 0.1);
      }
    }
    
    // 设置子菜单标题文字颜色
    :deep(.el-sub-menu__title) {
      color: rgba(255, 255, 255, 0.85);
      
      &:hover {
        color: #fff;
        background-color: rgba(255, 255, 255, 0.1);
      }
    }
    
    // 设置展开的子菜单背景
    :deep(.el-sub-menu .el-menu) {
      background-color: rgba(0, 0, 0, 0.2);
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
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 20px;
    
    .collapse-icon {
      font-size: 20px;
      cursor: pointer;
      
      &:hover {
        color: #409eff;
      }
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
        color: #409eff;
      }
    }
  }
}

.layout-main {
  background: #f5f7fa;
  padding: 20px;
}

/* 路由过渡动画 */
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
