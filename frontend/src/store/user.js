import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, register, resetPassword, getUserInfo, refreshToken as refreshTokenApi } from '../api/auth'
import { ElMessage } from 'element-plus'
import logger from '../utils/logger'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const refreshToken = ref(localStorage.getItem('refreshToken') || '')
  const tokenExpiry = ref(localStorage.getItem('tokenExpiry') || '')
  const userInfo = ref(null)
  const isRefreshing = ref(false) // 标记是否正在刷新token
  
  // 验证token格式是否有效
  const isValidTokenFormat = (token) => {
    if (!token) return false
    
    // JWT格式检查：必须是三部分，用.分隔
    const parts = token.split('.')
    if (parts.length !== 3) {
      logger.warn('Token格式无效：不是标准JWT格式')
      return false
    }
    
    // 尝试解析payload
    try {
      const payload = JSON.parse(atob(parts[1]))
      // 检查必要字段
      if (!payload.exp || !payload.sub) {
        logger.warn('Token格式无效：缺少必要字段')
        return false
      }
      return true
    } catch (error) {
      logger.error('Token格式无效：解析失败', error)
      return false
    }
  }
  
  // 解析JWT token获取过期时间
  const parseTokenExpiry = (token) => {
    try {
      if (!token) return null
      
      // 先检查格式
      if (!isValidTokenFormat(token)) {
        logger.error('Token格式无效，无法解析')
        return null
      }
      
      const payload = JSON.parse(atob(token.split('.')[1]))
      const expiry = payload.exp * 1000 // 转换为毫秒
      
      logger.debug('Token解析成功', {
        expiryDate: new Date(expiry).toLocaleString(),
        timeUntilExpiry: Math.floor((expiry - Date.now()) / 1000) + '秒'
      })
      
      return expiry
    } catch (error) {
      logger.error('解析token失败:', error)
      return null
    }
  }
  
  // 初始化时验证token
  const initializeAuth = () => {
    if (token.value) {
      const expiry = parseTokenExpiry(token.value)
      if (!expiry || new Date().getTime() > expiry) {
        // Token已过期，清除本地存储
        token.value = ''
        tokenExpiry.value = ''
        localStorage.removeItem('token')
        localStorage.removeItem('tokenExpiry')
      } else {
        // Token有效，更新过期时间
        tokenExpiry.value = expiry.toString()
        localStorage.setItem('tokenExpiry', tokenExpiry.value)
      }
    }
  }
  
  const isLoggedIn = computed(() => {
    const hasToken = !!token.value
    const hasUser = !!userInfo.value
    const tokenNotExpired = !isTokenExpired.value
    const result = hasToken && hasUser && tokenNotExpired
    
    logger.debug('登录状态检查:', { hasToken, hasUser, tokenNotExpired, isLoggedIn: result })
    
    return result
  })
  
  // 用户角色相关计算属性
  const user = computed(() => userInfo.value)
  
  // 新角色系统
  const isPlatformAdmin = computed(() => userInfo.value?.role === 'platform_admin')
  const isSchoolAdmin = computed(() => userInfo.value?.role === 'school_admin')
  const isTeacher = computed(() => userInfo.value?.role === 'teacher')
  const isStudent = computed(() => userInfo.value?.role === 'student')
  const isIndividual = computed(() => userInfo.value?.role === 'individual')
  
  // 旧角色系统（兼容性）
  const isAdmin = computed(() => userInfo.value?.role === 'admin' || userInfo.value?.role === 'platform_admin')
  const isSuperUser = computed(() => userInfo.value?.is_superuser === true || userInfo.value?.role === 'platform_admin')

  // Token过期检查
  const isTokenExpired = computed(() => {
    if (!tokenExpiry.value) {
      logger.debug('Token过期检查: 无token过期时间')
      return true
    }
    const now = Date.now()
    const expired = now >= tokenExpiry.value
    
    if (expired) {
      logger.warn('Token已过期')
    }
    
    return expired
  })

  // 检查token是否即将过期（3分钟内，用于主动刷新）
  const isTokenExpiringSoon = computed(() => {
    if (!tokenExpiry.value) {
      return false
    }
    const threeMinutes = 3 * 60 * 1000 // 提前3分钟刷新
    const now = Date.now()
    const expiringSoon = now >= (tokenExpiry.value - threeMinutes)
    
    if (expiringSoon) {
      logger.warn('Token即将过期')
    }
    
    return expiringSoon
  })

  // 检查 refresh token 是否过期
  const isRefreshTokenExpired = computed(() => {
    if (!refreshToken.value) {
      return true
    }
    const expiry = parseTokenExpiry(refreshToken.value)
    if (!expiry) {
      return true
    }
    return Date.now() >= expiry
  })

  // 设置token过期时间（从JWT token中获取）
  const setTokenExpiry = () => {
    if (token.value) {
      const expiry = parseTokenExpiry(token.value)
      if (expiry) {
        tokenExpiry.value = expiry.toString()
        localStorage.setItem('tokenExpiry', tokenExpiry.value)
      }
    }
  }

  // 登录
  const loginUser = async (email, password) => {
    try {
      const response = await login(email, password)
      token.value = response.data.access_token
      refreshToken.value = response.data.refresh_token
      userInfo.value = response.data.user
      
      // 保存到localStorage
      localStorage.setItem('token', token.value)
      localStorage.setItem('refreshToken', refreshToken.value)
      
      setTokenExpiry() // 设置token过期时间
      
      logger.info('登录成功', {
        accessTokenExpiry: '15分钟',
        refreshTokenExpiry: '45分钟'
      })
      
      ElMessage.success('登录成功')
      return response
    } catch (error) {
      // 优先使用 message 字段，如果没有则使用 detail
      const errorMessage = error.response?.data?.message || error.response?.data?.detail || '登录失败'
      ElMessage.error(errorMessage)
      throw error
    }
  }

  // 刷新Access Token
  const refreshAccessToken = async () => {
    if (isRefreshing.value) {
      logger.debug('Token刷新正在进行中，跳过')
      return null
    }
    
    if (!refreshToken.value) {
      logger.warn('无refresh token，无法刷新')
      return null
    }
    
    // 检查refresh token格式
    if (!isValidTokenFormat(refreshToken.value)) {
      logger.error('Refresh token格式无效，清除并登出')
      logout('Refresh token格式无效')
      return null
    }
    
    // 检查refresh token是否过期
    if (isRefreshTokenExpired.value) {
      logger.error('Refresh token已过期，清除并登出')
      logout('Refresh token已过期')
      return null
    }
    
    try {
      isRefreshing.value = true
      logger.info('开始刷新access token')
      
      // 使用 axios 而不是 fetch，以便经过拦截器处理响应格式
      const response = await refreshTokenApi(refreshToken.value)
      
      // 处理标准响应格式 {code, message, data}
      const responseData = response.data || response
      
      // 更新tokens
      token.value = responseData.access_token
      refreshToken.value = responseData.refresh_token
      
      // 更新localStorage
      localStorage.setItem('token', token.value)
      localStorage.setItem('refreshToken', refreshToken.value)
      
      setTokenExpiry()
      
      logger.info('✅ Access token刷新成功')
      return responseData.access_token
    } catch (error) {
      logger.error('Token刷新失败:', error)
      // 刷新失败，清除认证信息
      logout('Token刷新失败')
      return null
    } finally {
      isRefreshing.value = false
    }
  }

  // 主动刷新 token（在即将过期时）
  const proactiveRefreshToken = async () => {
    if (isRefreshing.value) {
      return false
    }
    
    // 如果 token 即将过期且 refresh token 有效，主动刷新
    if (isTokenExpiringSoon.value && !isRefreshTokenExpired.value) {
      logger.info('Token即将过期，主动刷新')
      const newToken = await refreshAccessToken()
      return !!newToken
    }
    
    return false
  }

  // 注册
  const registerUser = async (email, username, password) => {
    try {
      const response = await register(email, username, password)
      ElMessage.success('注册成功，请登录')
      // 返回响应数据，而不是整个响应对象
      return response.data || response
    } catch (error) {
      // 优先使用 message 字段，如果没有则使用 detail
      const errorMessage = error.response?.data?.message || error.response?.data?.detail || '注册失败'
      ElMessage.error(errorMessage)
      throw error
    }
  }

  // 重置密码
  const resetUserPassword = async (email, password) => {
    try {
      const response = await resetPassword(email, password)
      ElMessage.success('密码重置成功，请登录')
      return response
    } catch (error) {
      // 优先使用 message 字段，如果没有则使用 detail
      const errorMessage = error.response?.data?.message || error.response?.data?.detail || '密码重置失败'
      ElMessage.error(errorMessage)
      throw error
    }
  }

  // 获取用户信息
  const fetchUserInfo = async () => {
    try {
      const response = await getUserInfo()
      userInfo.value = response.data
      logger.info('用户信息获取成功')
      return response
    } catch (error) {
      logger.error('获取用户信息失败:', error)
      throw error
    }
  }

  // 检查认证状态
  const checkAuth = async () => {
    logger.debug('检查认证状态', {
      hasToken: !!token.value,
      isExpired: isTokenExpired.value
    })
    
    if (token.value) {
      // 检查token是否过期
      if (isTokenExpired.value) {
        logger.warn('Token已过期，执行退出登录')
        ElMessage.warning('登录已过期，请重新登录')
        logout('Token过期')
        return false
      }
      
      // 检查token是否即将过期
      // 注释掉提示，因为系统会自动刷新token，不需要提醒用户
      // if (isTokenExpiringSoon.value) {
      //   ElMessage.info('登录即将过期，请注意保存工作')
      // }
      
      try {
        await fetchUserInfo()
        return true
      } catch (error) {
        logger.error('获取用户信息失败:', error)
        logout()
        return false
      }
    }
    return false
  }

  // 设置token（用于机构登录等场景）
  const setToken = (newToken) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
    setTokenExpiry()
  }

  // 设置refresh token
  const setRefreshToken = (newRefreshToken) => {
    refreshToken.value = newRefreshToken
    localStorage.setItem('refreshToken', newRefreshToken)
  }

  // 设置用户信息
  const setUser = (user) => {
    userInfo.value = user
    logger.info('用户信息已设置', { username: user.username, role: user.role })
  }

  // 退出登录
  const logout = (reason = '手动退出') => {
    logger.info('用户退出登录:', { reason })
    
    token.value = ''
    refreshToken.value = ''
    tokenExpiry.value = ''
    userInfo.value = null
    isRefreshing.value = false
    
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('tokenExpiry')
  }

  // 初始化认证状态
  initializeAuth()

  return {
    token,
    refreshToken,
    tokenExpiry,
    userInfo,
    user,
    isLoggedIn,
    // 新角色系统
    isPlatformAdmin,
    isSchoolAdmin,
    isTeacher,
    isStudent,
    isIndividual,
    // 旧角色系统（兼容）
    isAdmin,
    isSuperUser,
    // Token相关
    isTokenExpired,
    isTokenExpiringSoon,
    isRefreshTokenExpired,
    isRefreshing,
    proactiveRefreshToken,
    // 方法
    initializeAuth,
    loginUser,
    registerUser,
    resetUserPassword,
    refreshAccessToken,
    fetchUserInfo,
    checkAuth,
    setToken,
    setRefreshToken,
    setUser,
    logout
  }
})
