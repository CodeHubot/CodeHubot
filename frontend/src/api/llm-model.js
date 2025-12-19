import request from '@/utils/request'

/**
 * 获取所有LLM模型列表
 * @param {Object} params - 查询参数
 * @param {number} params.skip - 跳过的记录数
 * @param {number} params.limit - 返回的记录数
 * @returns {Promise}
 */
export function getLLMModels(params) {
  return request({
    url: '/api/ai/llm-models',
    method: 'get',
    params
  })
}

/**
 * 获取激活状态的LLM模型列表
 * @returns {Promise}
 */
export function getActiveLLMModels() {
  return request({
    url: '/api/ai/llm-models/active',
    method: 'get'
  })
}

/**
 * 获取默认LLM模型
 * @returns {Promise}
 */
export function getDefaultLLMModel() {
  return request({
    url: '/api/ai/llm-models/default',
    method: 'get'
  })
}

/**
 * 获取LLM模型详情
 * @param {number} modelId - 模型ID
 * @returns {Promise}
 */
export function getLLMModel(modelId) {
  return request({
    url: `/api/ai/llm-models/${modelId}`,
    method: 'get'
  })
}

/**
 * 创建LLM模型
 * @param {Object} data - 模型数据
 * @returns {Promise}
 */
export function createLLMModel(data) {
  return request({
    url: '/api/ai/llm-models',
    method: 'post',
    data
  })
}

/**
 * 更新LLM模型
 * @param {number} modelId - 模型ID
 * @param {Object} data - 模型数据
 * @returns {Promise}
 */
export function updateLLMModel(modelId, data) {
  return request({
    url: `/api/ai/llm-models/${modelId}`,
    method: 'put',
    data
  })
}

/**
 * 删除LLM模型
 * @param {number} modelId - 模型ID
 * @returns {Promise}
 */
export function deleteLLMModel(modelId) {
  return request({
    url: `/api/ai/llm-models/${modelId}`,
    method: 'delete'
  })
}

/**
 * 设置默认LLM模型
 * @param {number} modelId - 模型ID
 * @returns {Promise}
 */
export function setDefaultLLMModel(modelId) {
  return request({
    url: `/api/ai/llm-models/${modelId}/set-default`,
    method: 'post'
  })
}

/**
 * 获取LLM提供商列表
 * @returns {Promise}
 */
export function getLLMProviders() {
  return request({
    url: '/api/ai/llm-models/providers',
    method: 'get'
  })
}
