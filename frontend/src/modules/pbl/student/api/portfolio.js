import request from '@/utils/request'

/**
 * 成长档案 API
 */

// 获取学生成长档案
export const getStudentPortfolio = (studentId, schoolYear) => {
  return request({
    url: `/pbl/students/${studentId}/portfolio`,
    method: 'get',
    params: { school_year: schoolYear }
  })
}

// 获取当前用户成长档案
export const getMyPortfolio = (schoolYear) => {
  return request({
    url: '/pbl/my-portfolio',
    method: 'get',
    params: { school_year: schoolYear }
  })
}

// 更新自我反思
export const updateSelfReflection = (portfolioUuid, reflection) => {
  return request({
    url: `/pbl/portfolios/${portfolioUuid}/reflection`,
    method: 'put',
    data: { content: reflection }
  })
}

// 更新教师评语
export const updateTeacherComments = (portfolioUuid, comments) => {
  return request({
    url: `/pbl/portfolios/${portfolioUuid}/teacher-comments`,
    method: 'put',
    data: { comments: comments }
  })
}

// 获取学生成就列表
export const getStudentAchievements = (studentId) => {
  return request({
    url: `/pbl/students/${studentId}/achievements`,
    method: 'get'
  })
}

// 获取成就列表
export const getAchievements = (params) => {
  return request({
    url: '/pbl/achievements',
    method: 'get',
    params
  })
}

// 导出成长档案
export const exportPortfolio = (portfolioUuid) => {
  return request({
    url: `/pbl/portfolios/${portfolioUuid}/export`,
    method: 'get',
    responseType: 'blob'
  })
}

// 管理员获取所有学生成长档案列表
export const getAdminPortfolios = (params) => {
  return request({
    url: '/pbl/admin/portfolios',
    method: 'get',
    params
  })
}
