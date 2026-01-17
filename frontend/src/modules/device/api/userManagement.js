/**
 * 用户管理模块API
 */
import request from '@/utils/request'

// ===== 学校管理员 =====

/**
 * 创建学校管理员
 */
export const createSchoolAdmin = (data) => {
  return request.post('user-management/school-admins', data)
}

// ===== 教师管理 =====

/**
 * 创建教师
 */
export const createTeacher = (data) => {
  return request.post('user-management/teachers', data)
}

/**
 * 获取教师列表
 */
export const getTeachers = (params) => {
  return request.get('user-management/teachers', { params })
}

// ===== 学生管理 =====

/**
 * 创建学生
 */
export const createStudent = (data) => {
  return request.post('user-management/students', data)
}

/**
 * 获取学生列表
 */
export const getStudents = (params) => {
  return request.get('user-management/students', { params })
}

/**
 * 获取用户列表（通用接口，支持角色和班级过滤）
 */
export const getUsers = async (params) => {
  const response = await request.get('user-management/users', { params })
  return response.data
}

// ===== 角色分配 =====

/**
 * 搜索独立用户（通过用户名或昵称）
 * @param {Object} params - 搜索参数
 * @param {string} params.keyword - 搜索关键词（用户名或真实姓名）
 */
export const searchIndividualUsers = (params) => {
  return request.get('user-management/search-individual-users', { params })
}

/**
 * 分配角色（独立用户→教师/学生）
 */
export const assignRole = (userUuid, data) => {
  return request.post(`user-management/users/${userUuid}/assign-role`, data)
}

// ===== 用户信息更新 =====

/**
 * 更新用户信息
 */
export const updateUser = (userUuid, data) => {
  return request.put(`user-management/users/${userUuid}`, data)
}

/**
 * 删除用户
 */
export const deleteUser = (userUuid) => {
  return request.delete(`user-management/users/${userUuid}`)
}

