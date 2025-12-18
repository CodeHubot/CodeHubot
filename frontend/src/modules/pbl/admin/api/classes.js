// 班级和小组管理相关API
import request from '@/utils/request'
import { handleApiError } from './config'

// ===== 班级管理 =====

/**
 * 获取班级列表
 */
export const getClassList = async (params = {}) => {
  try {
    const response = await request.get('admin/classes-groups/classes', { params })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 创建班级
 */
export const createClass = async (classData) => {
  try {
    const response = await request.post('admin/classes-groups/classes', null, {
      params: classData
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取班级学生列表
 */
export const getClassStudents = async (classId) => {
  try {
    const response = await request.get(`admin/classes-groups/classes/${classId}/students`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 批量添加学生到班级
 */
export const addStudentsToClass = async (classId, studentIds) => {
  try {
    const response = await request.post(
      `/admin/classes-groups/classes/${classId}/add-students`,
      studentIds
    )
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// ===== 小组管理 =====

/**
 * 获取小组列表
 */
export const getGroupList = async (params = {}) => {
  try {
    const response = await request.get('admin/classes-groups/groups', { params })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 创建小组
 */
export const createGroup = async (groupData) => {
  try {
    const response = await request.post('admin/classes-groups/groups', null, {
      params: groupData
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取小组成员列表
 */
export const getGroupMembers = async (groupId) => {
  try {
    const response = await request.get(`admin/classes-groups/groups/${groupId}/members`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取小组可添加的学生列表
 */
export const getAvailableStudentsForGroup = async (groupId, keyword = '') => {
  try {
    const params = keyword ? { keyword } : {}
    const response = await request.get(
      `/admin/classes-groups/groups/${groupId}/available-students`,
      { params }
    )
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 批量添加成员到小组
 */
export const addMembersToGroup = async (groupId, studentIds) => {
  try {
    const response = await request.post(
      `/admin/classes-groups/groups/${groupId}/add-members`,
      studentIds
    )
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 从小组移除成员
 */
export const removeMemberFromGroup = async (groupId, studentId) => {
  try {
    const response = await request.delete(
      `/admin/classes-groups/groups/${groupId}/members/${studentId}`
    )
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// ===== 班级教师管理 =====

/**
 * 获取班级教师列表
 */
export const getClassTeachers = async (classId) => {
  try {
    const response = await request.get(`admin/classes-groups/classes/${classId}/teachers`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 为班级分配教师
 */
export const assignTeacherToClass = async (classId, data) => {
  try {
    const response = await request.post(
      `/admin/classes-groups/classes/${classId}/teachers`,
      null,
      { params: data }
    )
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 从班级移除教师
 */
export const removeTeacherFromClass = async (classId, teacherId) => {
  try {
    const response = await request.delete(
      `/admin/classes-groups/classes/${classId}/teachers/${teacherId}`
    )
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// ===== 班级课程管理 =====

/**
 * 获取班级课程列表
 */
export const getClassCourses = async (classId) => {
  try {
    const response = await request.get(`admin/classes-groups/classes/${classId}/courses`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 为班级分配课程
 */
export const assignCourseToClass = async (classId, data) => {
  try {
    const response = await request.post(
      `/admin/classes-groups/classes/${classId}/courses`,
      null,
      { params: data }
    )
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 从班级移除课程
 */
export const removeCourseFromClass = async (classId, courseUuid, removeEnrollments = false) => {
  try {
    const response = await request.delete(
      `/admin/classes-groups/classes/${classId}/courses/${courseUuid}`,
      {
        params: { remove_student_enrollments: removeEnrollments }
      }
    )
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// ===== 班级学习进度 =====

/**
 * 获取班级学生课程学习进度
 */
export const getClassLearningProgress = async (classId, courseId = null) => {
  try {
    const params = courseId ? { course_id: courseId } : {}
    const response = await request.get(`admin/classes-groups/classes/${classId}/progress`, { params })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// ===== 导出别名(为了兼容不同的命名习惯) =====
export const addClassTeacher = assignTeacherToClass
export const removeClassTeacher = removeTeacherFromClass
export const assignClassCourse = assignCourseToClass
export const removeClassCourse = removeCourseFromClass
export const getClassProgress = getClassLearningProgress
