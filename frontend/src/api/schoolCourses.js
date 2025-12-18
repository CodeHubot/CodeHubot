import request from '@/utils/request'

/**
 * 为学校分配课程
 * @param {Object} data - 课程分配数据
 * @returns {Promise}
 */
export const assignCourseToSchool = (data) => {
  return request({
    url: '/admin/school-courses/assign',
    method: 'post',
    data
  })
}

/**
 * 批量分配课程给学校
 * @param {Object} data - 批量分配数据
 * @returns {Promise}
 */
export const batchAssignCourses = (data) => {
  return request({
    url: '/admin/school-courses/batch-assign',
    method: 'post',
    data
  })
}

/**
 * 获取学校的课程列表
 * @param {number} schoolId - 学校ID
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export const getSchoolCourses = (schoolId, params = {}) => {
  return request({
    url: `/admin/school-courses/school/${schoolId}/courses`,
    method: 'get',
    params
  })
}

/**
 * 获取所有学校课程分配记录
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export const getAllSchoolCourses = (params = {}) => {
  return request({
    url: '/admin/school-courses/all',
    method: 'get',
    params
  })
}

/**
 * 获取课程已分配的学校列表
 * @param {number} courseId - 课程ID
 * @returns {Promise}
 */
export const getCourseSchools = (courseId) => {
  return request({
    url: `/admin/school-courses/course/${courseId}/schools`,
    method: 'get'
  })
}

/**
 * 更新学校课程配置
 * @param {string} uuid - 学校课程UUID
 * @param {Object} data - 更新数据
 * @returns {Promise}
 */
export const updateSchoolCourse = (uuid, data) => {
  return request({
    url: `/admin/school-courses/${uuid}`,
    method: 'put',
    data
  })
}

/**
 * 取消学校课程分配
 * @param {string} uuid - 学校课程UUID
 * @returns {Promise}
 */
export const removeSchoolCourse = (uuid) => {
  return request({
    url: `/admin/school-courses/${uuid}`,
    method: 'delete'
  })
}

/**
 * 获取可分配的课程列表（学校管理员视角）
 * @returns {Promise}
 */
export const getAvailableCourses = () => {
  return request({
    url: '/admin/school-courses/available',
    method: 'get'
  })
}

/**
 * 获取学校列表
 * @returns {Promise}
 */
export const getSchools = () => {
  return request({
    url: '/admin/schools/list',
    method: 'get'
  })
}
