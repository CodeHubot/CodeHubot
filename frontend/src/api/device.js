import request from './request'

// 获取设备列表
export function getDevices(params) {
  return request({
    url: '/devices',
    method: 'get',
    params
  })
}

// 获取包含产品信息的设备列表
export function getDevicesWithProductInfo(params) {
  return request({
    url: '/devices/with-product-info',
    method: 'get',
    params
  })
}

// 获取设备详情（使用UUID）
export function getDevice(uuid) {
  return request({
    url: `/devices/${uuid}`,
    method: 'get'
  })
}

// 创建设备
export function createDevice(data) {
  return request({
    url: '/devices/',
    method: 'post',
    data
  })
}

// 更新设备信息（使用UUID）
export function updateDevice(uuid, data) {
  return request({
    url: `/devices/${uuid}`,
    method: 'put',
    data
  })
}

// 删除设备（使用UUID）
export function deleteDevice(uuid) {
  return request({
    url: `/devices/${uuid}`,
    method: 'delete'
  })
}

// 设置设备归属学校
export function setDeviceSchool(uuid, schoolId) {
  return request({
    url: `/devices/${uuid}/set-school`,
    method: 'put',
    params: { school_id: schoolId }
  })
}

// 设备心跳（使用UUID）
export function deviceHeartbeat(uuid) {
  return request({
    url: `/devices/${uuid}/heartbeat`,
    method: 'post'
  })
}

// 前端页面预注册设备
export function preRegisterDevice(data) {
  return request({
    url: '/devices/pre-register',
    method: 'post',
    data
  })
}

// 设备注册
export function registerDevice(data) {
  return request({
    url: '/devices/register',
    method: 'post',
    data
  })
}

// 获取设备配置（使用UUID）
export function getDeviceConfig(uuid) {
  return request({
    url: `/devices/${uuid}/config`,
    method: 'get'
  })
}

// 更新设备配置（使用UUID）
export function updateDeviceConfig(uuid, data) {
  return request({
    url: `/devices/${uuid}/config`,
    method: 'put',
    data
  })
}

// 获取设备实时数据（通过UUID）
export function getDeviceRealtimeData(uuid, limit = 10) {
  return request({
    url: `/devices/${uuid}/realtime-data`,
    method: 'get',
    params: { limit }
  })
}

// 获取设备预设指令（通过UUID）
export function getDevicePresets(uuid) {
  return request({
    url: `/devices/${uuid}/presets`,
    method: 'get'
  })
}

// 发送设备控制命令（通过UUID）
export function sendDeviceControl(uuid, command) {
  return request({
    url: `/devices/${uuid}/control`,
    method: 'post',
    data: command
  })
}

// 获取设备历史记录（模拟）
export function getDeviceHistory(id, params = {}) {
  return request({
    url: `/devices/${id}/history`,
    method: 'get',
    params
  })
}

// 获取设备统计概览
export function getDevicesStatistics() {
  return request({
    url: '/devices/statistics/overview',
    method: 'get'
  })
}

// 获取指定产品的所有设备
export function getDevicesByProduct(productId, params) {
  return request({
    url: `/devices/by-product/${productId}`,
    method: 'get',
    params
  })
}

// 激活设备（使用UUID）
export function activateDevice(uuid) {
  return request({
    url: `/devices/${uuid}/activate`,
    method: 'post'
  })
}

// 停用设备（使用UUID）
export function deactivateDevice(uuid) {
  return request({
    url: `/devices/${uuid}/deactivate`,
    method: 'post'
  })
}

// 获取设备的产品信息（使用UUID）
export function getDeviceProductInfo(uuid) {
  return request({
    url: `/devices/${uuid}/product-info`,
    method: 'get'
  })
}

// 获取设备的完整配置信息（包括产品配置，使用UUID）
export function getDeviceFullConfig(uuid) {
  return request({
    url: `/devices/${uuid}/full-config`,
    method: 'get'
  })
}

// 获取设备的产品配置（传感器和控制端口配置，使用UUID）
export function getDeviceProductConfig(uuid) {
  return request({
    url: `/devices/${uuid}/product-config`,
    method: 'get'
  })
}

// 解绑设备（使用UUID）- 自动清除所有历史数据
export function unbindDevice(uuid) {
  return request({
    url: `/devices/${uuid}/unbind`,
    method: 'post'
  })
}