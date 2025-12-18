/**
 * 设备分组管理API
 */
import request from '@/utils/request'

// ============================================================================
// 设备分组管理
// ============================================================================

/**
 * 创建设备组
 */
export function createDeviceGroup(data) {
  return request({
    url: '/device-groups',
    method: 'post',
    data
  }).then(response => response.data)
}

/**
 * 获取设备组列表
 */
export function getDeviceGroups(params) {
  return request({
    url: '/device-groups',
    method: 'get',
    params
  }).then(response => response.data)
}

/**
 * 获取设备组详情
 */
export function getDeviceGroup(groupUuid) {
  return request({
    url: `/device-groups/${groupUuid}`,
    method: 'get'
  }).then(response => response.data)
}

/**
 * 更新设备组
 */
export function updateDeviceGroup(groupUuid, data) {
  return request({
    url: `/device-groups/${groupUuid}`,
    method: 'put',
    data
  }).then(response => response.data)
}

/**
 * 删除设备组
 */
export function deleteDeviceGroup(groupUuid) {
  return request({
    url: `/device-groups/${groupUuid}`,
    method: 'delete'
  }).then(response => response.data)
}

// ============================================================================
// 设备组成员管理
// ============================================================================

/**
 * 添加设备到组
 */
export function addDeviceToGroup(groupUuid, data) {
  return request({
    url: `/device-groups/${groupUuid}/devices`,
    method: 'post',
    data
  }).then(response => response.data)
}

/**
 * 批量添加设备到组
 */
export function batchAddDevicesToGroup(groupUuid, data) {
  return request({
    url: `/device-groups/${groupUuid}/devices/batch`,
    method: 'post',
    data
  }).then(response => response.data)
}

/**
 * 获取设备组的设备列表
 */
export function getGroupDevices(groupUuid, params) {
  return request({
    url: `/device-groups/${groupUuid}/devices`,
    method: 'get',
    params
  }).then(response => response.data)
}

/**
 * 从设备组移除设备
 */
export function removeDeviceFromGroup(groupUuid, deviceId) {
  return request({
    url: `/device-groups/${groupUuid}/devices/${deviceId}`,
    method: 'delete'
  }).then(response => response.data)
}

// ============================================================================
// 课程设备授权管理
// ============================================================================

/**
 * 为课程授权设备组
 */
export function createDeviceAuthorization(courseUuid, data) {
  return request({
    url: `/courses/${courseUuid}/device-authorizations`,
    method: 'post',
    data
  }).then(response => response.data)
}

/**
 * 获取课程的设备授权列表
 */
export function getDeviceAuthorizations(courseUuid) {
  return request({
    url: `/courses/${courseUuid}/device-authorizations`,
    method: 'get'
  }).then(response => response.data)
}

/**
 * 更新设备授权
 */
export function updateDeviceAuthorization(courseUuid, authId, data) {
  return request({
    url: `/courses/${courseUuid}/device-authorizations/${authId}`,
    method: 'put',
    data
  }).then(response => response.data)
}

/**
 * 撤销设备授权
 */
export function revokeDeviceAuthorization(courseUuid, authId) {
  return request({
    url: `/courses/${courseUuid}/device-authorizations/${authId}`,
    method: 'delete'
  }).then(response => response.data)
}

/**
 * 获取课程已授权的设备列表
 */
export function getAuthorizedDevices(courseUuid, params) {
  return request({
    url: `/courses/${courseUuid}/authorized-devices`,
    method: 'get',
    params
  }).then(response => response.data)
}

