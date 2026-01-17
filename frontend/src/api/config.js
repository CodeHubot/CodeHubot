// API配置文件
export const API_CONFIG = {
  // 后端API基础URL
  // 在开发模式下使用相对路径，通过 Vite proxy 转发到后端
  // 在生产模式下使用空字符串，通过 nginx proxy 转发
  BASE_URL: import.meta.env.VITE_API_BASE_URL || (import.meta.env.MODE === 'production' ? '' : ''),
  
  // API版本（已弃用，后端不使用版本号）
  API_VERSION: '',
  
  // 完整的API基础路径
  get API_BASE() {
    return `${this.BASE_URL}/api`
  },
  
  // 请求超时时间（毫秒）
  TIMEOUT: 10000,
  
  // 默认请求头
  DEFAULT_HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
}

// HTTP状态码
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500
}

// API端点
export const API_ENDPOINTS = {
  // 认证相关
  AUTH: {
    LOGIN: '/auth/login',
    STUDENT_LOGIN: '/student/auth/login',
    STUDENT_REFRESH: '/student/auth/refresh',
    STUDENT_ME: '/student/auth/me',
    ADMIN_LOGIN: '/admin/auth/login',
    ADMIN_REFRESH: '/admin/auth/refresh',
    ADMIN_ME: '/admin/auth/me',
    REFRESH: '/auth/refresh',
    LOGOUT: '/auth/logout',
    CURRENT_USER: '/auth/me',
    SWITCH_TENANT: '/auth/switch-tenant'
  },
  
  // 用户相关
  USERS: {
    LIST: '/users',
    DETAIL: (id) => `/users/${id}`,
    CREATE: '/users',
    UPDATE: (id) => `/users/${id}`,
    DELETE: (id) => `/users/${id}`,
    TEAMS: (id) => `/users/${id}/teams`,
    PERMISSIONS: (id) => `/users/${id}/permissions`,
    STATS: '/users/stats'
  },
  
  // 课程相关
  COURSES: {
    LIST: '/courses',
    DETAIL: (id) => `/courses/${id}`,
    CREATE: '/courses',
    UPDATE: (id) => `/courses/${id}`,
    DELETE: (id) => `/courses/${id}`,
    UNITS: (id) => `/courses/${id}/units`
  },
  
  // 单元相关
  UNITS: {
    LIST: '/units',
    DETAIL: (id) => `/units/${id}`,
    RESOURCES: (id) => `/units/${id}/resources`,
    TASKS: (id) => `/units/${id}/tasks`
  },
  
  // AI对话相关
  AI: {
    CHAT: '/ai/chat',
    CONVERSATIONS: '/ai/conversations',
    CONVERSATION: (id) => `/ai/conversations/${id}`
  }
}

// 错误消息映射
export const ERROR_MESSAGES = {
  NETWORK_ERROR: '网络连接失败，请检查网络设置',
  TIMEOUT_ERROR: '请求超时，请稍后重试',
  UNAUTHORIZED: '登录已过期，请重新登录',
  FORBIDDEN: '没有权限执行此操作',
  NOT_FOUND: '请求的资源不存在',
  SERVER_ERROR: '服务器内部错误，请稍后重试',
  VALIDATION_ERROR: '数据验证失败，请检查输入',
  UNKNOWN_ERROR: '未知错误，请稍后重试'
}

// 请求工具函数
export const createApiUrl = (endpoint) => {
  return `${API_CONFIG.API_BASE}${endpoint}`
}

// 处理API错误
export const handleApiError = (error) => {
  if (!error.response) {
    // 网络错误
    return ERROR_MESSAGES.NETWORK_ERROR
  }
  
  const status = error.response.status
  const data = error.response.data
  
  // 如果后端返回了具体的错误消息，优先使用
  if (data && data.message) {
    return data.message
  }
  
  // 根据状态码返回默认错误消息
  switch (status) {
    case HTTP_STATUS.UNAUTHORIZED:
      return ERROR_MESSAGES.UNAUTHORIZED
    case HTTP_STATUS.FORBIDDEN:
      return ERROR_MESSAGES.FORBIDDEN
    case HTTP_STATUS.NOT_FOUND:
      return ERROR_MESSAGES.NOT_FOUND
    case HTTP_STATUS.BAD_REQUEST:
      return ERROR_MESSAGES.VALIDATION_ERROR
    case HTTP_STATUS.INTERNAL_SERVER_ERROR:
      return ERROR_MESSAGES.SERVER_ERROR
    default:
      return ERROR_MESSAGES.UNKNOWN_ERROR
  }
}

// 创建请求配置
export const createRequestConfig = (options = {}) => {
  return {
    timeout: API_CONFIG.TIMEOUT,
    headers: {
      ...API_CONFIG.DEFAULT_HEADERS,
      ...options.headers
    },
    ...options
  }
}

