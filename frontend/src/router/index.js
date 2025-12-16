import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../store/user'
import logger from '../utils/logger'

const routes = [
  {
    path: '/',
    redirect: '/agents'
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
        path: 'device-pbl-authorization',
        name: 'DevicePBLAuthorization',
        component: () => import('../views/DevicePBLAuthorization.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'device-pbl-authorization-management',
        name: 'DevicePBLAuthorizationManagement',
        component: () => import('../views/DevicePBLAuthorizationManagement.vue'),
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
        path: 'agents/:uuid/edit',
        name: 'AgentEditor',
        component: () => import('../views/AgentEditor.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'agents/:uuid/chat',
        name: 'Chat',
        component: () => import('../views/Chat.vue'),
        meta: { requiresAuth: true }
      },
      // 知识库管理
      {
        path: 'knowledge-bases',
        name: 'KnowledgeBases',
        component: () => import('../views/KnowledgeBaseManagement.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'knowledge-bases/:uuid',
        name: 'KnowledgeBaseDetail',
        component: () => import('../views/KnowledgeBaseDetail.vue'),
        meta: { requiresAuth: true }
      },
      // 插件管理
      {
        path: 'plugins',
        name: 'Plugins',
        component: () => import('../views/Plugins.vue'),
        meta: { requiresAuth: true }
      },
      // 工作流管理
      {
        path: 'workflows',
        name: 'Workflows',
        component: () => import('../views/Workflows.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'workflows/editor/:uuid?',
        name: 'WorkflowEditor',
        component: () => import('../views/WorkflowEditor.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'plugins/:uuid/view',
        name: 'PluginViewer',
        component: () => import('../views/PluginViewer.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'plugins/:uuid/edit',
        name: 'PluginEditor',
        component: () => import('../views/PluginEditor.vue'),
        meta: { requiresAuth: true }
      },
      // 模型配置
      {
        path: 'llm-models',
        name: 'LLMModels',
        component: () => import('../views/LLMModels.vue'),
        meta: { requiresAuth: true, requiresRole: 'admin' }
      },
      // 个人信息
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/Profile.vue'),
        meta: { requiresAuth: true }
      },
      // 学校管理（平台管理员）
      {
        path: 'schools',
        name: 'Schools',
        component: () => import('../views/SchoolManagement.vue'),
        meta: { requiresAuth: true, requiresRole: 'platform_admin' }
      },
      // 课程管理（学校管理员/教师）
      {
        path: 'courses',
        name: 'Courses',
        component: () => import('../views/CourseManagement.vue'),
        meta: { requiresAuth: true }
      },
      // 课程学生管理（学校管理员/教师）
      {
        path: 'courses/:courseUuid/students',
        name: 'CourseStudents',
        component: () => import('../views/CourseStudentManagement.vue'),
        meta: { requiresAuth: true }
      },
      // 课程教师管理（学校管理员）
      {
        path: 'courses/:courseUuid/teachers',
        name: 'CourseTeachers',
        component: () => import('../views/CourseTeacherManagement.vue'),
        meta: { requiresAuth: true, requiresRole: 'school_admin' }
      },
      // 课程分组管理（学校管理员/教师）
      {
        path: 'courses/:courseUuid/groups',
        name: 'CourseGroups',
        component: () => import('../views/CourseGroupManagement.vue'),
        meta: { requiresAuth: true }
      },
      // 设备分组管理（学校管理员）
      {
        path: 'device-groups',
        name: 'DeviceGroups',
        component: () => import('../views/DeviceGroupManagement.vue'),
        meta: { requiresAuth: true, requiresRole: 'school_admin' }
      },
      // 教师管理（学校管理员）
      {
        path: 'teachers',
        name: 'Teachers',
        component: () => import('../views/TeacherManagement.vue'),
        meta: { requiresAuth: true, requiresRole: 'school_admin' }
      },
      // 学生管理（学校管理员/教师）
      {
        path: 'students',
        name: 'Students',
        component: () => import('../views/StudentManagement.vue'),
        meta: { requiresAuth: true }
      },
      // 分组管理（学校管理员/教师）- 课程分组
      {
        path: 'groups',
        name: 'Groups',
        component: () => import('../views/CourseGroupManagement.vue'),
        meta: { requiresAuth: true }
      },
      // 用户管理（旧的，保留兼容）
      {
        path: 'users',
        name: 'Users',
        component: () => import('../views/Users.vue'),
        meta: { requiresAuth: true, requiresRole: 'platform_admin' }
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
  routes,
  // 路由切换时的滚动行为
  scrollBehavior(to, from, savedPosition) {
    // 如果有保存的位置（浏览器前进/后退），使用保存的位置
    if (savedPosition) {
      return savedPosition
    }
    // 否则滚动到页面顶部
    return { top: 0, behavior: 'smooth' }
  }
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
  
  // 需要认证的路由
  if (to.meta.requiresAuth) {
    // 检查是否已登录（有有效的 token 和用户信息）
    if (userStore.isLoggedIn) {
      // 已登录，检查权限
      if (to.meta.requiresRole) {
        const userRole = userStore.userInfo?.role
        const requiredRole = to.meta.requiresRole
        
        // 平台管理员可以访问所有页面
        if (userRole !== 'platform_admin' && userRole !== requiredRole) {
          // 特殊处理：学生管理页面，学校管理员和教师都可以访问
          if (to.path === '/students' && (userRole === 'school_admin' || userRole === 'teacher')) {
            // 允许访问
          } else {
            logger.warn('权限不足，重定向到首页')
            next('/agents')
            return
          }
        }
      }
      logger.debug('已登录，路由守卫检查通过')
      next()
      return
    }
    
    // 未登录，但有 token（可能没有用户信息）
    if (userStore.token && !userStore.userInfo) {
      logger.debug('有token但没有用户信息，尝试获取')
      try {
        await userStore.fetchUserInfo()
        logger.debug('用户信息获取成功')
        // 获取成功后，检查权限
        if (to.meta.requiresRole) {
          const userRole = userStore.userInfo?.role
          const requiredRole = to.meta.requiresRole
          
          // 平台管理员可以访问所有页面
          if (userRole !== 'platform_admin' && userRole !== requiredRole) {
            // 特殊处理：学生管理页面，学校管理员和教师都可以访问
            if (to.path === '/students' && (userRole === 'school_admin' || userRole === 'teacher')) {
              // 允许访问
            } else {
              logger.warn('权限不足，重定向到首页')
              next('/agents')
              return
            }
          }
        }
        next()
        return
      } catch (error) {
        logger.warn('用户信息获取失败:', error)
        // 继续尝试使用 refreshToken
      }
    }
    
    // 未登录，但有有效的 refreshToken，尝试刷新
    if (userStore.refreshToken && !userStore.isRefreshTokenExpired) {
      logger.info('用户未登录但有有效的 refreshToken，尝试刷新 token')
      try {
        const newToken = await userStore.refreshAccessToken()
        if (newToken) {
          logger.info('✅ Token 刷新成功，尝试获取用户信息')
          // 刷新成功后，尝试获取用户信息
          try {
            await userStore.fetchUserInfo()
            logger.info('✅ 用户信息获取成功，继续访问目标页面')
            // 检查权限
            if (to.meta.requiresRole) {
              const userRole = userStore.userInfo?.role
              const requiredRole = to.meta.requiresRole
              
              // 平台管理员可以访问所有页面
              if (userRole !== 'platform_admin' && userRole !== requiredRole) {
                // 特殊处理：学生管理页面，学校管理员和教师都可以访问
                if (to.path === '/students' && (userRole === 'school_admin' || userRole === 'teacher')) {
                  // 允许访问
                } else {
                  logger.warn('权限不足，重定向到首页')
                  next('/agents')
                  return
                }
              }
            }
            next() // 继续访问目标页面
            return
          } catch (error) {
            logger.warn('获取用户信息失败:', error)
          }
        }
      } catch (error) {
        logger.error('Token 刷新失败:', error)
      }
    }
    
    // 所有尝试都失败，跳转到登录页
    logger.info('需要认证但用户未登录，重定向到登录页')
    next('/login')
    return
  }
  
  // 已登录用户访问登录/注册页，重定向到仪表盘
  if ((to.name === 'Login' || to.name === 'Register') && userStore.isLoggedIn) {
    logger.debug('已登录用户访问登录/注册页，重定向到首页')
    next('/agents')
    return
  }
  
  // 不需要认证的路由，直接通过
    logger.debug('路由守卫检查通过')
    next()
})

export default router
