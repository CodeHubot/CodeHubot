/**
 * Device系统路由配置
 */
export default [
  // 注册页面（公开访问）
  {
    path: '/register',
    name: 'Register',
    component: () => import('@device/views/Register.vue'),
    meta: { title: '用户注册', public: true }
  },
  {
    path: '/device',
    component: () => import('@/layouts/DeviceLayout.vue'),
    meta: { requiresAuth: true },
    redirect: '/device/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'DeviceDashboard',
        component: () => import('@device/views/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'device-register',
        name: 'DeviceRegister',
        component: () => import('@device/views/DeviceRegister.vue'),
        meta: { title: '设备注册' }
      },
      {
        path: 'devices',
        name: 'DeviceList',
        component: () => import('@device/views/Devices.vue'),
        meta: { title: '设备列表' }
      },
      {
        path: 'firmware-flasher',
        name: 'FirmwareFlasher',
        component: () => import('@device/views/FirmwareFlasher.vue'),
        meta: { title: '固件烧录' }
      },
      {
        path: 'serial-monitor',
        name: 'SerialMonitor',
        component: () => import('@device/views/SerialMonitor.vue'),
        meta: { title: '串口监视器' }
      },
      // 注意：更具体的路由必须放在更通用的路由之前
      {
        path: ':uuid/realtime',
        name: 'DeviceRealtime',
        component: () => import('@device/views/DeviceRealtimeData.vue'),
        meta: { title: '实时数据' }
      },
      {
        path: ':uuid/remote-control',
        name: 'DeviceRemoteControl',
        component: () => import('@device/views/DeviceRemoteControl.vue'),
        meta: { title: '远程控制' }
      },
      {
        path: ':uuid/config',
        name: 'DeviceConfigPage',
        component: () => import('@device/views/DeviceConfigPage.vue'),
        meta: { title: '设备配置' }
      },
      {
        path: ':uuid/detail',
        name: 'DeviceDetailByUUID',
        component: () => import('@device/views/DeviceDetailByUUID.vue'),
        meta: { title: '设备详情' }
      },
      // 产品管理已移至平台管理系统
      // {
      //   path: 'products',
      //   name: 'ProductList',
      //   component: () => import('@device/views/Products.vue'),
      //   meta: { 
      //     title: '产品管理',
      //     requiresPlatformAdmin: true 
      //   }
      // },
      // 设备分组暂时移除
      // {
      //   path: 'device-groups',
      //   name: 'DeviceGroupList',
      //   component: () => import('@device/views/DeviceGroups.vue'),
      //   meta: { title: '设备分组' }
      // },
      // PBL设备授权功能已删除
      // {
      //   path: 'device-pbl-authorization',
      //   name: 'DevicePBLAuthorization',
      //   component: () => import('@device/views/DevicePBLAuthorization.vue'),
      //   meta: { 
      //     title: '设备授权',
      //     requiresTeacherOrAdmin: true 
      //   }
      // },
      {
        path: 'firmware',
        name: 'FirmwareManagement',
        component: () => import('@device/views/DeviceConfig.vue'),
        meta: { 
          title: '固件管理',
          requiresPlatformAdmin: true 
        }
      },
      {
        path: 'platform-config',
        name: 'PlatformConfig',
        component: () => import('@device/views/PlatformConfig.vue'),
        meta: { title: '系统配置', requiresPlatformAdmin: true }
      },
      {
        path: 'module-config',
        name: 'ModuleConfig',
        component: () => import('@device/views/ModuleConfig.vue'),
        meta: { title: '模块配置', requiresPlatformAdmin: true }
      },
      {
        path: 'teams',
        name: 'TeamManagement',
        component: () => import('@device/views/TeamManagement.vue'),
        meta: { 
          title: '团队管理',
          requiresPlatformAdmin: true 
        }
      },
      {
        path: 'teachers',
        name: 'TeacherManagement',
        component: () => import('@device/views/TeacherManagement.vue'),
        meta: { 
          title: '教师管理',
          requiresTeacherOrAdmin: true 
        }
      },
      {
        path: 'students',
        name: 'StudentManagement',
        component: () => import('@device/views/StudentManagement.vue'),
        meta: { 
          title: '学生管理',
          requiresTeacherOrAdmin: true 
        }
      },
      {
        path: 'courses',
        name: 'CourseManagement',
        component: () => import('@device/views/CourseManagement.vue'),
        meta: { 
          title: '课程管理',
          requiresTeacherOrAdmin: true 
        }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: () => import('@device/views/Users.vue'),
        meta: { 
          title: '用户管理',
          requiresPlatformAdmin: true 
        }
      },
      {
        path: 'device-groups',
        name: 'DeviceGroupManagement',
        component: () => import('@device/views/DeviceGroups.vue'),
        meta: { 
          title: '设备分组',
          requiresTeacherOrAdmin: true 
        }
      },
      {
        path: 'courses/:courseUuid/teachers',
        name: 'CourseTeacherManagement',
        component: () => import('@device/views/CourseTeacherManagement.vue'),
        meta: { 
          title: '课程教师管理',
          requiresTeacherOrAdmin: true 
        }
      },
      {
        path: 'courses/:courseUuid/students',
        name: 'CourseStudentManagement',
        component: () => import('@device/views/CourseStudentManagement.vue'),
        meta: { 
          title: '课程学生管理',
          requiresTeacherOrAdmin: true 
        }
      },
      {
        path: 'courses/:courseUuid/groups',
        name: 'CourseGroupManagement',
        component: () => import('@device/views/CourseGroupManagement.vue'),
        meta: { 
          title: '课程分组管理',
          requiresTeacherOrAdmin: true 
        }
      },
      // AI 相关路由
      {
        path: 'agents',
        name: 'DeviceAgentList',
        component: () => import('@device/views/Agents.vue'),
        meta: { title: '智能体管理' }
      },
      {
        path: 'agents/:uuid/edit',
        name: 'DeviceAgentEdit',
        component: () => import('@device/views/AgentEditor.vue'),
        meta: { title: '编辑智能体' }
      },
      {
        path: 'agents/:uuid/chat',
        name: 'DeviceAgentChat',
        component: () => import('@device/views/Chat.vue'),
        meta: { title: '智能体对话' }
      },
      {
        path: 'plugins',
        name: 'DevicePluginList',
        component: () => import('@device/views/Plugins.vue'),
        meta: { title: '插件管理' }
      },
      {
        path: 'plugins/:uuid/edit',
        name: 'DevicePluginEdit',
        component: () => import('@device/views/PluginEditor.vue'),
        meta: { title: '编辑插件' }
      },
      {
        path: 'plugins/:uuid/view',
        name: 'DevicePluginView',
        component: () => import('@device/views/PluginViewer.vue'),
        meta: { title: '查看插件' }
      },
      {
        path: 'workflows',
        name: 'DeviceWorkflowList',
        component: () => import('@device/views/Workflows.vue'),
        meta: { title: '工作流管理' }
      },
      {
        path: 'workflows/editor',
        name: 'DeviceWorkflowEditor',
        component: () => import('@device/views/WorkflowEditor.vue'),
        meta: { title: '工作流编辑器' }
      },
      {
        path: 'workflows/editor/:uuid',
        name: 'DeviceWorkflowEditorWithId',
        component: () => import('@device/views/WorkflowEditor.vue'),
        meta: { title: '编辑工作流' }
      },
      {
        path: 'knowledge-bases',
        name: 'DeviceKnowledgeBaseList',
        component: () => import('@device/views/KnowledgeBaseManagement.vue'),
        meta: { title: '知识库管理' }
      },
      {
        path: 'knowledge-bases/:uuid',
        name: 'DeviceKnowledgeBaseDetail',
        component: () => import('@device/views/KnowledgeBaseDetail.vue'),
        meta: { title: '知识库详情' }
      },
      {
        path: 'llm-models',
        name: 'DeviceLLMModels',
        component: () => import('@device/views/LLMModels.vue'),
        meta: { title: '模型配置' }
      }
    ]
  }
]
