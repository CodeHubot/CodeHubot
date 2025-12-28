/**
 * AI学习助手API接口
 * 用于学生学习过程中的AI助手对话
 * 
 * 后端路径: /api/pbl/learning-assistant
 */
import request from '@/utils/request'

/**
 * 与AI学习助手对话（核心接口）
 * @param {Object} data - 对话数据
 * @param {string} data.message - 用户消息内容
 * @param {Object} data.context - 学习上下文
 * @param {string} data.context.course_uuid - 课程UUID（可选）
 * @param {string} data.context.course_name - 课程名称（可选）
 * @param {string} data.context.unit_uuid - 单元UUID（可选）
 * @param {string} data.context.unit_name - 单元名称（可选）
 * @param {Object} data.context.current_resource - 当前学习资源（可选）
 * @param {string} data.context.current_resource.uuid - 资源UUID
 * @param {string} data.context.current_resource.type - 资源类型（video/pdf/quiz）
 * @param {string} data.context.current_resource.title - 资源标题
 * @param {string} data.conversation_id - 会话UUID（可选，不传则创建新会话）
 * @returns {Promise}
 * @example
 * chatWithAssistant({
 *   message: '什么是Python？',
 *   context: {
 *     course_uuid: 'xxx',
 *     course_name: 'Python编程基础',
 *     unit_uuid: 'yyy',
 *     unit_name: '第一章',
 *     current_resource: {
 *       uuid: 'zzz',
 *       type: 'video',
 *       title: 'Python入门'
 *     }
 *   },
 *   conversation_id: 'existing-conversation-uuid' // 可选
 * })
 */
export function chatWithAssistant(data) {
  return request({
    url: '/pbl/learning-assistant/chat',
    method: 'post',
    data
  })
}

/**
 * 获取会话列表
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码，默认1
 * @param {number} params.pageSize - 每页数量，默认20
 * @returns {Promise}
 */
export function getConversations(params) {
  return request({
    url: '/pbl/learning-assistant/conversations',
    method: 'get',
    params
  })
}

/**
 * 获取会话详情
 * @param {string} conversationUuid - 会话UUID
 * @returns {Promise}
 */
export function getConversation(conversationUuid) {
  return request({
    url: `/pbl/learning-assistant/conversations/${conversationUuid}`,
    method: 'get'
  })
}

/**
 * 获取会话的所有消息
 * @param {string} conversationUuid - 会话UUID
 * @returns {Promise}
 */
export function getConversationMessages(conversationUuid) {
  return request({
    url: `/pbl/learning-assistant/conversations/${conversationUuid}/messages`,
    method: 'get'
  })
}

/**
 * 更新会话信息（如重命名标题）
 * @param {string} conversationUuid - 会话UUID
 * @param {Object} data - 更新数据
 * @param {string} data.title - 新标题
 * @returns {Promise}
 */
export function updateConversation(conversationUuid, data) {
  return request({
    url: `/pbl/learning-assistant/conversations/${conversationUuid}`,
    method: 'put',
    data
  })
}

/**
 * 删除会话（软删除）
 * @param {string} conversationUuid - 会话UUID
 * @returns {Promise}
 */
export function deleteConversation(conversationUuid) {
  return request({
    url: `/pbl/learning-assistant/conversations/${conversationUuid}`,
    method: 'delete'
  })
}

/**
 * 清空所有会话（软删除）
 * @returns {Promise}
 */
export function clearAllConversations() {
  return request({
    url: '/pbl/learning-assistant/conversations',
    method: 'delete'
  })
}

/**
 * 提交消息反馈（有帮助/无帮助）
 * @param {string} messageUuid - 消息UUID
 * @param {Object} data - 反馈数据
 * @param {boolean} data.was_helpful - 是否有帮助
 * @param {string} data.feedback - 反馈内容（可选）
 * @returns {Promise}
 */
export function submitMessageFeedback(messageUuid, data) {
  return request({
    url: `/pbl/learning-assistant/messages/${messageUuid}/feedback`,
    method: 'post',
    data
  })
}

/**
 * 获取我的学习档案
 * @returns {Promise}
 */
export function getMyProfile() {
  return request({
    url: '/pbl/learning-assistant/my-profile',
    method: 'get'
  })
}

// ==================== 教师端API ====================

/**
 * 获取学生列表（教师视角）
 * @param {Object} params - 查询参数
 * @param {string} params.course_uuid - 课程UUID（可选）
 * @param {number} params.page - 页码
 * @param {number} params.pageSize - 每页数量
 * @returns {Promise}
 */
export function getStudentsList(params) {
  return request({
    url: '/pbl/learning-assistant/teacher/students',
    method: 'get',
    params
  })
}

/**
 * 查看学生的对话列表（教师视角）
 * @param {string} studentUuid - 学生UUID
 * @param {Object} params - 查询参数
 * @param {number} params.page - 页码
 * @param {number} params.pageSize - 每页数量
 * @returns {Promise}
 */
export function getStudentConversations(studentUuid, params) {
  return request({
    url: `/pbl/learning-assistant/teacher/students/${studentUuid}/conversations`,
    method: 'get',
    params
  })
}

/**
 * 查看会话的所有消息（教师视角）
 * @param {string} conversationUuid - 会话UUID
 * @returns {Promise}
 */
export function getConversationMessagesAsTeacher(conversationUuid) {
  return request({
    url: `/pbl/learning-assistant/teacher/conversations/${conversationUuid}/messages`,
    method: 'get'
  })
}

/**
 * 教师修正AI回复
 * @param {string} messageUuid - 消息UUID
 * @param {Object} data - 修正数据
 * @param {string} data.correction - 修正内容
 * @returns {Promise}
 */
export function correctMessage(messageUuid, data) {
  return request({
    url: `/pbl/learning-assistant/teacher/messages/${messageUuid}/correct`,
    method: 'post',
    data
  })
}

/**
 * 标记需要关注的对话
 * @param {string} conversationUuid - 会话UUID
 * @param {Object} data - 标记数据
 * @param {string} data.comment - 备注（可选）
 * @returns {Promise}
 */
export function flagConversation(conversationUuid, data = {}) {
  return request({
    url: `/pbl/learning-assistant/teacher/conversations/${conversationUuid}/flag`,
    method: 'post',
    data
  })
}

/**
 * 取消标记
 * @param {string} conversationUuid - 会话UUID
 * @returns {Promise}
 */
export function unflagConversation(conversationUuid) {
  return request({
    url: `/pbl/learning-assistant/teacher/conversations/${conversationUuid}/flag`,
    method: 'delete'
  })
}

/**
 * 获取统计数据（教师视角）
 * @param {Object} params - 查询参数
 * @param {string} params.course_uuid - 课程UUID（可选）
 * @returns {Promise}
 */
export function getTeacherStatistics(params) {
  return request({
    url: '/pbl/learning-assistant/teacher/statistics',
    method: 'get',
    params
  })
}
