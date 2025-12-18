import request from '@/utils/request'

/**
 * 数据集管理 API
 */

// 获取数据集列表
export const getDatasets = (params) => {
  return request({
    url: '/pbl/datasets',
    method: 'get',
    params
  })
}

// 获取数据集详情
export const getDatasetDetail = (uuid) => {
  return request({
    url: `/pbl/datasets/${uuid}`,
    method: 'get'
  })
}

// 创建数据集
export const createDataset = (data) => {
  return request({
    url: '/pbl/datasets',
    method: 'post',
    data
  })
}

// 更新数据集
export const updateDataset = (uuid, data) => {
  return request({
    url: `/pbl/datasets/${uuid}`,
    method: 'put',
    data
  })
}

// 删除数据集
export const deleteDataset = (uuid) => {
  return request({
    url: `/pbl/datasets/${uuid}`,
    method: 'delete'
  })
}

// 上传数据集文件
export const uploadDatasetFile = (formData, onUploadProgress) => {
  return request({
    url: '/pbl/datasets/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress
  })
}

// 下载数据集
export const downloadDataset = (uuid) => {
  return request({
    url: `/pbl/datasets/${uuid}/download`,
    method: 'get',
    responseType: 'blob'
  })
}

// 更新数据集公开状态
export const updateDatasetPublicStatus = (uuid, isPublic) => {
  return request({
    url: `/pbl/datasets/${uuid}/public`,
    method: 'put',
    data: { is_public: isPublic }
  })
}

// 评价数据集质量
export const rateDataset = (uuid, score) => {
  return request({
    url: `/pbl/datasets/${uuid}/rate`,
    method: 'post',
    data: { quality_score: score }
  })
}
