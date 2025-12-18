/**
 * PBL小组设备授权API
 */
import request from '@/utils/request'

// ============================================================================
// PBL小组设备授权管理
// ============================================================================

/**
 * 授权设备给多个小组（批量）
 */
export function createPBLDeviceAuthorizations(deviceUuid, data) {
  return request({
    url: `/devices/${deviceUuid}/pbl-authorizations`,
    method: 'post',
    data
  }).then(response => response.data)
}

/**
 * 查询设备已授权的小组列表
 */
export function getPBLDeviceAuthorizations(deviceUuid, params) {
  return request({
    url: `/devices/${deviceUuid}/pbl-authorizations`,
    method: 'get',
    params
  }).then(response => response.data)
}

/**
 * 撤销单个授权
 */
export function revokePBLDeviceAuthorization(deviceUuid, authId) {
  return request({
    url: `/devices/${deviceUuid}/pbl-authorizations/${authId}`,
    method: 'delete'
  }).then(response => response.data)
}

/**
 * 批量撤销授权
 */
export function revokePBLDeviceAuthorizationsBatch(deviceUuid, data) {
  return request({
    url: `/devices/${deviceUuid}/pbl-authorizations`,
    method: 'delete',
    data
  }).then(response => response.data)
}

/**
 * 查询教师可授权的小组列表（用于前端选择）
 */
export function getAuthorizableGroups() {
  return request({
    url: '/devices/authorizable-groups',
    method: 'get'
  }).then(response => response.data)
}
