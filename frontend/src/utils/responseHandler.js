/**
 * 统一的API响应处理工具
 * 兼容两种响应格式：
 * 1. { success: true, data: {...} }
 * 2. { code: 200, data: {...} }
 */

/**
 * 检查响应是否成功
 * @param {Object} response - axios响应对象
 * @returns {boolean}
 */
export function isResponseSuccess(response) {
  if (!response || !response.data) {
    return false
  }
  
  // 格式1: { success: true }
  if (response.data.success === true) {
    return true
  }
  
  // 格式2: { code: 200 }
  if (response.data.code === 200) {
    return true
  }
  
  return false
}

/**
 * 获取响应数据
 * @param {Object} response - axios响应对象
 * @returns {any} 返回data字段内容，如果不存在返回null
 */
export function getResponseData(response) {
  if (!isResponseSuccess(response)) {
    return null
  }
  
  return response.data.data || null
}

/**
 * 获取响应消息
 * @param {Object} response - axios响应对象
 * @returns {string}
 */
export function getResponseMessage(response) {
  if (!response || !response.data) {
    return ''
  }
  
  return response.data.message || response.data.msg || ''
}

/**
 * 处理列表响应（自动提取items和total）
 * @param {Object} response - axios响应对象
 * @returns {Object} { items: [], total: 0 }
 */
export function handleListResponse(response) {
  const data = getResponseData(response)
  
  if (!data) {
    return { items: [], total: 0 }
  }
  
  return {
    items: data.items || data.list || [],
    total: data.total || 0,
    page: data.page || 1,
    pageSize: data.page_size || data.pageSize || 20
  }
}

/**
 * 处理详情响应
 * @param {Object} response - axios响应对象
 * @returns {Object|null}
 */
export function handleDetailResponse(response) {
  return getResponseData(response)
}
