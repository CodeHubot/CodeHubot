/**
 * 课程管理API
 * 提供课程、选课、教师-课程、分组管理的API接口
 */
import request from './request'

// ============================================================================
// 课程管理
// ============================================================================

/**
 * 获取课程列表
 */
export const getCourses = (params) => {
  return request({
    url: '/courses',
    method: 'get',
    params
  })
}

/**
 * 获取课程详情
 */
export const getCourse = (courseUuid) => {
  return request({
    url: `/courses/${courseUuid}`,
    method: 'get'
  })
}

/**
 * 创建课程
 */
export const createCourse = (data) => {
  return request({
    url: '/courses',
    method: 'post',
    data
  })
}

/**
 * 更新课程
 */
export const updateCourse = (courseUuid, data) => {
  return request({
    url: `/courses/${courseUuid}`,
    method: 'put',
    data
  })
}

/**
 * 删除课程
 */
export const deleteCourse = (courseUuid) => {
  return request({
    url: `/courses/${courseUuid}`,
    method: 'delete'
  })
}

/**
 * 获取课程统计信息
 */
export const getCourseStatistics = (courseUuid) => {
  return request({
    url: `/courses/${courseUuid}/statistics`,
    method: 'get'
  })
}

// ============================================================================
// 教师-课程管理
// ============================================================================

/**
 * 为课程添加教师
 */
export const addCourseTeacher = (courseUuid, data) => {
  return request({
    url: `/courses/${courseUuid}/teachers`,
    method: 'post',
    data
  })
}

/**
 * 批量添加教师
 */
export const batchAddCourseTeachers = (courseUuid, data) => {
  return request({
    url: `/courses/${courseUuid}/teachers/batch`,
    method: 'post',
    data
  })
}

/**
 * 获取课程教师列表
 */
export const getCourseTeachers = (courseUuid) => {
  return request({
    url: `/courses/${courseUuid}/teachers`,
    method: 'get'
  })
}

/**
 * 从课程移除教师
 */
export const removeCourseTeacher = (courseUuid, teacherId) => {
  return request({
    url: `/courses/${courseUuid}/teachers/${teacherId}`,
    method: 'delete'
  })
}

// ============================================================================
// 选课管理（核心功能）
// ============================================================================

/**
 * 学生选课
 */
export const enrollCourse = (courseUuid, data) => {
  return request({
    url: `/courses/${courseUuid}/enroll`,
    method: 'post',
    data
  })
}

/**
 * 批量选课
 */
export const enrollCourseBatch = (courseUuid, data) => {
  return request({
    url: `/courses/${courseUuid}/enroll/batch`,
    method: 'post',
    data
  })
}

/**
 * 获取课程的学生列表（选课记录）
 */
export const getCourseStudents = (courseUuid, params) => {
  return request({
    url: `/courses/${courseUuid}/students`,
    method: 'get',
    params
  })
}

/**
 * 添加学生到课程
 */
export const addStudentToCourse = (courseUuid, data) => {
  return request({
    url: `/courses/${courseUuid}/students`,
    method: 'post',
    data
  })
}

/**
 * 移除学生从课程
 */
export const removeStudentFromCourse = (courseUuid, studentId) => {
  return request({
    url: `/courses/${courseUuid}/students/${studentId}`,
    method: 'delete'
  })
}

/**
 * 更新选课状态或成绩
 */
export const updateEnrollment = (courseUuid, studentId, data) => {
  return request({
    url: `/courses/${courseUuid}/students/${studentId}`,
    method: 'put',
    data
  })
}

/**
 * 退课
 */
export const dropCourse = (courseUuid, studentId) => {
  return request({
    url: `/courses/${courseUuid}/students/${studentId}`,
    method: 'delete'
  })
}

// ============================================================================
// 课程分组管理
// ============================================================================

/**
 * 创建课程分组
 */
export const createCourseGroup = (courseUuid, data) => {
  return request({
    url: `/courses/${courseUuid}/groups`,
    method: 'post',
    data
  })
}

/**
 * 获取课程分组列表
 */
export const getCourseGroups = (courseUuid) => {
  return request({
    url: `/courses/${courseUuid}/groups`,
    method: 'get'
  })
}

/**
 * 更新课程分组
 */
export const updateCourseGroup = (courseUuid, groupUuid, data) => {
  return request({
    url: `/courses/${courseUuid}/groups/${groupUuid}`,
    method: 'put',
    data
  })
}

/**
 * 删除课程分组
 */
export const deleteCourseGroup = (courseUuid, groupUuid) => {
  return request({
    url: `/courses/${courseUuid}/groups/${groupUuid}`,
    method: 'delete'
  })
}

// ============================================================================
// 分组成员管理
// ============================================================================

/**
 * 添加分组成员
 */
export const addGroupMember = (courseUuid, groupUuid, data) => {
  return request({
    url: `/courses/${courseUuid}/groups/${groupUuid}/members`,
    method: 'post',
    data
  })
}

/**
 * 批量添加分组成员
 */
export const batchAddGroupMembers = (courseUuid, groupUuid, data) => {
  return request({
    url: `/courses/${courseUuid}/groups/${groupUuid}/members/batch`,
    method: 'post',
    data
  })
}

/**
 * 获取分组成员列表
 */
export const getGroupMembers = (courseUuid, groupUuid) => {
  return request({
    url: `/courses/${courseUuid}/groups/${groupUuid}/members`,
    method: 'get'
  })
}

/**
 * 从分组移除成员
 */
export const removeGroupMember = (courseUuid, groupUuid, studentId) => {
  return request({
    url: `/courses/${courseUuid}/groups/${groupUuid}/members/${studentId}`,
    method: 'delete'
  })
}

/**
 * 设置分组组长
 */
export const setGroupLeader = (courseUuid, groupUuid, studentId) => {
  return request({
    url: `/courses/${courseUuid}/groups/${groupUuid}/leader/${studentId}`,
    method: 'put'
  })
}

