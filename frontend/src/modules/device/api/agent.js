import request from '@/utils/request'

// 智能体管理API

// 创建新智能体
export const createAgent = (data) => {
  return request({
    url: '/ai/agents',
    method: 'post',
    data
  })
}

// 获取智能体列表
export const getAgents = (params) => {
  return request({
    url: '/ai/agents',
    method: 'get',
    params
  })
}

// 获取单个智能体详情
export const getAgent = (id) => {
  return request({
    url: `/ai/agents/${id}`,
    method: 'get'
  })
}

// 更新智能体信息
export const updateAgent = (id, data) => {
  return request({
    url: `/ai/agents/${id}`,
    method: 'put',
    data
  })
}

// 删除智能体
export const deleteAgent = (id) => {
  return request({
    url: `/ai/agents/${id}`,
    method: 'delete'
  })
}

