import request from '@/utils/request'

/**
 * 获取用户列表
 * @param {Object} params - 查询参数
 * @param {number} params.skip - 跳过的记录数
 * @param {number} params.limit - 返回的记录数
 * @param {string} params.username - 用户名筛选
 * @param {string} params.role - 角色筛选
 * @param {boolean} params.is_active - 状态筛选
 * @param {string} params.search - 搜索关键词
 */
export const getUserList = (params = {}) => {
  return request.get('users/list', { params })
}

/**
 * 创建用户
 * @param {Object} data - 用户数据
 * @param {string} data.email - 邮箱
 * @param {string} data.username - 用户名
 * @param {string} data.password - 密码
 * @param {string} data.role - 角色 (admin/user)
 */
export const createUser = (data) => {
  return request.post('users/', data)
}

/**
 * 更新用户信息
 * @param {number} userId - 用户ID
 * @param {Object} data - 更新数据
 * @param {string} data.username - 用户名
 * @param {boolean} data.is_active - 是否启用
 */
export const updateUser = (userId, data) => {
  return request.put(`users/${userId}`, data)
}

/**
 * 删除用户
 * @param {number} userId - 用户ID
 */
export const deleteUser = (userId) => {
  return request.delete(`users/${userId}`)
}

/**
 * 切换用户启用/禁用状态
 * @param {number} userId - 用户ID
 */
export const toggleUserStatus = (userId) => {
  return request.put(`users/${userId}/toggle-status`)
}

/**
 * 重置用户密码
 * @param {number} userId - 用户ID
 * @param {string} newPassword - 新密码
 */
export const resetUserPassword = (userId, newPassword) => {
  return request.post(`users/${userId}/reset-password`, null, {
    params: { new_password: newPassword }
  })
}

