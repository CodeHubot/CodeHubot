// 学习进度相关API
import request from '@/utils/request'
import { handleApiError } from './config'

// ===== 学生端学习进度 =====

/**
 * 获取我的学习进度
 */
export const getMyProgress = async () => {
  try {
    const response = await request.get('student/learning-progress/my-progress')
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取课程学习进度
 */
export const getCourseProgress = async (courseId) => {
  try {
    const response = await request.get(`student/learning-progress/course/${courseId}`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 更新学习进度
 */
export const updateProgress = async (progressData) => {
  try {
    const response = await request.post('student/learning-progress/update', progressData)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// ===== 管理端学习进度查看 =====

/**
 * 获取学生学习进度列表
 */
export const getStudentProgressList = async (params = {}) => {
  try {
    const response = await request.get('admin/learning-progress/students', { params })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取课程的学生进度统计
 */
export const getCourseStudentProgress = async (courseId, params = {}) => {
  try {
    const response = await request.get(`admin/learning-progress/course/${courseId}/students`, { params })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取学生详细进度
 */
export const getStudentDetailProgress = async (studentId, courseId) => {
  try {
    const response = await request.get(`admin/learning-progress/student/${studentId}/course/${courseId}`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}
