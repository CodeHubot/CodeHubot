/**
 * 渠道管理API接口
 */
import request from '@/utils/request'

/**
 * 获取所有渠道商列表
 */
export function getChannelPartners() {
  return request({
    url: '/pbl/channel-management/partners',
    method: 'get'
  })
}

/**
 * 创建渠道商
 */
export function createChannelPartner(data) {
  return request({
    url: '/pbl/channel-management/partners',
    method: 'post',
    data
  })
}

/**
 * 获取渠道商详情
 */
export function getChannelPartnerDetail(partnerId) {
  return request({
    url: `/pbl/channel-management/partners/${partnerId}`,
    method: 'get'
  })
}

/**
 * 更新渠道商信息
 */
export function updateChannelPartner(partnerId, data) {
  return request({
    url: `/pbl/channel-management/partners/${partnerId}`,
    method: 'put',
    data
  })
}

/**
 * 重置渠道商密码
 */
export function resetPartnerPassword(partnerId, newPassword) {
  return request({
    url: `/pbl/channel-management/partners/${partnerId}/reset-password`,
    method: 'post',
    params: { new_password: newPassword }
  })
}

/**
 * 为渠道商分配学校
 */
export function assignSchoolsToPartner(data) {
  return request({
    url: '/pbl/channel-management/assign-schools',
    method: 'post',
    data
  })
}

/**
 * 解除渠道商与学校的关联
 */
export function removeSchoolFromPartner(partnerId, schoolId) {
  return request({
    url: `/pbl/channel-management/partners/${partnerId}/schools/${schoolId}`,
    method: 'delete'
  })
}

/**
 * 获取可分配的学校列表
 */
export function getAvailableSchools() {
  return request({
    url: '/pbl/channel-management/schools/available',
    method: 'get'
  })
}

/**
 * 获取渠道统计数据
 */
export function getChannelStatistics() {
  return request({
    url: '/pbl/channel-management/statistics',
    method: 'get'
  })
}

/**
 * 获取所有学校列表
 */
export function getSchools() {
  return request({
    url: '/pbl/channel-management/schools',
    method: 'get'
  })
}

/**
 * 创建学校
 */
export function createSchool(data) {
  return request({
    url: '/pbl/channel-management/schools',
    method: 'post',
    data
  })
}
