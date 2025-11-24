<template>
  <div class="main-layout">
    <el-container>
      <!-- 移动端遮罩层 -->
      <div 
        class="mobile-overlay" 
        :class="{ show: isMobileMenuOpen }"
        @click="closeMobileMenu"
      ></div>
      
      <!-- 全新设计的侧边栏 -->
      <el-aside 
        :width="sidebarCollapsed ? '80px' : '280px'" 
        :class="['new-sidebar', { 
          'collapsed': sidebarCollapsed,
          'mobile-open': isMobileMenuOpen 
        }]"
      >
        <!-- 新的Logo区域 -->
        <div class="new-logo-section">
          <div class="logo-container">
            <div class="logo-icon">
              <el-icon size="28"><Monitor /></el-icon>
            </div>
            <div class="logo-text" v-if="!sidebarCollapsed">
              <h2>AIOT</h2>
              <span>Admin System</span>
            </div>
          </div>
          <div class="logo-divider" v-if="!sidebarCollapsed"></div>
        </div>

        <!-- 新的导航菜单 -->
        <div class="new-navigation">
          <!-- 快速访问区域 -->
          <div class="nav-section">
            <div class="section-label" v-if="!sidebarCollapsed">快速访问</div>
            <div class="nav-items">
              <div 
                class="nav-item dashboard-item"
                :class="{ active: $route.path === '/dashboard' }"
                @click="handleNavItemClick({route: '/dashboard'}, $event)"
              >
                <div class="item-icon">
                  <el-icon size="20"><House /></el-icon>
                </div>
                <div class="item-content" v-if="!sidebarCollapsed">
                  <span class="item-title">仪表盘</span>
                  <span class="item-desc">系统概览</span>
                </div>
                <div class="item-indicator"></div>
              </div>
            </div>
          </div>

          <!-- 产品管理区域 -->
          <div class="nav-section">
            <div class="section-label" v-if="!sidebarCollapsed">产品管理</div>
            <div class="nav-items">
              <div 
                class="nav-item"
                :class="{ active: $route.path === '/products' }"
                @click="handleNavItemClick({route: '/products'}, $event)"
              >
                <div class="item-icon">
                  <el-icon size="20"><Box /></el-icon>
                </div>
                <div class="item-content" v-if="!sidebarCollapsed">
                  <span class="item-title">产品管理</span>
                  <span class="item-desc">产品类型配置</span>
                </div>
                <div class="item-indicator"></div>
              </div>


            </div>
          </div>

          <!-- 设备管理区域 -->
          <div class="nav-section">
            <div class="section-label" v-if="!sidebarCollapsed">设备管理</div>
            <div class="nav-items">
              <div 
                class="nav-item"
                :class="{ active: $route.path === '/device-register' }"
                @click="handleNavItemClick({route: '/device-register'}, $event)"
              >
                <div class="item-icon register-icon">
                  <el-icon size="20"><Plus /></el-icon>
                </div>
                <div class="item-content" v-if="!sidebarCollapsed">
                  <span class="item-title">设备注册</span>
                  <span class="item-desc">添加新设备</span>
                </div>
                <div class="item-indicator"></div>
              </div>

              <div 
                class="nav-item"
                :class="{ active: $route.path === '/devices' }"
                @click="handleNavItemClick({route: '/devices'}, $event)"
              >
                <div class="item-icon">
                  <el-icon size="20"><List /></el-icon>
                </div>
                <div class="item-content" v-if="!sidebarCollapsed">
                  <span class="item-title">设备列表</span>
                  <span class="item-desc">管理所有设备</span>
                </div>
                <div class="item-indicator"></div>
              </div>

            </div>
          </div>

          <!-- 数据分析区域 (暂时隐藏) -->
          <!-- <div class="nav-section">
            <div class="section-label" v-if="!sidebarCollapsed">数据分析</div>
            <div class="nav-items">
              <div 
                class="nav-item"
                :class="{ active: $route.path === '/data-overview' }"
                @click="handleNavItemClick({route: '/data-overview'}, $event)"
              >
                <div class="item-icon">
                  <el-icon size="20"><TrendCharts /></el-icon>
                </div>
                <div class="item-content" v-if="!sidebarCollapsed">
                  <span class="item-title">数据概览</span>
                  <span class="item-desc">总体统计</span>
                </div>
                <div class="item-indicator"></div>
              </div>


            </div>
          </div> -->

          <!-- 系统管理区域 -->
          <div class="nav-section" v-if="canAccessUserManagement || canAccessSystemManagement">
            <div class="section-label" v-if="!sidebarCollapsed">系统管理</div>
            <div class="nav-items">
              <div 
                v-if="canAccessUserManagement"
                class="nav-item"
                :class="{ active: $route.path === '/users' }"
                @click="handleNavItemClick({route: '/users'}, $event)"
              >
                <div class="item-icon">
                  <el-icon size="20"><UserFilled /></el-icon>
                </div>
                <div class="item-content" v-if="!sidebarCollapsed">
                  <span class="item-title">用户管理</span>
                  <span class="item-desc">账户权限</span>
                </div>
                <div class="item-indicator"></div>
              </div>

              <div 
                v-if="canAccessSystemManagement"
                class="nav-item"
                :class="{ active: $route.path === '/system-config' }"
                @click="handleNavItemClick({route: '/system-config'}, $event)"
              >
                <div class="item-icon">
                  <el-icon size="20"><Setting /></el-icon>
                </div>
                <div class="item-content" v-if="!sidebarCollapsed">
                  <span class="item-title">系统配置</span>
                  <span class="item-desc">参数设置</span>
                </div>
                <div class="item-indicator"></div>
              </div>
            </div>
          </div>
        </div>


      </el-aside>
      
      <!-- 主内容区 -->
      <el-container>
        <!-- 顶部导航 -->
        <el-header class="header">
          <div class="header-left">
            <!-- 移动端菜单按钮 -->
            <button 
              class="mobile-menu-btn"
              @click="toggleMobileMenu"
              v-if="isMobile"
            >
              <el-icon size="20">
                <Menu />
              </el-icon>
            </button>
            
            <el-button 
              type="text" 
              class="sidebar-toggle"
              @click="toggleSidebar"
              v-if="!isMobile"
            >
              <el-icon size="20">
                <component :is="sidebarCollapsed ? 'Expand' : 'Fold'" />
              </el-icon>
            </el-button>
            <div class="page-title">
              <el-icon size="24" :color="pageIcon.color">
                <component :is="pageIcon.icon" />
              </el-icon>
              <h2>{{ pageTitle }}</h2>
            </div>
            <div class="breadcrumb" v-if="!isMobile">
              <span v-for="(item, index) in breadcrumbs" :key="index">
                {{ item }}
                <el-icon v-if="index < breadcrumbs.length - 1"><ArrowRight /></el-icon>
              </span>
            </div>
          </div>
          <div class="header-right">

            <el-dropdown @command="handleCommand" class="user-dropdown">
              <div class="user-info">
                <el-avatar :size="32" :src="userAvatar" class="user-avatar">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <div class="user-details" v-if="!isMobile">
                  <span class="user-name">{{ userStore.userInfo?.username || '用户' }}</span>
                  <span class="user-email">{{ userStore.userInfo?.email }}</span>
                </div>
                <el-icon class="dropdown-icon" v-if="!isMobile"><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">
                    <el-icon><User /></el-icon>
                    个人信息
                  </el-dropdown-item>
                  <el-dropdown-item command="account">
                    <el-icon><Setting /></el-icon>
                    账户设置
                  </el-dropdown-item>
                  <el-dropdown-item command="security">
                    <el-icon><Monitor /></el-icon>
                    安全设置
                  </el-dropdown-item>
                  <el-dropdown-item command="preferences">
                    <el-icon><TrendCharts /></el-icon>
                    偏好设置
                  </el-dropdown-item>
                  <el-dropdown-item divided command="about">
                    <el-icon><InfoFilled /></el-icon>
                    关于系统
                  </el-dropdown-item>
                  <el-dropdown-item command="help">
                    <el-icon><House /></el-icon>
                    帮助中心
                  </el-dropdown-item>
                  <el-dropdown-item command="logout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        
        <!-- 内容区域 -->
        <el-main class="main-content">
          <div class="content-wrapper">
            <router-view />
          </div>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  House, Monitor, User, ArrowRight, ArrowDown, Setting, SwitchButton,
  Fold, Expand, Menu, TrendCharts, UserFilled, Plus, List, Box, Collection,
  InfoFilled
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const sidebarCollapsed = ref(false)
const isMobileMenuOpen = ref(false)
const windowWidth = ref(window.innerWidth)
const userName = computed(() => userStore.userInfo?.username || '管理员')

