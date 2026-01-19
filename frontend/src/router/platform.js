/**
 * 平台管理系统路由配置
 * 包含用户管理、系统配置、日志管理等平台级管理功能
 */
export default [
  {
    path: '/platform',
    component: () => import('@/layouts/PlatformLayout.vue'),
    meta: { requiresAuth: true, requiresPlatformAdmin: true },
    redirect: '/platform/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'PlatformDashboard',
        component: () => import('@device/views/Dashboard.vue'),
        meta: { title: '平台管理控制台' }
      },
      {
        path: 'users',
        name: 'PlatformUserManagement',
        component: () => import('@device/views/Users.vue'),
        meta: { title: '用户管理' }
      },
      {
        path: 'products',
        name: 'PlatformProductManagement',
        component: () => import('@device/views/Products.vue'),
        meta: { title: '产品管理' }
      },
      {
        path: 'platform-config',
        name: 'PlatformConfig',
        component: () => import('@device/views/PlatformConfig.vue'),
        meta: { title: '平台配置' }
      },
      {
        path: 'module-config',
        name: 'PlatformModuleConfig',
        component: () => import('@device/views/ModuleConfig.vue'),
        meta: { title: '模块配置' }
      },
      {
        path: 'server-config',
        name: 'PlatformServerConfig',
        component: () => import('@device/views/ServerConfig.vue'),
        meta: { title: '服务器信息配置' }
      }
      // 系统日志和数据概览暂时隐藏
      // {
      //   path: 'system-logs',
      //   name: 'PlatformSystemLogs',
      //   component: () => import('@device/views/SystemLogs.vue'),
      //   meta: { title: '系统日志' }
      // },
      // {
      //   path: 'data-overview',
      //   name: 'PlatformDataOverview',
      //   component: () => import('@device/views/DataOverview.vue'),
      //   meta: { title: '数据概览' }
      // }
    ]
  }
]
