import request from '@/utils/request'

/**
 * 评价管理 API
 */

// 获取评价列表
export const getAssessments = (params) => {
  return request({
    url: '/pbl/assessments',
    method: 'get',
    params
  })
}

// 创建评价
export const createAssessment = (data) => {
  return request({
    url: '/pbl/assessments',
    method: 'post',
    data
  })
}

// 更新评价
export const updateAssessment = (uuid, data) => {
  return request({
    url: `/pbl/assessments/${uuid}`,
    method: 'put',
    data
  })
}

// 删除评价
export const deleteAssessment = (uuid) => {
  return request({
    url: `/pbl/assessments/${uuid}`,
    method: 'delete'
  })
}

// 获取评价详情
export const getAssessmentDetail = (uuid) => {
  return request({
    url: `/pbl/assessments/${uuid}`,
    method: 'get'
  })
}

// 获取评价模板列表
export const getAssessmentTemplates = (params) => {
  return request({
    url: '/pbl/assessment-templates',
    method: 'get',
    params
  })
}

// 创建评价模板
export const createAssessmentTemplate = (data) => {
  return request({
    url: '/pbl/assessment-templates',
    method: 'post',
    data
  })
}

// 更新评价模板
export const updateAssessmentTemplate = (uuid, data) => {
  return request({
    url: `/pbl/assessment-templates/${uuid}`,
    method: 'put',
    data
  })
}

// 删除评价模板
export const deleteAssessmentTemplate = (uuid) => {
  return request({
    url: `/pbl/assessment-templates/${uuid}`,
    method: 'delete'
  })
}

// 获取学生评价统计
export const getStudentAssessmentStats = (studentId) => {
  return request({
    url: `/pbl/students/${studentId}/assessment-stats`,
    method: 'get'
  })
}
