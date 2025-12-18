/**
 * 认证状态管理
 * 使用Pinia管理全局的认证状态
 * 
 * 安全设计：
 * - Token 存储在 localStorage（必需，用于请求认证）
 * - 用户信息仅存储在内存中（Pinia state），页面刷新后重新获取
 * - 不在 localStorage 存储敏感用户信息
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { 
  getToken, setToken, removeToken,
  clearAuth
} from '@shared/utils/auth'
import { getUserInfo as fetchUserInfo } from '@shared/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // 状态 - 用户信息只存储在内存中
  const token = ref(null)
  const userInfo = ref(null)
  const loading = ref(false)
  const isInitialized = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  const userRole = computed(() => {
    const role = userInfo.value?.role || ''
    return role
  })
  const userName = computed(() => userInfo.value?.username || userInfo.value?.name || '')
  const userEmail = computed(() => userInfo.value?.email || '')
  
  // 角色判断 - 直接从userInfo读取，不依赖userRole computed
  const isStudent = computed(() => {
    const role = userInfo.value?.role
    return role === 'student'
  })
  const isTeacher = computed(() => {
    const role = userInfo.value?.role
    return role === 'teacher'
  })
  const isChannelPartner = computed(() => {
    const role = userInfo.value?.role
    return role === 'channel_partner'
  })
  const isChannelManager = computed(() => {
    const role = userInfo.value?.role
    return role === 'channel_manager'
  })
  const isAdmin = computed(() => {
    const role = userInfo.value?.role
    return role === 'admin' || role === 'super_admin' || role === 'platform_admin'
  })
  
  /**
   * 是否为学校管理员
   */
  const isSchoolAdmin = computed(() => {
    const role = userInfo.value?.role
    return role === 'school_admin'
  })

  /**
   * 设置登录信息
   */
  function setAuth(authData) {
    // request.js 的响应拦截器返回格式：
    // { success: true, data: {...}, message: '', originalResponse: {...} }
    // 
    // 登录接口返回的 data 结构：
    // { access_token, refresh_token, user: {...} }
    
    let data = authData.data || authData
    
    // 保存 access token（存储在 localStorage）
    const accessToken = data.access_token || data.token
    if (accessToken) {
      token.value = accessToken
      setToken(accessToken)
    }
    
    // 保存 refresh token（存储在 localStorage）
    const refreshToken = data.refresh_token
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken)
    }
    
    // 保存用户信息（仅存储在内存中，不存储到 localStorage）
    const user = data.user || data.userInfo || data.admin || data.student || data.teacher
    if (user) {
      userInfo.value = user
      // 注意：不再调用 storeUserInfo(user)，用户信息只保存在内存
    }
  }

  /**
   * 登录
   */
  async function login(loginFunc, loginData) {
    loading.value = true
    try {
      const response = await loginFunc(loginData)
      setAuth(response)
      return response
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  /**
   * 退出登录
   */
  function logout() {
    token.value = null
    userInfo.value = null
    clearAuth()
  }

  /**
   * 刷新用户信息
   */
  async function refreshUserInfo() {
    if (!token.value) return null
    
    try {
      const response = await fetchUserInfo()
      
      // request.js 的响应拦截器返回格式：
      // { success: true, data: {...}, message: '', originalResponse: {...} }
      // 
      // 后端 /auth/user-info 返回的是 UserResponse 对象，所以：
      // response.data 就是用户对象 { id, username, role, ... }
      
      const user = response.data
      
      if (user && user.id) {
        userInfo.value = user
        return userInfo.value
      } else {
        return null
      }
    } catch (error) {
      return null
    }
  }

  /**
   * 初始化（从localStorage恢复token，从后端获取用户信息）
   */
  async function init() {
    // 恢复 token（从 localStorage）
    const storedToken = getToken()
    token.value = storedToken
    
    // 如果有 token，从后端获取用户信息（不从 localStorage 读取）
    if (storedToken) {
      try {
        await refreshUserInfo()
      } catch (error) {
        // 如果获取失败，清除 token
        logout()
      }
    }
    
    isInitialized.value = true
  }

  return {
    // 状态
    token,
    userInfo,
    loading,
    isInitialized,
    // 计算属性
    isAuthenticated,
    userRole,
    userName,
    userEmail,
    isStudent,
    isTeacher,
    isSchoolAdmin,
    isChannelPartner,
    isChannelManager,
    isAdmin,
    // 方法
    setAuth,
    login,
    logout,
    refreshUserInfo,
    init
  }
})
