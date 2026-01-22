/**
 * 团队管理API
 */
import request from '@/utils/request'

/**
 * 创建团队
 */
export const createTeam = (data) => {
  return request.post('teams', data)
}

/**
 * 获取团队列表
 */
export const getTeams = (params) => {
  return request.get('teams', { params })
}

/**
 * 获取团队详情
 */
export const getTeam = (teamId) => {
  return request.get(`teams/${teamId}`)
}

/**
 * 更新团队信息
 */
export const updateTeam = (teamId, data) => {
  return request.put(`teams/${teamId}`, data)
}

/**
 * 删除团队
 */
export const deleteTeam = (teamId) => {
  return request.delete(`teams/${teamId}`)
}

/**
 * 获取团队统计信息
 */
export const getTeamStatistics = (teamId) => {
  return request.get(`teams/${teamId}/statistics`)
}
