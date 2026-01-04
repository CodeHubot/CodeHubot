/**
 * 统一路由配置
 * 整合Device和PBL所有路由
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { usePlatformStore } from '@/stores/platform'
import { ElMessage } from 'element-plus'

// 导入路由模块
import deviceRoutes from './device'
import pblRoutes from './pbl'
import aiRoutes from './ai'

const routes = [
  // 登录页
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true }
  },
  
  // 根路径重定向到PBL平台
  {
    path: '/',
    redirect: () => {
      const authStore = useAuthStore()
      // 根据用户角色重定向到对应的PBL页面
      if (authStore.isStudent) return '/pbl/student/courses'
      if (authStore.isTeacher) return '/pbl/school/dashboard'
      if (authStore.isSchoolAdmin) return '/pbl/school/dashboard'
      if (authStore.isChannelPartner) return '/pbl/channel/schools'
      if (authStore.isAdmin || authStore.isChannelManager) return '/pbl/admin/schools'
      return '/pbl'
    },
    meta: { requiresAuth: true }
  },
  
  // 门户页（系统选择）- 保留但不作为默认页
  {
    path: '/portal',
    name: 'Portal',
    component: () => import('@/views/Portal.vue'),
    meta: { title: '系统门户', requiresAuth: true }
  },
  
  // Device系统路由
  ...deviceRoutes,
  
  // PBL系统路由
  ...pblRoutes,
  
  // AI系统路由
  ...aiRoutes,
  
  // 404页面
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 全局前置守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const platformStore = usePlatformStore()
  
  // 等待 authStore 初始化完成
  if (!authStore.isInitialized) {
    await authStore.init()
  }

  // 加载平台配置（仅加载一次）
  if (!platformStore.isLoaded) {
    await platformStore.loadConfig()
  }
  
  // 设置页面标题（使用平台名称）
  document.title = to.meta.title ? `${to.meta.title} - ${platformStore.platformName}` : platformStore.platformName
  
  // 公开页面直接放行
  if (to.meta.public) {
    // 检查是否有 token
    const hasToken = localStorage.getItem('access_token')
    
    // 如果有token且访问登录页，跳转到PBL平台
    if (to.path === '/login' && hasToken && authStore.isAuthenticated) {
      // 根据用户角色跳转到对应的PBL页面
      let targetPath = '/pbl'
      if (authStore.isStudent) {
        targetPath = '/pbl/student/courses'
      } else if (authStore.isTeacher || authStore.isSchoolAdmin) {
        targetPath = '/pbl/school/dashboard'
      } else if (authStore.isChannelPartner) {
        targetPath = '/pbl/channel/schools'
      } else if (authStore.isAdmin || authStore.isChannelManager) {
        targetPath = '/pbl/admin/schools'
      }
      next(targetPath)
      return
    }
    next()
    return
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
    return
  }
  
  // 检查角色权限
  if (to.meta.roles) {
    const userRole = authStore.userRole
    if (!userRole) {
      ElMessage.error('无法获取用户角色信息')
      next('/login')
      return
    }
    if (!to.meta.roles.includes(userRole)) {
      ElMessage.error('没有权限访问该页面')
      // 跳转到用户对应的默认页面
      if (authStore.isStudent) {
        next('/pbl/student/courses')
      } else if (authStore.isTeacher || authStore.isSchoolAdmin) {
        next('/pbl/school/dashboard')
      } else if (authStore.isChannelPartner) {
        next('/pbl/channel/schools')
      } else if (authStore.isAdmin || authStore.isChannelManager) {
        next('/pbl/admin/schools')
      } else {
        next('/pbl')
      }
      return
    }
  }
  
  // 检查管理员权限（admin/super_admin/platform_admin）
  if (to.meta.requiresAdmin) {
    if (!authStore.isAdmin) {
      ElMessage.error('只有管理员可以访问该页面')
      next('/pbl')
      return
    }
  }
  
  // 检查平台管理员权限
  if (to.meta.requiresPlatformAdmin) {
    const userRole = authStore.userInfo?.role
    if (userRole !== 'platform_admin') {
      ElMessage.error('只有平台管理员可以访问该页面')
      next('/pbl')
      return
    }
  }
  
  // 检查教师或管理员权限
  if (to.meta.requiresTeacherOrAdmin) {
    const userRole = authStore.userInfo?.role
    if (!['platform_admin', 'school_admin', 'teacher'].includes(userRole)) {
      ElMessage.error('只有教师或管理员可以访问该页面')
      next('/')
      return
    }
  }
  
  next()
})

// 全局后置钩子
router.afterEach((to, from) => {
  // 可以在这里添加页面访问统计等逻辑
})

export default router
