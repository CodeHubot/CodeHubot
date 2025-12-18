/**
 * 平台配置 Store
 * 用于管理平台名称、描述等全局配置
 */
import { defineStore } from 'pinia'
import { getPlatformConfig } from '@/modules/device/api/systemConfig'

export const usePlatformStore = defineStore('platform', {
  state: () => ({
    platformName: 'CodeHubot',
    platformDescription: '智能物联网管理平台',
    enableUserRegistration: false,
    userAgreement: '',
    privacyPolicy: '',
    isLoaded: false
  }),

  getters: {
    /**
     * 获取平台名称
     */
    name: (state) => state.platformName,

    /**
     * 获取平台描述
     */
    description: (state) => state.platformDescription,

    /**
     * 是否开启用户注册
     */
    canRegister: (state) => state.enableUserRegistration
  },

  actions: {
    /**
     * 加载平台配置
     */
    async loadConfig() {
      try {
        const response = await getPlatformConfig()
        const data = response.data

        this.platformName = data.platform_name || 'CodeHubot'
        this.platformDescription = data.platform_description || '智能物联网管理平台'
        this.enableUserRegistration = data.enable_user_registration || false
        this.userAgreement = data.user_agreement || ''
        this.privacyPolicy = data.privacy_policy || ''
        this.isLoaded = true

        // 更新页面标题
        document.title = this.platformName

        return data
      } catch (error) {
        console.error('加载平台配置失败:', error)
        // 使用默认值
        this.isLoaded = true
        return null
      }
    },

    /**
     * 更新平台配置
     */
    updateConfig(config) {
      if (config.platform_name !== undefined) {
        this.platformName = config.platform_name
      }
      if (config.platform_description !== undefined) {
        this.platformDescription = config.platform_description
      }
      if (config.enable_user_registration !== undefined) {
        this.enableUserRegistration = config.enable_user_registration
      }
      if (config.user_agreement !== undefined) {
        this.userAgreement = config.user_agreement
      }
      if (config.privacy_policy !== undefined) {
        this.privacyPolicy = config.privacy_policy
      }

      // 更新页面标题
      document.title = this.platformName
    },

    /**
     * 重置为默认配置
     */
    reset() {
      this.platformName = 'CodeHubot'
      this.platformDescription = '智能物联网管理平台'
      this.enableUserRegistration = false
      this.userAgreement = ''
      this.privacyPolicy = ''
      this.isLoaded = false
    }
  }
})
