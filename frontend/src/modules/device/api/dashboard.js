import request from '@/utils/request'

// 获取仪表盘统计数据
export function getDashboardStats() {
  return request({
    url: '/dashboard/stats',
    method: 'get'
  })
}

// 获取最近设备列表
export function getRecentDevices(limit = 5) {
  return request({
    url: '/dashboard/recent-devices',
    method: 'get',
    params: { limit }
  })
}

// 获取最近交互记录
export function getRecentInteractions(limit = 10) {
  return request({
    url: '/dashboard/recent-interactions',
    method: 'get',
    params: { limit }
  })
}