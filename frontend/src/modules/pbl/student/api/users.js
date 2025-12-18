// 用户管理相关API
import request from '@/utils/request'
import { handleApiError } from './config'

/**
 * 获取用户列表
 */
export const getUserList = async (params = {}) => {
  try {
    const response = await request.get('admin/users/list', { params })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取用户详情
 */
export const getUserDetail = async (userId) => {
  try {
    const response = await request.get(`admin/users/${userId}`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 创建用户
 */
export const createUser = async (userData) => {
  try {
    const response = await request.post('admin/users', userData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 更新用户信息
 */
export const updateUser = async (userId, userData) => {
  try {
    const response = await request.put(`admin/users/${userId}`, userData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 删除用户（软删除）
 */
export const deleteUser = async (userId) => {
  try {
    const response = await request.delete(`admin/users/${userId}`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 启用/禁用用户
 */
export const toggleUserActive = async (userId) => {
  try {
    const response = await request.patch(`admin/users/${userId}/toggle-active`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 重置用户密码
 */
export const resetUserPassword = async (userId, newPassword) => {
  try {
    const response = await request.post(`admin/users/${userId}/reset-password`, null, {
      params: { new_password: newPassword }
    })
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 批量导入学生（CSV文件）
 */
export const batchImportStudents = async (schoolId, file) => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await request.post(
      `/admin/users/batch-import/students?school_id=${schoolId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 批量导入教师（CSV文件）
 */
export const batchImportTeachers = async (schoolId, file) => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await request.post(
      `/admin/users/batch-import/teachers?school_id=${schoolId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}
