import request from '@/utils/request'

// 产品管理API

// 创建新产品
export const createProduct = (data) => {
  return request({
    url: '/products',
    method: 'post',
    data
  })
}

// 获取产品列表
export const getProducts = (params) => {
  return request({
    url: '/products',
    method: 'get',
    params
  })
}

// 获取产品摘要列表（用于下拉选择）
export const getProductsSummary = (params) => {
  return request({
    url: '/products/summary',
    method: 'get',
    params
  })
}

// 获取单个产品详情
export const getProduct = (id) => {
  return request({
    url: `/products/${id}`,
    method: 'get'
  })
}

// 更新产品信息
export const updateProduct = (id, data) => {
  return request({
    url: `/products/${id}`,
    method: 'put',
    data
  })
}

// 删除产品
export const deleteProduct = (id) => {
  return request({
    url: `/products/${id}`,
    method: 'delete'
  })
}

// 获取产品的所有设备
export const getProductDevices = (id, params) => {
  return request({
    url: `/products/${id}/devices`,
    method: 'get',
    params
  })
}

// 获取所有产品类别
export const getProductCategories = () => {
  return request({
    url: '/products/categories',
    method: 'get'
  })
}

// 获取产品统计信息
export const getProductStatistics = (id) => {
  return request({
    url: `/products/${id}/statistics`,
    method: 'get'
  })
}