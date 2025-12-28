/**
 * AI系统路由配置
 * 包含智能体、工作流、知识库、插件等AI功能
 */
export default [
  {
    path: '/ai',
    component: () => import('@/layouts/AILayout.vue'),
    meta: { requiresAuth: true },
    redirect: '/ai/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'AIDashboard',
        component: () => import('@ai/views/Dashboard.vue'),
        meta: { title: 'AI控制台' }
      },
      {
        path: 'agents',
        name: 'AIAgentList',
        component: () => import('@ai/views/Agents.vue'),
        meta: { title: '智能体管理' }
      },
      {
        path: 'agents/create',
        name: 'AIAgentCreate',
        component: () => import('@ai/views/AgentEditor.vue'),
        meta: { title: '创建智能体' }
      },
      {
        path: 'agents/:id/edit',
        name: 'AIAgentEdit',
        component: () => import('@ai/views/AgentEditor.vue'),
        meta: { title: '编辑智能体' }
      },
      {
        path: 'workflows',
        name: 'AIWorkflowList',
        component: () => import('@ai/views/Workflows.vue'),
        meta: { title: '工作流管理' }
      },
      {
        path: 'workflows/create',
        name: 'AIWorkflowCreate',
        component: () => import('@ai/views/WorkflowEditor.vue'),
        meta: { title: '创建工作流' }
      },
      {
        path: 'workflows/:id/edit',
        name: 'AIWorkflowEdit',
        component: () => import('@ai/views/WorkflowEditor.vue'),
        meta: { title: '编辑工作流' }
      },
      {
        path: 'knowledge-bases',
        name: 'AIKnowledgeBaseList',
        component: () => import('@ai/views/KnowledgeBaseManagement.vue'),
        meta: { title: '知识库管理' }
      },
      {
        path: 'knowledge-bases/:id',
        name: 'AIKnowledgeBaseDetail',
        component: () => import('@ai/views/KnowledgeBaseDetail.vue'),
        meta: { title: '知识库详情' }
      },
      {
        path: 'plugins',
        name: 'AIPluginList',
        component: () => import('@ai/views/Plugins.vue'),
        meta: { title: '插件管理' }
      },
      {
        path: 'plugins/create',
        name: 'AIPluginCreate',
        component: () => import('@ai/views/PluginEditor.vue'),
        meta: { title: '创建插件' }
      },
      {
        path: 'plugins/:id/edit',
        name: 'AIPluginEdit',
        component: () => import('@ai/views/PluginEditor.vue'),
        meta: { title: '编辑插件' }
      },
      {
        path: 'plugins/:id/view',
        name: 'AIPluginView',
        component: () => import('@ai/views/PluginViewer.vue'),
        meta: { title: '查看插件' }
      },
      {
        path: 'llm-models',
        name: 'AILLMModelList',
        component: () => import('@ai/views/LLMModels.vue'),
        meta: { title: 'LLM模型管理' }
      },
      {
        path: 'prompt-templates',
        name: 'AIPromptTemplateList',
        component: () => import('@ai/views/PromptTemplates.vue'),
        meta: { title: '提示词模板' }
      }
    ]
  }
]
