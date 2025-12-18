/**
 * PBL用户管理API
 */
import request from '@/utils/request'

/**
 * 获取用户列表
 * @param {Object} params - 查询参数
 * @param {string} params.role - 角色筛选 (teacher/student)
 * @param {number} params.school_id - 学校ID
 * @param {number} params.skip - 跳过数量
 * @param {number} params.limit - 每页数量
 */
export function getUserList(params) {
  return request({
    url: '/admin/users/list',
    method: 'get',
    params
  })
}

/**
 * 获取用户详情
 * @param {number} userId - 用户ID
 */
export function getUserDetail(userId) {
  return request({
    url: `/admin/users/${userId}`,
    method: 'get'
  })
}

/**
 * 创建用户
 * @param {Object} data - 用户数据
 */
export function createUser(data) {
  return request({
    url: '/admin/users',
    method: 'post',
    data
  })
}

/**
 * 更新用户信息
 * @param {number} userId - 用户ID
 * @param {Object} data - 用户数据
 */
export function updateUser(userId, data) {
  return request({
    url: `/admin/users/${userId}`,
    method: 'put',
    data
  })
}

/**
 * 删除用户（软删除）
 * @param {number} userId - 用户ID
 */
export function deleteUser(userId) {
  return request({
    url: `/admin/users/${userId}`,
    method: 'delete'
  })
}

/**
 * 启用/禁用用户
 * @param {number} userId - 用户ID
 */
export function toggleUserActive(userId) {
  return request({
    url: `/admin/users/${userId}/toggle-active`,
    method: 'patch'
  })
}

/**
 * 重置用户密码
 * @param {number} userId - 用户ID
 * @param {string} newPassword - 新密码
 */
export function resetUserPassword(userId, newPassword) {
  return request({
    url: `/admin/users/${userId}/reset-password`,
    method: 'post',
    data: { new_password: newPassword }
  })
}

/**
 * 批量导入学生
 * @param {File} file - CSV文件
 */
export function batchImportStudents(file) {
  const formData = new FormData()
  formData.append('file', file)
  
  return request({
    url: '/admin/users/batch-import/students',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 批量导入教师
 * @param {File} file - CSV文件
 */
export function batchImportTeachers(file) {
  const formData = new FormData()
  formData.append('file', file)
  
  return request({
    url: '/admin/users/batch-import/teachers',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取学校统计信息
 * @param {number} schoolId - 学校ID
 */
export function getSchoolStatistics(schoolId) {
  return request({
    url: `/schools/${schoolId}/statistics`,
    method: 'get'
  })
}
