/**
 * Device模块的用户Store（兼容层）
 * 桥接到统一的auth store，保持向后兼容
 * 
 * 注意：返回的属性可以直接访问（不需要 .value）
 */
import { useAuthStore } from '@/stores/auth'
import { computed, reactive, toRefs } from 'vue'

export function useUserStore() {
  const authStore = useAuthStore()
  
  // 使用 reactive 包装，这样在模板和 script 中都可以直接访问属性
  const store = reactive({
    // 状态（直接代理 authStore）
    get token() { return authStore.token },
    get userInfo() { return authStore.userInfo },
    get user() { return authStore.userInfo }, // 兼容别名
    get loading() { return authStore.loading },
    
    // 计算属性
    get isAuthenticated() { return authStore.isAuthenticated },
    get userRole() { return authStore.userRole },
    get userName() { return authStore.userName },
    get userEmail() { return authStore.userEmail },
    get isStudent() { return authStore.isStudent },
    get isTeacher() { return authStore.isTeacher },
    get isAdmin() { return authStore.isAdmin },
    get isTeamAdmin() { return authStore.isTeamAdmin },
    get isPlatformAdmin() { return authStore.isAdmin }, // platform_admin 归入 isAdmin
    
    // Token过期检查
    get isTokenExpired() {
      if (!authStore.token) return true
      try {
        const payload = JSON.parse(atob(authStore.token.split('.')[1]))
        return Date.now() > payload.exp * 1000
      } catch {
        return true
      }
    },
    
    get isTokenExpiringSoon() {
      if (!authStore.token) return false
      try {
        const payload = JSON.parse(atob(authStore.token.split('.')[1]))
        return Date.now() > (payload.exp * 1000 - 5 * 60 * 1000) // 5分钟内
      } catch {
        return false
      }
    },
    
    get isRefreshTokenExpired() {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) return true
      try {
        const payload = JSON.parse(atob(refreshToken.split('.')[1]))
        return Date.now() > payload.exp * 1000
      } catch {
        return true
      }
    },
    
    // 方法
    setAuth: (authData) => authStore.setAuth(authData),
    
    setToken: (token) => {
      authStore.token = token
      localStorage.setItem('access_token', token)
    },
    
    setRefreshToken: (token) => {
      localStorage.setItem('refresh_token', token)
    },
    
    setUser: (user) => {
      authStore.userInfo = user
      localStorage.setItem('userInfo', JSON.stringify(user))
    },
    
    login: (loginFunc, loginData) => authStore.login(loginFunc, loginData),
    
    // 兼容旧的loginUser方法
    loginUser: async (email, password) => {
      const { login } = await import('@shared/api/auth')
      return authStore.login(login, { email, password })
    },
    
    logout: (reason) => {
      console.log('用户登出:', reason)
      authStore.logout()
    },
    
    refreshUserInfo: () => authStore.refreshUserInfo(),
    
    // Token刷新方法
    refreshAccessToken: async () => {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) return null
      
      try {
        const { refreshToken: refreshTokenApi } = await import('@shared/api/auth')
        const response = await refreshTokenApi(refreshToken)
        const newToken = response.access_token || response.data?.access_token
        
        if (newToken) {
          authStore.setAuth(response)
          return newToken
        }
        return null
      } catch (error) {
        console.error('刷新token失败:', error)
        return null
      }
    },
    
    proactiveRefreshToken: async () => {
      try {
        const newToken = await store.refreshAccessToken()
        return !!newToken
      } catch (error) {
        console.error('主动刷新token失败:', error)
        return false
      }
    },
    
    init: () => authStore.init()
  })
  
  return store
}
