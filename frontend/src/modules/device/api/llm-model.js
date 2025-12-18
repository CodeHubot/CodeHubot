import request from '@/utils/request'

/**
 * 获取大模型列表
 */
export function getLLMModels(params) {
  return request({
    url: '/ai/llm-models',
    method: 'get',
    params
  })
}

/**
 * 获取激活的大模型列表
 */
export function getActiveLLMModels() {
  return request({
    url: '/ai/llm-models/active',
    method: 'get'
  })
}

/**
 * 获取默认大模型
 */
export function getDefaultLLMModel() {
  return request({
    url: '/ai/llm-models/default',
    method: 'get'
  })
}

/**
 * 获取指定大模型详情
 */
export function getLLMModel(uuid) {
  return request({
    url: `/ai/llm-models/${uuid}`,
    method: 'get'
  })
}

/**
 * 创建大模型配置
 */
export function createLLMModel(data) {
  return request({
    url: '/ai/llm-models',
    method: 'post',
    data
  })
}

/**
 * 更新大模型配置
 */
export function updateLLMModel(uuid, data) {
  return request({
    url: `/ai/llm-models/${uuid}`,
    method: 'put',
    data
  })
}

/**
 * 删除大模型配置
 */
export function deleteLLMModel(uuid) {
  return request({
    url: `/ai/llm-models/${uuid}`,
    method: 'delete'
  })
}

/**
 * 设置默认大模型
 */
export function setDefaultLLMModel(uuid) {
  return request({
    url: `/ai/llm-models/${uuid}/set-default`,
    method: 'post'
  })
}

/**
 * 获取提供商列表
 */
export function getLLMProviders() {
  return request({
    url: '/ai/llm-models/providers',
    method: 'get'
  })
}