// 计算属性
const isMobile = computed(() => windowWidth.value <= 768)

// 页面标题和图标映射
const pageConfig = {
  '/dashboard': { title: '仪表盘', icon: 'House', color: '#409EFF' },
  '/products': { title: '产品管理', icon: 'Box', color: '#409EFF' },
  '/device-batches': { title: '设备批次', icon: 'Collection', color: '#409EFF' },
  '/device-register': { title: '设备注册', icon: 'Plus', color: '#67C23A' },
  '/devices': { title: '设备列表', icon: 'List', color: '#409EFF' },
  '/device': { title: '设备详情', icon: 'Monitor', color: '#409EFF' },

  // '/data-overview': { title: '数据概览', icon: 'TrendCharts', color: '#67C23A' }, // 暂时隐藏
  '/users': { title: '用户列表', icon: 'UserFilled', color: '#E6A23C' },
  '/roles': { title: '角色管理', icon: 'UserFilled', color: '#E6A23C' },
  '/permissions': { title: '权限管理', icon: 'UserFilled', color: '#E6A23C' },
  '/system-config': { title: '系统配置', icon: 'Setting', color: '#909399' },
  '/system-logs': { title: '系统日志', icon: 'Setting', color: '#909399' },
  '/system-backup': { title: '数据备份', icon: 'Setting', color: '#909399' }
}

