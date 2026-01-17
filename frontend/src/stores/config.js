/**
 * 系统配置 Store
 * 管理系统级别的配置项，控制功能模块的显示和行为
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'

export const useConfigStore = defineStore('config', () => {
  // ==================== 状态 ====================
  const configs = ref({})
  const loading = ref(false)
  const loaded = ref(false)

  // ==================== 计算属性 ====================
  
  /**
   * 获取配置值（支持布尔类型转换）
   */
  const getConfig = computed(() => {
    return (key, defaultValue = null) => {
      const config = configs.value[key]
      if (!config) return defaultValue

      // 布尔类型转换
      if (config.config_type === 'boolean') {
        return config.config_value?.toLowerCase() === 'true'
      }

      // 整数类型转换
      if (config.config_type === 'integer') {
        return parseInt(config.config_value) || defaultValue
      }

      // JSON类型解析
      if (config.config_type === 'json') {
        try {
          return JSON.parse(config.config_value)
        } catch {
          return defaultValue
        }
      }

      // 字符串和文本类型
      return config.config_value || defaultValue
    }
  })

  // ==================== AI模块功能开关 ====================
  
  /**
   * AI模块 - 知识库功能是否启用
   * 默认值为false，确保配置加载失败时不显示未启用的功能
   */
  const aiKnowledgeBaseEnabled = computed(() => {
    return getConfig.value('ai_module_knowledge_base_enabled', false)
  })

  /**
   * AI模块 - 工作流功能是否启用
   * 默认值为false，确保配置加载失败时不显示未启用的功能
   */
  const aiWorkflowEnabled = computed(() => {
    return getConfig.value('ai_module_workflow_enabled', false)
  })

  /**
   * AI模块 - 智能体功能是否启用
   * 默认值为false，确保配置加载失败时不显示未启用的功能
   */
  const aiAgentEnabled = computed(() => {
    return getConfig.value('ai_module_agent_enabled', false)
  })

  /**
   * AI模块 - 提示词模板功能是否启用
   * 默认值为false，确保配置加载失败时不显示未启用的功能
   */
  const aiPromptTemplateEnabled = computed(() => {
    return getConfig.value('ai_module_prompt_template_enabled', false)
  })

  // ==================== 通用模块开关 ====================
  
  /**
   * 是否启用AI模块
   */
  const aiModuleEnabled = computed(() => {
    return getConfig.value('enable_ai_module', true)
  })

  /**
   * 是否启用设备管理模块
   */
  const deviceModuleEnabled = computed(() => {
    return getConfig.value('enable_device_module', true)
  })

  /**
   * 是否启用PBL模块
   */
  const pblModuleEnabled = computed(() => {
    return getConfig.value('enable_pbl_module', true)
  })

  /**
   * 是否启用用户注册
   */
  const userRegistrationEnabled = computed(() => {
    return getConfig.value('enable_user_registration', false)
  })

  // ==================== 方法 ====================
  
  /**
   * 加载公开配置
   */
  async function loadPublicConfigs() {
    if (loaded.value) return
    
    loading.value = true
    try {
      // 调用后端公开配置接口（无需认证）
      const response = await request.get('/system-config/configs/public')
      
      // 转换为键值对形式
      const configMap = {}
      if (response.data) {
        response.data.forEach(config => {
          configMap[config.config_key] = config
        })
      }
      
      configs.value = configMap
      loaded.value = true
      
      console.log('✅ 系统配置加载成功:', Object.keys(configMap).length, '个配置项')
    } catch (error) {
      console.error('❌ 加载系统配置失败:', error)
      // 加载失败时使用默认值，不影响系统运行
      loaded.value = true
    } finally {
      loading.value = false
    }
  }

  /**
   * 重新加载配置
   */
  async function reloadConfigs() {
    loaded.value = false
    await loadPublicConfigs()
  }

  /**
   * 清空配置
   */
  function clearConfigs() {
    configs.value = {}
    loaded.value = false
  }

  // ==================== 返回 ====================
  return {
    // 状态
    configs,
    loading,
    loaded,

    // 计算属性
    getConfig,
    
    // AI模块功能开关
    aiKnowledgeBaseEnabled,
    aiWorkflowEnabled,
    aiAgentEnabled,
    aiPromptTemplateEnabled,
    
    // 通用模块开关
    aiModuleEnabled,
    deviceModuleEnabled,
    pblModuleEnabled,
    userRegistrationEnabled,

    // 方法
    loadPublicConfigs,
    reloadConfigs,
    clearConfigs
  }
})

