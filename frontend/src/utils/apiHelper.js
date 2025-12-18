/**
 * API调用辅助工具
 * 提供常用的数据处理和格式化方法
 */

/**
 * 处理列表响应数据
 * @param {Object} response - API响应对象
 * @returns {Object} { items: [], total: 0, page: 1, pageSize: 20 }
 */
export function handleListResponse(response) {
  if (!response || !response.success || !response.data) {
    return {
      items: [],
      total: 0,
      page: 1,
      pageSize: 20
    }
  }

  const data = response.data

  return {
    items: data.items || data.list || data.data || [],
    total: data.total || 0,
    page: data.page || data.current_page || 1,
    pageSize: data.page_size || data.pageSize || data.per_page || 20
  }
}

/**
 * 处理详情响应数据
 * @param {Object} response - API响应对象
 * @returns {Object|null}
 */
export function handleDetailResponse(response) {
  if (!response || !response.success) {
    return null
  }

  return response.data || null
}

/**
 * 处理操作响应（创建、更新、删除等）
 * @param {Object} response - API响应对象
 * @returns {boolean}
 */
export function handleOperationResponse(response) {
  return response && response.success === true
}

/**
 * 构建查询参数（自动过滤空值）
 * @param {Object} params - 原始参数对象
 * @returns {Object} 过滤后的参数对象
 */
export function buildQueryParams(params) {
  const result = {}
  
  for (const key in params) {
    const value = params[key]
    
    // 过滤 null、undefined、空字符串
    if (value !== null && value !== undefined && value !== '') {
      result[key] = value
    }
  }
  
  return result
}

/**
 * 构建分页参数
 * @param {number} page - 页码
 * @param {number} pageSize - 每页数量
 * @param {Object} filters - 其他筛选条件
 * @returns {Object}
 */
export function buildPaginationParams(page, pageSize, filters = {}) {
  return buildQueryParams({
    page,
    page_size: pageSize,
    ...filters
  })
}

/**
 * 格式化日期时间
 * @param {string} dateString - 日期字符串
 * @param {string} format - 格式（'date'|'datetime'|'time'）
 * @returns {string}
 */
export function formatDateTime(dateString, format = 'datetime') {
  if (!dateString) return ''
  
  const date = new Date(dateString)
  
  if (isNaN(date.getTime())) return ''
  
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  
  switch (format) {
    case 'date':
      return `${year}-${month}-${day}`
    case 'time':
      return `${hours}:${minutes}:${seconds}`
    case 'datetime':
    default:
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
  }
}

/**
 * 防抖函数
 * @param {Function} func - 要防抖的函数
 * @param {number} wait - 等待时间（毫秒）
 * @returns {Function}
 */
export function debounce(func, wait = 300) {
  let timeout
  
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * 节流函数
 * @param {Function} func - 要节流的函数
 * @param {number} limit - 限制时间（毫秒）
 * @returns {Function}
 */
export function throttle(func, limit = 300) {
  let inThrottle
  
  return function executedFunction(...args) {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

/**
 * 深拷贝对象
 * @param {any} obj - 要拷贝的对象
 * @returns {any}
 */
export function deepClone(obj) {
  if (obj === null || typeof obj !== 'object') {
    return obj
  }
  
  if (obj instanceof Date) {
    return new Date(obj.getTime())
  }
  
  if (obj instanceof Array) {
    return obj.map(item => deepClone(item))
  }
  
  const clonedObj = {}
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      clonedObj[key] = deepClone(obj[key])
    }
  }
  
  return clonedObj
}