// 计算页面标题
const pageTitle = computed(() => {
  const path = route.path
  for (const [key, config] of Object.entries(pageConfig)) {
    if (path.startsWith(key)) {
      return config.title
    }
  }
  return '未知页面'
})

// 计算页面图标
const pageIcon = computed(() => {
  const path = route.path
  for (const [key, config] of Object.entries(pageConfig)) {
    if (path.startsWith(key)) {
      return { icon: config.icon, color: config.color }
    }
  }
  return { icon: 'House', color: '#409EFF' }
})

// 计算面包屑
const breadcrumbs = computed(() => {
  const path = route.path
  const crumbs = ['首页']
  
  if (path.startsWith('/dashboard')) {
    crumbs.push('仪表盘')
  } else if (path.startsWith('/device-register')) {
    crumbs.push('设备管理', '设备注册')
  } else if (path.startsWith('/devices')) {
    crumbs.push('设备管理', '设备列表')
  } else if (path.startsWith('/device-interactions')) {
    crumbs.push('设备管理', '交互日志')
  } else if (path.startsWith('/device-types')) {
    crumbs.push('设备管理', '设备类型')
  } else if (path.startsWith('/device-groups')) {
    crumbs.push('设备管理', '设备分组')
  } else if (path.startsWith('/device/')) {
    crumbs.push('设备管理', '设备详情')
  // } else if (path.startsWith('/data-overview')) {
  //   crumbs.push('数据分析', '数据概览')
  } else if (path.startsWith('/data-charts')) {
    crumbs.push('数据分析', '数据图表')
  } else if (path.startsWith('/data-reports')) {
    crumbs.push('数据分析', '数据报告')
  } else if (path.startsWith('/users')) {
    crumbs.push('用户管理', '用户列表')
  } else if (path.startsWith('/roles')) {
    crumbs.push('用户管理', '角色管理')
  } else if (path.startsWith('/permissions')) {
    crumbs.push('用户管理', '权限管理')
  } else if (path.startsWith('/system-config')) {
    crumbs.push('系统管理', '系统配置')
  } else if (path.startsWith('/system-logs')) {
    crumbs.push('系统管理', '系统日志')
  } else if (path.startsWith('/system-backup')) {
    crumbs.push('系统管理', '数据备份')
  }
  
  return crumbs
})

