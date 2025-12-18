/**
 * 系统配置相关API
 */
import request from '@/utils/request'

/**
 * 获取所有系统配置
 */
export const getAllConfigs = (category) => {
  return request.get('/api/system/configs', {
    params: { category }
  })
}

/**
 * 获取公开的系统配置
 */
export const getPublicConfigs = () => {
  return request.get('/api/system/configs/public')
}

/**
 * 获取单个配置项
 */
export const getConfig = (configKey) => {
  return request.get(`/api/system/configs/${configKey}`)
}

/**
 * 创建系统配置
 */
export const createConfig = (data) => {
  return request.post('/api/system/configs', data)
}

/**
 * 更新系统配置
 */
export const updateConfig = (configKey, data) => {
  return request.put(`/api/system/configs/${configKey}`, data)
}

/**
 * 删除系统配置
 */
export const deleteConfig = (configKey) => {
  return request.delete(`/api/system/configs/${configKey}`)
}

/**
 * 获取模块配置
 */
export const getModuleConfig = () => {
  return request.get('/api/system/modules')
}

/**
 * 更新模块配置
 */
export const updateModuleConfig = (data) => {
  return request.put('/api/system/modules', data)
}

/**
 * 初始化模块配置
 */
export const initModuleConfig = () => {
  return request.post('/api/system/modules/init')
}
