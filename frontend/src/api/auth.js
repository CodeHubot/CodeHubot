import request from './request'

// 用户登录
export const login = (email, password) => {
  return request.post('/auth/login', {
    email,
    password
  })
}

// 用户注册
export const register = (email, username, password) => {
  return request.post('/auth/register', {
    email,
    username,
    password
  })
}

// 重置密码
export const resetPassword = (email, password) => {
  return request.post('/auth/reset-password', {
    email,
    password
  })
}

// 获取用户信息
export const getUserInfo = () => {
  return request.get('/auth/user-info')
}

// 更新用户个人信息
export const updateProfile = (data) => {
  return request.put('/auth/profile', data)
}

// 修改密码
export const changePassword = (data) => {
  return request.post('/auth/change-password', data)
}

// 获取用户统计信息
export const getUserStats = () => {
  return request.get('/users/stats')
}

// 刷新 access token
export const refreshToken = (refresh_token) => {
  return request.post('/auth/refresh', {
    refresh_token
  })
}
