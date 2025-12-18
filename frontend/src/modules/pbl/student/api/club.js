/**
 * 社团班课程系统API
 */
import request from '@/utils/request'

// ===== 班级管理 =====

/**
 * 获取班级列表
 */
export function getClubClasses(params) {
  return request({
    url: '/admin/club/classes',
    method: 'get',
    params
  })
}

/**
 * 创建班级
 */
export function createClubClass(data) {
  return request({
    url: '/admin/club/classes',
    method: 'post',
    data
  })
}

/**
 * 获取班级详情
 */
export function getClubClassDetail(classUuid) {
  return request({
    url: `/admin/club/classes/${classUuid}`,
    method: 'get'
  })
}

/**
 * 更新班级信息
 */
export function updateClubClass(classUuid, data) {
  return request({
    url: `/admin/club/classes/${classUuid}`,
    method: 'put',
    data
  })
}

/**
 * 删除班级
 */
export function deleteClubClass(classUuid) {
  return request({
    url: `/admin/club/classes/${classUuid}`,
    method: 'delete'
  })
}

// ===== 班级成员管理 =====

/**
 * 获取可添加到班级的学生列表
 */
export function getAvailableStudentsForClass(classUuid, params) {
  return request({
    url: `/admin/club/classes/${classUuid}/available-students`,
    method: 'get',
    params
  })
}

/**
 * 获取班级成员列表
 */
export function getClubClassMembers(classUuid) {
  return request({
    url: `/admin/club/classes/${classUuid}/members`,
    method: 'get'
  })
}

/**
 * 添加成员到班级
 */
export function addMembersToClubClass(classUuid, data) {
  return request({
    url: `/admin/club/classes/${classUuid}/members`,
    method: 'post',
    data
  })
}

/**
 * 从班级移除成员
 */
export function removeMemberFromClubClass(classUuid, studentId) {
  return request({
    url: `/admin/club/classes/${classUuid}/members/${studentId}`,
    method: 'delete'
  })
}

/**
 * 更新成员角色
 */
export function updateMemberRole(classUuid, studentId, data) {
  return request({
    url: `/admin/club/classes/${classUuid}/members/${studentId}/role`,
    method: 'put',
    data
  })
}

/**
 * 重置成员密码
 */
export function resetMemberPassword(classUuid, studentId) {
  return request({
    url: `/admin/club/classes/${classUuid}/members/${studentId}/reset-password`,
    method: 'post'
  })
}

// ===== 课程模板 =====

/**
 * 获取课程模板列表
 */
export function getCourseTemplates(params) {
  return request({
    url: '/admin/club/course-templates',
    method: 'get',
    params
  })
}

/**
 * 获取学校可用的课程模板列表
 */
export function getAvailableTemplates(params) {
  return request({
    url: '/admin/available-templates',
    method: 'get',
    params
  })
}

/**
 * 基于模板创建课程
 */
export function createCourseFromTemplate(data) {
  return request({
    url: '/admin/club/courses/create-from-template',
    method: 'post',
    data
  })
}

/**
 * 为课程的班级成员批量选课
 */
export function enrollClassMembersToCourse(courseId) {
  return request({
    url: `/admin/club/courses/${courseId}/enroll-class-members`,
    method: 'post'
  })
}

// ===== 学生端 =====

/**
 * 获取学生自己的班级列表
 */
export function getMyClubClasses() {
  return request({
    url: '/student/club/my-classes',
    method: 'get'
  })
}

/**
 * 获取学生自己的课程列表
 */
export function getMyClubCourses() {
  return request({
    url: '/student/club/my-courses',
    method: 'get'
  })
}

/**
 * 获取可加入的班级列表
 */
export function getAvailableClubClasses(params) {
  return request({
    url: '/student/club/available-classes',
    method: 'get',
    params
  })
}

/**
 * 加入班级
 */
export function joinClubClass(data) {
  return request({
    url: '/student/club/join-class',
    method: 'post',
    data
  })
}

/**
 * 获取班级详情（学生视角）
 */
export function getStudentClubClassDetail(classUuid) {
  return request({
    url: `/student/club/class/${classUuid}`,
    method: 'get'
  })
}

// ===== 小组管理 =====

/**
 * 获取小组列表
 */
export function getGroups(params) {
  return request({
    url: '/admin/classes-groups/groups',
    method: 'get',
    params
  })
}

/**
 * 创建小组
 */
export function createGroup(data) {
  return request({
    url: '/admin/classes-groups/groups',
    method: 'post',
    params: data
  })
}

/**
 * 删除小组
 */
export function deleteGroup(groupUuid) {
  return request({
    url: `/admin/classes-groups/groups/${groupUuid}`,
    method: 'delete'
  })
}

/**
 * 获取小组成员列表
 */
export function getGroupMembers(groupUuid) {
  return request({
    url: `/admin/classes-groups/groups/${groupUuid}/members`,
    method: 'get'
  })
}

/**
 * 获取小组可添加的学生列表（班级中未分组的学生）
 */
export function getAvailableStudentsForGroup(groupUuid, keyword = '') {
  return request({
    url: `/admin/classes-groups/groups/${groupUuid}/available-students`,
    method: 'get',
    params: keyword ? { keyword } : {}
  })
}

/**
 * 添加成员到小组
 */
export function addMembersToGroup(groupUuid, data) {
  return request({
    url: `/admin/classes-groups/groups/${groupUuid}/add-members`,
    method: 'post',
    data
  })
}

/**
 * 从小组移除成员
 */
export function removeMemberFromGroup(groupUuid, studentId) {
  return request({
    url: `/admin/classes-groups/groups/${groupUuid}/members/${studentId}`,
    method: 'delete'
  })
}
