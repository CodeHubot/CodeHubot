/**
 * 渠道商API接口
 */
import request from '@/utils/request'

/**
 * 获取渠道商负责的所有学校列表
 */
export function getChannelSchools() {
  return request({
    url: '/pbl/channel/schools',
    method: 'get'
  })
}

/**
 * 获取学校详情
 */
export function getSchoolDetail(schoolId) {
  return request({
    url: `/pbl/channel/schools/${schoolId}`,
    method: 'get'
  })
}

/**
 * 获取学校的课程列表
 */
export function getSchoolCourses(schoolId) {
  return request({
    url: `/pbl/channel/schools/${schoolId}/courses`,
    method: 'get'
  })
}

/**
 * 获取课程详情
 */
export function getCourseDetail(courseUuid) {
  return request({
    url: `/pbl/channel/courses/${courseUuid}`,
    method: 'get'
  })
}

/**
 * 获取课程学生作业提交统计
 */
export function getCourseStudentSubmissions(courseUuid) {
  return request({
    url: `/pbl/channel/courses/${courseUuid}/student-submissions`,
    method: 'get'
  })
}

/**
 * 获取课程进度
 */
export function getCourseProgress(courseUuid) {
  return request({
    url: `/pbl/channel/courses/${courseUuid}/progress`,
    method: 'get'
  })
}

/**
 * 获取课程作业列表
 */
export function getCourseAssignments(courseUuid) {
  return request({
    url: `/pbl/channel/courses/${courseUuid}/assignments`,
    method: 'get'
  })
}
