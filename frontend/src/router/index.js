import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../store/user'
import logger from '../utils/logger'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('../views/ForgotPassword.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('../components/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { requiresAuth: true }
      },
      // 产品管理
      {
        path: 'products',
        name: 'Products',
        component: () => import('../views/Products.vue'),
        meta: { requiresAuth: true }
      },

      // 设备管理
      {
        path: 'devices',
        name: 'Devices',
        component: () => import('../views/Devices.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'device-register',
        name: 'DeviceRegister',
        component: () => import('../views/DeviceRegister.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'device-status',
        name: 'DeviceStatus',
        component: () => import('../views/DeviceStatus.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'device-types',
        name: 'DeviceTypes',
        component: () => import('../views/Products.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'device-groups',
        name: 'DeviceGroups',
        component: () => import('../views/DeviceGroups.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'device/:uuid',
        name: 'DeviceDetail',
        component: () => import('../views/DeviceDetailNew.vue'),
        meta: { requiresAuth: true }
      },
      // 基于UUID的设备功能页面
      {
        path: 'device/:uuid/realtime',
        name: 'DeviceRealtimeData',
        component: () => import('../views/DeviceRealtimeData.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'device/:uuid/remote-control',
        name: 'DeviceRemoteControl',
        component: () => import('../views/DeviceRemoteControl.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'device/:uuid/detail',
        name: 'DeviceDetailInfo',
        component: () => import('../views/DeviceDetailInfo.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'device/:uuid/config',
        name: 'DeviceConfigPage',
        component: () => import('../views/DeviceConfigPage.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'device-interactions',
        name: 'DeviceInteractions',
        component: () => import('../views/DeviceInteractions.vue'),
        meta: { requiresAuth: true }
      },
      // 数据分析 (暂时禁用)
      // {
      //   path: 'data-overview',
      //   name: 'DataOverview',
      //   component: () => import('../views/DataOverview.vue'),
      //   meta: { requiresAuth: true }
      // },
      {
        path: 'data-charts',
        name: 'DataCharts',
        component: () => import('../views/DataCharts.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'data-reports',
        name: 'DataReports',
        component: () => import('../views/DataReports.vue'),
        meta: { requiresAuth: true }
      },
      // 智能体管理
      {
        path: 'agents',
        name: 'Agents',
        component: () => import('../views/Agents.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'agents/:id/edit',
        name: 'AgentEditor',
        component: () => import('../views/AgentEditor.vue'),
        meta: { requiresAuth: true }
      },
      // 插件管理
      {
        path: 'plugins',
        name: 'Plugins',
        component: () => import('../views/Plugins.vue'),
        meta: { requiresAuth: true }
      },
      // 用户管理
      {
        path: 'users',
        name: 'Users',
        component: () => import('../views/Users.vue'),
        meta: { requiresAuth: true, requiresRole: 'admin' }
      },
      {
        path: 'roles',
        name: 'Roles',
        component: () => import('../views/Roles.vue'),
        meta: { requiresAuth: true, requiresRole: 'admin' }
      },
      {
        path: 'permissions',
        name: 'Permissions',
        component: () => import('../views/Permissions.vue'),
        meta: { requiresAuth: true, requiresRole: 'admin' }
      },
      // 系统管理
      {
        path: 'system-config',
        name: 'SystemConfig',
        component: () => import('../views/SystemConfig.vue'),
        meta: { requiresAuth: true, requiresRole: 'admin' }
      },
      {
        path: 'system-logs',
        name: 'SystemLogs',
        component: () => import('../views/SystemLogs.vue'),
        meta: { requiresAuth: true, requiresRole: 'admin' }
      },
      {
        path: 'system-backup',
        name: 'SystemBackup',
        component: () => import('../views/SystemBackup.vue'),
        meta: { requiresAuth: true, requiresRole: 'admin' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  logger.route(from.path, to.path)
  logger.debug('路由守卫检查', {
    requiresAuth: to.meta.requiresAuth,
    isLoggedIn: userStore.isLoggedIn,
    requiredRole: to.meta.requiresRole,
    userRole: userStore.userInfo?.role
  })
  
  // 如果有token但没有用户信息，尝试获取用户信息
  if (userStore.token && !userStore.userInfo) {
    logger.debug('有token但没有用户信息，尝试获取')
    try {
      await userStore.fetchUserInfo()
      logger.debug('用户信息获取成功')
    } catch (error) {
      logger.warn('用户信息获取失败，执行登出:', error)
      userStore.logout()
    }
  }
  
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    logger.info('需要认证但用户未登录，重定向到登录页')
    next('/login')
  } else if ((to.name === 'Login' || to.name === 'Register') && userStore.isLoggedIn) {
    logger.debug('已登录用户访问登录/注册页，重定向到仪表盘')
    next('/dashboard')
  } else if (to.meta.requiresRole && userStore.userInfo?.role !== to.meta.requiresRole) {
    logger.warn('权限不足，重定向到仪表盘')
    next('/dashboard')
  } else {
    logger.debug('路由守卫检查通过')
    next()
  }
})

export default router