// 用户头像
const userAvatar = computed(() => {
  return `https://api.dicebear.com/7.x/avataaars/svg?seed=${userStore.userInfo?.username || 'user'}`
})

// 权限检查
const canAccessUserManagement = computed(() => userStore.isAdmin || userStore.isSuperUser)
const canAccessSystemManagement = computed(() => userStore.isSuperUser)

// 切换侧边栏
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  // 添加侧边栏切换动画效果
  animateSidebarToggle()
}

// 移动端菜单控制
const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
  // 添加移动端菜单动画
  if (isMobileMenuOpen.value) {
    animateMobileMenu()
  }
}

const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
}

// 处理菜单选择
const handleMenuSelect = () => {
  if (isMobile.value) {
    closeMobileMenu()
  }
}

// 处理导航项点击
const handleNavItemClick = (item, event) => {
  // 创建涟漪效果
  createRippleEffect(event.currentTarget, event)
  
  // 添加点击动画
  const element = event.currentTarget
  element.style.transform = 'scale(0.95)'
  setTimeout(() => {
    element.style.transform = 'scale(1)'
  }, 150)
  
  // 路由跳转
  router.push(item.route)
  if (isMobile.value) {
    closeMobileMenu()
  }
}

// 动画函数
const animateSidebarToggle = () => {
  nextTick(() => {
    const sidebar = document.querySelector('.new-sidebar')
    if (sidebar) {
      sidebar.style.transform = 'scale(0.98)'
      setTimeout(() => {
        sidebar.style.transform = 'scale(1)'
      }, 150)
    }
  })
}

const animateMobileMenu = () => {
  nextTick(() => {
    const navItems = document.querySelectorAll('.nav-item')
    navItems.forEach((item, index) => {
      item.style.opacity = '0'
      item.style.transform = 'translateX(-20px)'
      setTimeout(() => {
        item.style.transition = 'all 0.3s ease'
        item.style.opacity = '1'
        item.style.transform = 'translateX(0)'
      }, index * 50)
    })
  })
}

const createRippleEffect = (element, event) => {
  const ripple = document.createElement('div')
  const rect = element.getBoundingClientRect()
  const size = Math.max(rect.width, rect.height)
  const x = event.clientX - rect.left - size / 2
  const y = event.clientY - rect.top - size / 2
  
  ripple.style.cssText = `
    position: absolute;
    width: ${size}px;
    height: ${size}px;
    left: ${x}px;
    top: ${y}px;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.3) 0%, transparent 70%);
    border-radius: 50%;
    transform: scale(0);
    animation: ripple 0.6s ease-out;
    pointer-events: none;
    z-index: 1;
  `
  
  element.style.position = 'relative'
  element.appendChild(ripple)
  
  setTimeout(() => {
    ripple.remove()
  }, 600)
}

// 初始化动画
const initAnimations = () => {
  nextTick(() => {
    // 页面加载时的入场动画
    const navItems = document.querySelectorAll('.nav-item')
    navItems.forEach((item, index) => {
      item.style.opacity = '0'
      item.style.transform = 'translateY(20px)'
      setTimeout(() => {
        item.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)'
        item.style.opacity = '1'
        item.style.transform = 'translateY(0)'
      }, index * 100)
    })
    
    // Logo动画
    const logo = document.querySelector('.logo-container')
    if (logo) {
      logo.style.opacity = '0'
      logo.style.transform = 'scale(0.8)'
      setTimeout(() => {
        logo.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)'
        logo.style.opacity = '1'
        logo.style.transform = 'scale(1)'
      }, 200)
    }
  })
}



const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    userStore.logout()
    router.push('/login')
  })
}

