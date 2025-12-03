import request from './request'

// 工作流管理API

// 获取工作流列表
export const getWorkflows = (params) => {
  return request({
    url: '/workflows',
    method: 'get',
    params
  })
}

// 创建工作流
export const createWorkflow = (data) => {
  return request({
    url: '/workflows',
    method: 'post',
    data
  })
}

// 获取工作流详情
export const getWorkflow = (uuid) => {
  return request({
    url: `/workflows/${uuid}`,
    method: 'get'
  })
}

// 更新工作流
export const updateWorkflow = (uuid, data) => {
  return request({
    url: `/workflows/${uuid}`,
    method: 'put',
    data
  })
}

// 删除工作流
export const deleteWorkflow = (uuid) => {
  return request({
    url: `/workflows/${uuid}`,
    method: 'delete'
  })
}

// 验证工作流
export const validateWorkflow = (uuid) => {
  return request({
    url: `/workflows/${uuid}/validate`,
    method: 'post'
  })
}

// 执行工作流
export const executeWorkflow = (uuid, data) => {
  return request({
    url: `/workflows/${uuid}/execute`,
    method: 'post',
    data
  })
}

// 获取执行记录详情
export const getExecution = (executionId) => {
  return request({
    url: `/workflow-executions/${executionId}`,
    method: 'get'
  })
}

// 获取执行记录列表
export const getExecutions = (params) => {
  return request({
    url: '/workflow-executions',
    method: 'get',
    params
  })
}

