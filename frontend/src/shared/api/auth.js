/**
 * 统一的认证API
 * 支持多种登录方式
 */
import request from '@/utils/request'

/**
 * 通用登录（用户名/邮箱 + 密码）
 */
export function login(data) {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

/**
 * PBL学生登录
 */
export function pblStudentLogin(data) {
  return request({
    url: '/v1/student/auth/login',
    method: 'post',
    data
  })
}

/**
 * PBL教师登录
 */
export function pblTeacherLogin(data) {
  return request({
    url: '/v1/teacher/auth/login',
    method: 'post',
    data
  })
}

/**
 * PBL管理员登录
 */
export function pblAdminLogin(data) {
  return request({
    url: '/v1/admin/auth/login',
    method: 'post',
    data
  })
}

/**
 * 退出登录
 */
export function logout() {
  return request({
    url: '/auth/logout',
    method: 'post'
  })
}

/**
 * 刷新Token
 */
export function refreshToken(refreshToken) {
  return request({
    url: '/auth/refresh',
    method: 'post',
    data: { refresh_token: refreshToken }
  })
}

/**
 * 获取当前用户信息
 */
export function getUserInfo() {
  return request({
    url: '/auth/user-info',
    method: 'get'
  })
}

/**
 * 修改密码
 */
export function changePassword(data) {
  return request({
    url: '/auth/change-password',
    method: 'post',
    data
  })
}

/**
 * 更新个人资料
 */
export function updateProfile(data) {
  return request({
    url: '/auth/profile',
    method: 'put',
    data
  })
}