// 处理用户下拉菜单命令
const handleCommand = (command) => {
  if (command === 'profile') {
    ElMessage.info('个人信息功能开发中...')
  } else if (command === 'account') {
    ElMessage.info('账户设置功能开发中...')
  } else if (command === 'security') {
    ElMessage.info('安全设置功能开发中...')
  } else if (command === 'preferences') {
    ElMessage.info('偏好设置功能开发中...')
  } else if (command === 'about') {
    const appTitle = import.meta.env.VITE_APP_TITLE || '物联网设备服务系统'
    const appVersion = import.meta.env.VITE_APP_VERSION || '1.0.0'
    ElMessageBox.alert(
      `<div style="text-align: center; padding: 20px;">
        <h3 style="margin: 0 0 10px 0; color: #409EFF;">${appTitle}</h3>
        <p style="margin: 0; color: #909399;">版本 ${appVersion}</p>
      </div>`,
      '关于系统',
      {
        confirmButtonText: '确定',
        dangerouslyUseHTMLString: true
      }
    )
  } else if (command === 'help') {
    ElMessage.info('帮助中心功能开发中...')
  } else if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      userStore.logout()
      router.push('/login')
    })
  }
}

// 窗口大小监听
const handleResize = () => {
  windowWidth.value = window.innerWidth
  // 移动端时自动折叠侧边栏
  if (isMobile.value) {
    sidebarCollapsed.value = true
    isMobileMenuOpen.value = false
  }
}

// 监听移动端状态变化
watch(isMobile, (newVal) => {
  if (newVal) {
    // 切换到移动端时折叠侧边栏
    sidebarCollapsed.value = true
  } else {
    // 切换到桌面端时关闭移动菜单
    isMobileMenuOpen.value = false
  }
})

// 监听路由变化更新页面信息
watch(route, () => {
  // 路由变化时关闭移动菜单
  if (isMobile.value) {
    isMobileMenuOpen.value = false
  }
}, { immediate: true })

// 生命周期钩子
onMounted(() => {
  handleResize() // 初始化屏幕尺寸检测
  window.addEventListener('resize', handleResize)
  initAnimations() // 初始化动画效果
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
/* 全新现代化设计样式 */
.main-layout {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* 全新侧边栏设计 - 现代玻璃态风格 */
.new-sidebar {
  background: linear-gradient(180deg, 
    rgba(15, 23, 42, 0.95) 0%, 
    rgba(30, 41, 59, 0.95) 50%, 
    rgba(51, 65, 85, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.05);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.new-sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 20%, rgba(59, 130, 246, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(147, 51, 234, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 40% 60%, rgba(16, 185, 129, 0.05) 0%, transparent 50%);
  pointer-events: none;
}

.new-sidebar.collapsed {
  width: 80px !important;
}

/* 新Logo区域设计 */
.new-logo-section {
  padding: 24px 20px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  position: relative;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  z-index: 2;
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 
    0 8px 32px rgba(59, 130, 246, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.logo-icon::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  animation: logoRotate 4s linear infinite;
}

@keyframes logoRotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 涟漪动画 */
@keyframes ripple {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  100% {
    transform: scale(4);
    opacity: 0;
  }
}

/* 脉冲动画 */
@keyframes pulse {
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7);
  }
  70% {
    transform: scale(1.05);
    box-shadow: 0 0 0 10px rgba(59, 130, 246, 0);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
  }
}

/* 浮动动画 */
@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-6px);
  }
}

/* 闪烁动画 */
@keyframes shimmer {
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
}

/* 弹跳动画 */
@keyframes bounce {
  0%, 20%, 53%, 80%, 100% {
    transform: translate3d(0, 0, 0);
  }
  40%, 43% {
    transform: translate3d(0, -8px, 0);
  }
  70% {
    transform: translate3d(0, -4px, 0);
  }
  90% {
    transform: translate3d(0, -2px, 0);
  }
}

.logo-icon .el-icon {
  color: #ffffff;
  position: relative;
  z-index: 1;
}

.logo-text h2 {
  margin: 0;
  color: #ffffff;
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, #ffffff 0%, #e2e8f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-text span {
  color: #94a3b8;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.logo-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, #3b82f6, transparent);
  margin-top: 16px;
  opacity: 0.6;
}



/* 新导航菜单设计 */
.new-navigation {
  flex: 1;
  padding: 24px 0;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.new-navigation::-webkit-scrollbar {
  display: none;
}

.nav-section {
  margin-bottom: 32px;
}

.section-label {
  color: #64748b;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  margin: 0 20px 12px 20px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(100, 116, 139, 0.2);
  position: relative;
}

.section-label::before {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 24px;
  height: 1px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
}

.nav-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 0 16px;
}

/* 导航项目设计 */
.nav-item {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  background: rgba(51, 65, 85, 0.3);
  border: 1px solid rgba(148, 163, 184, 0.1);
  backdrop-filter: blur(10px);
  margin-bottom: 4px;
}

.nav-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(59, 130, 246, 0.1) 0%, 
    rgba(147, 51, 234, 0.1) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.item-icon {
  width: 44px;
  height: 44px;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  transition: all 0.3s ease;
  position: relative;
  z-index: 2;
}

.item-icon .el-icon {
  color: #60a5fa;
  transition: all 0.3s ease;
}

.item-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  position: relative;
  z-index: 2;
}

