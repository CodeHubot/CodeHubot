import request from '@/utils/request'

/**
 * 与智能体对话
 */
export function chatWithAgent(data) {
  return request({
    url: '/ai/chat/',
    method: 'post',
    data,
    timeout: 120000 // 120秒超时（大模型响应可能需要较长时间）
  })
}

/**
 * 获取对话历史
 */
export function getChatHistory(agentUuid, params) {
  return request({
    url: `/ai/chat/history/${agentUuid}`,
    method: 'get',
    params
  })
}

/**
 * 清空对话历史
 */
export function clearChatHistory(agentUuid) {
  return request({
    url: `/ai/chat/history/${agentUuid}`,
    method: 'delete'
  })
}

/**
 * 获取当前用户的设备列表（轻量级，专用于聊天页面）
 */
export function getMyDevices() {
  return request({
    url: '/ai/chat/my-devices',
    method: 'get'
  })
}

