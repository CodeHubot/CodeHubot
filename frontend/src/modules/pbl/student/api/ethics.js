import request from '@/utils/request'

/**
 * 伦理教育 API
 */

// 获取伦理案例列表
export const getEthicsCases = (params) => {
  return request({
    url: '/pbl/ethics-cases',
    method: 'get',
    params
  })
}

// 获取伦理案例详情
export const getEthicsCaseDetail = (uuid) => {
  return request({
    url: `/pbl/ethics-cases/${uuid}`,
    method: 'get'
  })
}

// 创建伦理案例
export const createEthicsCase = (data) => {
  return request({
    url: '/pbl/ethics-cases',
    method: 'post',
    data
  })
}

// 更新伦理案例
export const updateEthicsCase = (uuid, data) => {
  return request({
    url: `/pbl/ethics-cases/${uuid}`,
    method: 'put',
    data
  })
}

// 删除伦理案例
export const deleteEthicsCase = (uuid) => {
  return request({
    url: `/pbl/ethics-cases/${uuid}`,
    method: 'delete'
  })
}

// 点赞案例
export const likeEthicsCase = (uuid) => {
  return request({
    url: `/pbl/ethics-cases/${uuid}/like`,
    method: 'post'
  })
}

// 获取伦理活动列表
export const getEthicsActivities = (params) => {
  return request({
    url: '/pbl/ethics-activities',
    method: 'get',
    params
  })
}

// 获取伦理活动详情
export const getEthicsActivityDetail = (uuid) => {
  return request({
    url: `/pbl/ethics-activities/${uuid}`,
    method: 'get'
  })
}

// 创建伦理活动
export const createEthicsActivity = (data) => {
  return request({
    url: '/pbl/ethics-activities',
    method: 'post',
    data
  })
}

// 更新伦理活动
export const updateEthicsActivity = (uuid, data) => {
  return request({
    url: `/pbl/ethics-activities/${uuid}`,
    method: 'put',
    data
  })
}

// 删除伦理活动
export const deleteEthicsActivity = (uuid) => {
  return request({
    url: `/pbl/ethics-activities/${uuid}`,
    method: 'delete'
  })
}

// 参与伦理活动
export const joinEthicsActivity = (uuid) => {
  return request({
    url: `/pbl/ethics-activities/${uuid}/join`,
    method: 'post'
  })
}

// 提交讨论记录
export const submitDiscussion = (uuid, data) => {
  return request({
    url: `/pbl/ethics-activities/${uuid}/discussion`,
    method: 'post',
    data
  })
}

// 提交反思
export const submitReflection = (uuid, data) => {
  return request({
    url: `/pbl/ethics-activities/${uuid}/reflection`,
    method: 'post',
    data
  })
}
