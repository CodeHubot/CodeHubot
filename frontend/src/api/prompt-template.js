import request from '@/utils/request'

/**
 * 获取提示词模板列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 * @returns {Promise}
 */
export function getPromptTemplates(params) {
  return request({
    url: '/api/ai/prompt-templates',
    method: 'get',
    params
  })
}

/**
 * 获取提示词模板详情
 * @param {number} templateId - 模板ID
 * @returns {Promise}
 */
export function getPromptTemplate(templateId) {
  return request({
    url: `/api/ai/prompt-templates/${templateId}`,
    method: 'get'
  })
}

/**
 * 创建提示词模板
 * @param {Object} data - 模板数据
 * @returns {Promise}
 */
export function createPromptTemplate(data) {
  return request({
    url: '/api/ai/prompt-templates',
    method: 'post',
    data
  })
}

/**
 * 更新提示词模板
 * @param {number} templateId - 模板ID
 * @param {Object} data - 模板数据
 * @returns {Promise}
 */
export function updatePromptTemplate(templateId, data) {
  return request({
    url: `/api/ai/prompt-templates/${templateId}`,
    method: 'put',
    data
  })
}

/**
 * 删除提示词模板
 * @param {number} templateId - 模板ID
 * @returns {Promise}
 */
export function deletePromptTemplate(templateId) {
  return request({
    url: `/api/ai/prompt-templates/${templateId}`,
    method: 'delete'
  })
}
