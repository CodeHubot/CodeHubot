import request from '@/utils/request'

/**
 * 视频播放进度追踪API
 */

// ========== 播放进度上报接口 ==========

/**
 * 创建播放会话
 * @param {string} resourceUuid - 资源UUID
 * @param {number} duration - 视频总时长（秒）
 * @param {string} deviceType - 设备类型
 * @returns {Promise}
 */
export function createPlaySession(resourceUuid, duration, deviceType = null) {
  return request({
    url: '/api/pbl/video/progress/session/create',
    method: 'post',
    data: {
      resource_uuid: resourceUuid,
      duration: duration,
      device_type: deviceType
    }
  })
}

/**
 * 更新播放进度
 * @param {string} sessionId - 会话ID
 * @param {number} currentPosition - 当前播放位置（秒）
 * @param {string} status - 播放状态
 * @param {string} eventType - 事件类型
 * @returns {Promise}
 */
export function updatePlayProgress(sessionId, currentPosition, status = 'playing', eventType = 'progress') {
  return request({
    url: '/api/pbl/video/progress/progress/update',
    method: 'post',
    data: {
      session_id: sessionId,
      current_position: currentPosition,
      status: status,
      event_type: eventType
    }
  })
}

/**
 * 记录拖动事件
 * @param {string} sessionId - 会话ID
 * @param {number} fromPosition - 拖动前的位置（秒）
 * @param {number} toPosition - 拖动后的位置（秒）
 * @returns {Promise}
 */
export function recordSeekEvent(sessionId, fromPosition, toPosition) {
  return request({
    url: '/api/pbl/video/progress/event/seek',
    method: 'post',
    data: {
      session_id: sessionId,
      from_position: fromPosition,
      to_position: toPosition
    }
  })
}

/**
 * 记录暂停事件
 * @param {string} sessionId - 会话ID
 * @param {number} position - 暂停位置（秒）
 * @returns {Promise}
 */
export function recordPauseEvent(sessionId, position) {
  return request({
    url: '/api/pbl/video/progress/event/pause',
    method: 'post',
    data: {
      session_id: sessionId,
      position: position
    }
  })
}

/**
 * 记录播放结束事件
 * @param {string} sessionId - 会话ID
 * @param {number} position - 结束位置（秒）
 * @returns {Promise}
 */
export function recordEndEvent(sessionId, position) {
  return request({
    url: '/api/pbl/video/progress/event/ended',
    method: 'post',
    data: {
      session_id: sessionId,
      position: position
    }
  })
}

// ========== 播放进度查询接口 ==========

/**
 * 获取最后观看位置（用于断点续看）
 * @param {string} resourceUuid - 资源UUID
 * @returns {Promise}
 */
export function getLastPosition(resourceUuid) {
  return request({
    url: `/api/pbl/video/progress/last-position/${resourceUuid}`,
    method: 'get'
  })
}

/**
 * 获取用户观看统计
 * @param {string} resourceUuid - 资源UUID
 * @param {number} userId - 用户ID（可选）
 * @returns {Promise}
 */
export function getUserWatchStats(resourceUuid, userId = null) {
  return request({
    url: `/api/pbl/video/progress/stats/user/${resourceUuid}`,
    method: 'get',
    params: userId ? { user_id: userId } : {}
  })
}

/**
 * 获取视频整体观看统计（所有学生）
 * @param {string} resourceUuid - 资源UUID
 * @returns {Promise}
 */
export function getVideoWatchStats(resourceUuid) {
  return request({
    url: `/api/pbl/video/progress/stats/video/${resourceUuid}`,
    method: 'get'
  })
}

/**
 * 获取学生观看排行榜
 * @param {string} resourceUuid - 资源UUID
 * @param {number} limit - 返回数量
 * @returns {Promise}
 */
export function getStudentsRanking(resourceUuid, limit = 20) {
  return request({
    url: `/api/pbl/video/progress/stats/ranking/${resourceUuid}`,
    method: 'get',
    params: { limit }
  })
}

/**
 * 获取播放会话信息
 * @param {string} sessionId - 会话ID
 * @returns {Promise}
 */
export function getSessionInfo(sessionId) {
  return request({
    url: `/api/pbl/video/progress/session/${sessionId}`,
    method: 'get'
  })
}

// ========== 视频播放凭证接口 ==========

/**
 * 获取视频播放凭证
 * @param {string} resourceUuid - 资源UUID
 * @returns {Promise}
 */
export function getVideoPlayAuth(resourceUuid) {
  return request({
    url: `/api/pbl/video/play-auth/${resourceUuid}`,
    method: 'get'
  })
}

/**
 * 获取视频信息
 * @param {string} resourceUuid - 资源UUID
 * @returns {Promise}
 */
export function getVideoInfo(resourceUuid) {
  return request({
    url: `/api/pbl/video/info/${resourceUuid}`,
    method: 'get'
  })
}

/**
 * 获取视频观看统计信息
 * @param {string} resourceUuid - 资源UUID
 * @returns {Promise}
 */
export function getWatchStats(resourceUuid) {
  return request({
    url: `/api/pbl/video/watch-stats/${resourceUuid}`,
    method: 'get'
  })
}

/**
 * 获取视频观看历史记录
 * @param {string} resourceUuid - 资源UUID
 * @param {number} limit - 返回记录数限制
 * @returns {Promise}
 */
export function getWatchHistory(resourceUuid, limit = 50) {
  return request({
    url: `/api/pbl/video/watch-history/${resourceUuid}`,
    method: 'get',
    params: { limit }
  })
}
