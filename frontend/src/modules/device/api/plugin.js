import request from '@/utils/request'

// 插件管理API

// 创建新插件
export const createPlugin = (data) => {
  return request({
    url: '/ai/plugins',
    method: 'post',
    data
  })
}

// 获取插件列表
export const getPlugins = (params) => {
  return request({
    url: '/ai/plugins',
    method: 'get',
    params
  })
}

// 获取单个插件详情
export const getPlugin = (uuid) => {
  return request({
    url: `/ai/plugins/${uuid}`,
    method: 'get'
  })
}

// 更新插件信息
export const updatePlugin = (uuid, data) => {
  return request({
    url: `/ai/plugins/${uuid}`,
    method: 'put',
    data
  })
}

// 删除插件
export const deletePlugin = (uuid) => {
  return request({
    url: `/ai/plugins/${uuid}`,
    method: 'delete'
  })
}

