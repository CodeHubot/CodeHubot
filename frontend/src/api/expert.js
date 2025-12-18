import request from '@/utils/request'
import { handleApiError } from './config'

/**
 * 专家管理 API
 */

// 获取专家列表
export const getExperts = async (params) => {
  try {
    const response = await request({
      url: '/pbl/experts',
      method: 'get',
      params
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// 获取专家详情
export const getExpertDetail = async (uuid) => {
  try {
    const response = await request({
      url: `/pbl/experts/${uuid}`,
      method: 'get'
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// 创建专家
export const createExpert = async (data) => {
  try {
    const response = await request({
      url: '/pbl/experts',
      method: 'post',
      data
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// 更新专家信息
export const updateExpert = async (uuid, data) => {
  try {
    const response = await request({
      url: `/pbl/experts/${uuid}`,
      method: 'put',
      data
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// 删除专家
export const deleteExpert = async (uuid) => {
  try {
    const response = await request({
      url: `/pbl/experts/${uuid}`,
      method: 'delete'
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// 邀请专家评审
export const inviteExpertReview = async (data) => {
  try {
    const response = await request({
      url: '/pbl/expert-reviews/invite',
      method: 'post',
      data
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// 获取专家评审列表
export const getExpertReviews = async (params) => {
  try {
    const response = await request({
      url: '/pbl/expert-reviews',
      method: 'get',
      params
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// 提交专家评审
export const submitExpertReview = async (data) => {
  try {
    const response = await request({
      url: '/pbl/expert-reviews',
      method: 'post',
      data
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}