.item-title {
  color: #e2e8f0;
  font-size: 0.95rem;
  font-weight: 600;
  transition: color 0.3s ease;
}

.item-desc {
  color: #94a3b8;
  font-size: 0.75rem;
  font-weight: 400;
  transition: color 0.3s ease;
}

.item-indicator {
  width: 4px;
  height: 24px;
  background: transparent;
  border-radius: 2px;
  transition: all 0.3s ease;
  position: relative;
  z-index: 2;
}

/* 悬停效果 */
.nav-item:hover {
  background: linear-gradient(135deg, 
    rgba(59, 130, 246, 0.2) 0%, 
    rgba(147, 51, 234, 0.2) 100%);
  border-color: rgba(59, 130, 246, 0.3);
  transform: translateX(8px) scale(1.02);
  box-shadow: 
    0 12px 40px rgba(59, 130, 246, 0.2),
    0 0 0 1px rgba(59, 130, 246, 0.1);
  animation: float 2s ease-in-out infinite;
}

.nav-item:hover::before {
  opacity: 1;
}

.nav-item:hover .item-icon {
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  transform: scale(1.1);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3);
}

.nav-item:hover .item-icon .el-icon {
  color: #ffffff;
  transform: scale(1.1);
}

.nav-item:hover .item-title {
  color: #ffffff;
}

.nav-item:hover .item-desc {
  color: #cbd5e1;
}

.nav-item:hover .item-indicator {
  background: linear-gradient(180deg, #3b82f6 0%, #8b5cf6 100%);
}

/* 激活状态 */
.nav-item.active {
  background: linear-gradient(135deg, 
    rgba(59, 130, 246, 0.25) 0%, 
    rgba(147, 51, 234, 0.25) 100%);
  border-color: rgba(59, 130, 246, 0.4);
  transform: translateX(6px);
  box-shadow: 
    0 16px 48px rgba(59, 130, 246, 0.25),
    0 0 0 1px rgba(59, 130, 246, 0.2);
  animation: pulse 2s infinite;
}

.nav-item.active::before {
  opacity: 1;
}

.nav-item.active .item-icon {
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
}

.nav-item.active .item-icon .el-icon {
  color: #ffffff;
}

.nav-item.active .item-title {
  color: #ffffff;
  font-weight: 700;
}

.nav-item.active .item-desc {
  color: #cbd5e1;
}

.nav-item.active .item-indicator {
  background: linear-gradient(180deg, #3b82f6 0%, #8b5cf6 100%);
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.6);
}

/* 特殊图标样式 */
.register-icon {
  background: rgba(16, 185, 129, 0.1) !important;
}

.register-icon .el-icon {
  color: #10b981 !important;
}

.nav-item:hover .register-icon,
.nav-item.active .register-icon {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
}



.dashboard-item .item-icon {
  background: rgba(6, 182, 212, 0.1) !important;
}

.dashboard-item .item-icon .el-icon {
  color: #06b6d4 !important;
}

.nav-item.dashboard-item:hover .item-icon,
.nav-item.dashboard-item.active .item-icon {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%) !important;
}



