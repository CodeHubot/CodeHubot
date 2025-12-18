// 选课管理相关API
import request from '@/utils/request'
import { handleApiError } from './config'

// ===== 学生端选课 =====

/**
 * 学生选课
 */
export const enrollCourse = async (courseId) => {
  try {
    const response = await request.post(`student/enrollments/enroll/${courseId}`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 学生退课
 */
export const unenrollCourse = async (courseId) => {
  try {
    const response = await request.delete(`student/enrollments/unenroll/${courseId}`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取我的选课列表
 */
export const getMyEnrollments = async () => {
  try {
    const response = await request.get('student/enrollments/my-enrollments')
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// ===== 管理端选课管理 =====

/**
 * 获取课程的选课学生列表
 */
export const getCourseStudents = async (courseId) => {
  try {
    const response = await request.get(`admin/enrollments/course/${courseId}/students`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 批量为学生选课
 */
export const batchEnrollStudents = async (courseId, studentIds) => {
  try {
    const response = await request.post(
      `/admin/enrollments/course/${courseId}/batch-enroll`,
      studentIds
    )
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}
