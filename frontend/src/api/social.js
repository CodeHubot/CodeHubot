import request from '@/utils/request'
import { handleApiError } from './config'

/**
 * 社会实践活动 API
 */

// 获取社会实践活动列表
export const getSocialActivities = async (params) => {
  try {
    const response = await request({
      url: '/pbl/social-activities',
      method: 'get',
      params
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// 获取活动详情
export const getSocialActivityDetail = async (uuid) => {
  try {
    const response = await request({
      url: `/pbl/social-activities/${uuid}`,
      method: 'get'
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// 创建活动
export const createSocialActivity = async (data) => {
  try {
    const response = await request({
      url: '/pbl/social-activities',
      method: 'post',
      data
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// 更新活动
export const updateSocialActivity = async (uuid, data) => {
  try {
    const response = await request({
      url: `/pbl/social-activities/${uuid}`,
      method: 'put',
      data
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// 删除活动
export const deleteSocialActivity = async (uuid) => {
  try {
    const response = await request({
      url: `/pbl/social-activities/${uuid}`,
      method: 'delete'
    })
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// 报名参加活动
export const registerActivity = async (uuid) => {
  try {
    const response = await request({
      url: `/pbl/social-activities/${uuid}/register`,
      method: 'post'
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// 取消报名
export const cancelRegistration = async (uuid) => {
  try {
    const response = await request({
      url: `/pbl/social-activities/${uuid}/cancel`,
      method: 'post'
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// 提交活动反馈
export const submitActivityFeedback = async (uuid, data) => {
  try {
    const response = await request({
      url: `/pbl/social-activities/${uuid}/feedback`,
      method: 'post',
      data
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// 上传活动照片
export const uploadActivityPhotos = async (uuid, formData, onUploadProgress) => {
  try {
    const response = await request({
      url: `/pbl/social-activities/${uuid}/photos`,
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// 获取我的社会实践活动
export const getMySocialActivities = async (params) => {
  try {
    const response = await request({
      url: '/pbl/my-social-activities',
      method: 'get',
      params
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}
