/**
 * 统一的认证工具
 * 处理token存储、权限判断等
 * 
 * 安全原则：
 * - 只存储必要的 token
 * - 不在 localStorage 存储用户敏感信息
 * - 用户信息通过 API 实时获取并存储在内存（Pinia store）中
 */

/**
 * 获取访问令牌
 */
export function getToken() {
  return localStorage.getItem('access_token')
}

/**
 * 设置访问令牌
 */
export function setToken(token) {
  localStorage.setItem('access_token', token)
}

/**
 * 移除访问令牌
 */
export function removeToken() {
  localStorage.removeItem('access_token')
}

/**
 * 获取刷新令牌
 */
export function getRefreshToken() {
  return localStorage.getItem('refresh_token')
}

/**
 * 设置刷新令牌
 */
export function setRefreshToken(token) {
  localStorage.setItem('refresh_token', token)
}

/**
 * 清除所有认证信息
 */
export function clearAuth() {
  removeToken()
  localStorage.removeItem('refresh_token')
  // 注意：用户信息不再存储在 localStorage，由 Pinia store 管理
}

/**
 * 检查是否已登录
 */
export function isAuthenticated() {
  return !!getToken()
}