/* 折叠状态样式 */
.new-sidebar.collapsed .logo-text,
.new-sidebar.collapsed .section-label,
.new-sidebar.collapsed .item-content {
  display: none;
}

.new-sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 16px;
}

.new-sidebar.collapsed .item-icon {
  margin-right: 0;
}

.new-sidebar.collapsed .logo-container {
  justify-content: center;
}

/* 头部样式 */
.header {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  height: 64px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.sidebar-toggle {
  padding: 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.sidebar-toggle:hover {
  background: #f1f5f9;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-title h2 {
  margin: 0;
  color: #1e293b;
  font-size: 1.5rem;
  font-weight: 600;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748b;
  font-size: 0.9rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}



.user-dropdown {
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.user-info:hover {
  background: #f8fafc;
}

.user-avatar {
  border: 2px solid #e2e8f0;
}

.user-details {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.user-name {
  font-weight: 600;
  color: #1e293b;
  font-size: 0.9rem;
}

.user-email {
  color: #64748b;
  font-size: 0.8rem;
}

.dropdown-icon {
  color: #64748b;
  transition: transform 0.3s ease;
}

.user-info:hover .dropdown-icon {
  transform: rotate(180deg);
}

/* 主内容区域 */
.main-content {
  background: #f8fafc;
  padding: 24px;
  overflow-y: auto;
}

.content-wrapper {
  max-width: 1400px;
  margin: 0 auto;
}

/* 移动端遮罩层 */
.mobile-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(0, 0, 0, 0.7) 0%, 
    rgba(30, 41, 59, 0.8) 100%);
  backdrop-filter: blur(8px);
  z-index: 999;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
}

.mobile-overlay.show {
  opacity: 1;
  visibility: visible;
}

.mobile-menu-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border: 1px solid #e2e8f0;
  color: #475569;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.mobile-menu-btn:hover {
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  color: #ffffff;
  border-color: #60a5fa;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
  transform: scale(1.05);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .new-sidebar {
    width: 240px;
  }
  
  .new-sidebar.collapsed {
    width: 80px;
  }
  
  .nav-item {
    padding: 14px 16px;
  }
  
  .item-icon {
    width: 40px;
    height: 40px;
  }
  
  .main-content {
    padding: 20px;
  }
}

@media (max-width: 768px) {
  .new-sidebar {
    position: fixed;
    left: -280px;
    top: 0;
    height: 100vh;
    width: 280px !important;
    z-index: 1000;
    transition: left 0.3s ease;
  }
  
  .new-sidebar.mobile-open {
    left: 0;
  }
  
  .new-sidebar.collapsed {
    width: 280px !important;
  }
  
  .header {
    padding: 0 16px;
    height: 56px;
  }
  
  .mobile-menu-btn {
    display: flex !important;
  }
  
  .page-title h2 {
    font-size: 1.1rem;
  }
  
  .breadcrumb {
    display: none;
  }
  
  .main-content {
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .header {
    padding: 0 12px;
    height: 52px;
  }
  
  .page-title h2 {
    font-size: 1rem;
  }
  
  .user-details {
    display: none;
  }
  

  
  .user-avatar {
    width: 28px !important;
    height: 28px !important;
  }
  
  .main-content {
    padding: 12px;
  }
}

/* 过渡动画 */
.new-sidebar {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.main-content {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.mobile-overlay {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 滚动条样式 */
.new-navigation::-webkit-scrollbar {
  width: 4px;
}

.new-navigation::-webkit-scrollbar-track {
  background: transparent;
}

.new-navigation::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 2px;
}

.new-navigation::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}
</style>