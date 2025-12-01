/**
 * 学校管理API
 */
import request from './request'

/**
 * 创建学校
 */
export const createSchool = (data) => {
  return request.post('/schools', data)
}

/**
 * 获取学校列表
 */
export const getSchools = (params) => {
  return request.get('/schools', { params })
}

/**
 * 获取学校详情
 */
export const getSchool = (schoolId) => {
  return request.get(`/schools/${schoolId}`)
}

/**
 * 更新学校信息
 */
export const updateSchool = (schoolId, data) => {
  return request.put(`/schools/${schoolId}`, data)
}

/**
 * 删除学校
 */
export const deleteSchool = (schoolId) => {
  return request.delete(`/schools/${schoolId}`)
}

/**
 * 获取学校统计信息
 */
export const getSchoolStatistics = (schoolId) => {
  return request.get(`/schools/${schoolId}/statistics`)
}

