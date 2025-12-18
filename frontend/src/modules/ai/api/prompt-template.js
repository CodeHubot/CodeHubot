/**
 * 提示词模板API
 */
import request from '@/utils/request'

/**
 * 获取提示词模板列表
 */
export const getPromptTemplates = (params = {}) => {
  return request({
    url: '/ai/prompt-templates/',
    method: 'get',
    params: {
      page: 1,
      page_size: 100,
      is_active: true,
      ...params
    }
  })
}

/**
 * 获取单个模板详情
 */
export const getPromptTemplate = (templateId) => {
  return request({
    url: `/ai/prompt-templates/${templateId}`,
    method: 'get'
  })
}

/**
 * 创建提示词模板（仅管理员）
 */
export const createPromptTemplate = (data) => {
  return request({
    url: '/ai/prompt-templates/',
    method: 'post',
    data
  })
}

/**
 * 更新提示词模板（仅管理员）
 */
export const updatePromptTemplate = (templateId, data) => {
  return request({
    url: `/ai/prompt-templates/${templateId}`,
    method: 'put',
    data
  })
}

/**
 * 删除提示词模板（仅管理员）
 */
export const deletePromptTemplate = (templateId) => {
  return request({
    url: `/ai/prompt-templates/${templateId}`,
    method: 'delete'
  })
}

