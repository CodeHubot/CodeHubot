/**
 * 知识库管理API
 */
import request from './request'

// ============================================================================
// 知识库CRUD
// ============================================================================

/**
 * 创建知识库
 */
export function createKnowledgeBase(data) {
  return request({
    url: '/knowledge-bases',
    method: 'post',
    data
  })
}

/**
 * 获取知识库列表
 */
export function getKnowledgeBases(params) {
  return request({
    url: '/knowledge-bases',
    method: 'get',
    params
  })
}

/**
 * 获取知识库详情
 */
export function getKnowledgeBase(uuid) {
  return request({
    url: `/knowledge-bases/${uuid}`,
    method: 'get'
  })
}

/**
 * 更新知识库
 */
export function updateKnowledgeBase(uuid, data) {
  return request({
    url: `/knowledge-bases/${uuid}`,
    method: 'put',
    data
  })
}

/**
 * 删除知识库
 */
export function deleteKnowledgeBase(uuid, cascade = false) {
  return request({
    url: `/knowledge-bases/${uuid}`,
    method: 'delete',
    params: { cascade }
  })
}

/**
 * 获取知识库层级树
 */
export function getKnowledgeBaseTree(params) {
  return request({
    url: '/knowledge-bases/hierarchy-tree',
    method: 'get',
    params
  })
}

/**
 * 获取全局统计
 */
export function getGlobalStatistics() {
  return request({
    url: '/knowledge-bases/statistics/global',
    method: 'get'
  })
}

// ============================================================================
// 文档管理
// ============================================================================

/**
 * 上传文档
 */
/**
 * 预览文档切分结果
 * 超时时间：60秒（大文件需要更多时间进行编码检测和切分）
 */
export function previewDocumentChunks(kb_uuid, formData) {
  return request({
    url: `/kb-documents/${kb_uuid}/preview`,
    method: 'post',
    data: formData,
    // 不设置 Content-Type，让浏览器自动设置（包括 boundary）
    // axios 会自动检测 FormData 并设置正确的 Content-Type
    timeout: 60000  // 60秒超时
  })
}

/**
 * 上传文档
 * 超时时间：120秒（包含上传+编码检测+切分+向量化任务提交）
 */
export function uploadDocument(kb_uuid, formData) {
  return request({
    url: `/kb-documents/${kb_uuid}`,
    method: 'post',
    data: formData,
    // 不设置 Content-Type，让浏览器自动设置（包括 boundary）
    // axios 会自动检测 FormData 并设置正确的 Content-Type
    timeout: 120000  // 120秒超时
  })
}

/**
 * 获取文档列表
 */
export function getDocuments(kb_uuid, params) {
  return request({
    url: `/kb-documents/${kb_uuid}`,
    method: 'get',
    params
  })
}

/**
 * 获取文档详情
 */
export function getDocument(kb_uuid, doc_uuid, include_content = true) {
  return request({
    url: `/kb-documents/${kb_uuid}/${doc_uuid}`,
    method: 'get',
    params: {
      include_content
    }
  })
}

/**
 * 更新文档
 */
export function updateDocument(kb_uuid, doc_uuid, data) {
  return request({
    url: `/kb-documents/${kb_uuid}/${doc_uuid}`,
    method: 'put',
    data
  })
}

/**
 * 删除文档
 */
export function deleteDocument(kb_uuid, doc_uuid) {
  return request({
    url: `/kb-documents/${kb_uuid}/${doc_uuid}`,
    method: 'delete'
  })
}

/**
 * 手动触发文档向量化
 */
export function triggerEmbedding(kb_uuid, doc_uuid, force = false) {
  return request({
    url: `/kb-documents/${kb_uuid}/${doc_uuid}/embed`,
    method: 'post',
    data: { force }
  })
}

/**
 * 获取文档的文本块列表
 */
export function getDocumentChunks(kb_uuid, doc_uuid, params) {
  return request({
    url: `/kb-documents/${kb_uuid}/${doc_uuid}/chunks`,
    method: 'get',
    params
  })
}

/**
 * 下载文档
 */
export function downloadDocument(kb_uuid, doc_uuid) {
  return request({
    url: `/kb-documents/${kb_uuid}/${doc_uuid}/download`,
    method: 'get',
    responseType: 'blob'
  })
}

// ============================================================================
// 知识检索
// ============================================================================

/**
 * 知识检索
 */
export function searchKnowledge(data) {
  return request({
    url: '/knowledge-bases/search',
    method: 'post',
    data
  })
}

/**
 * 获取搜索建议
 */
export function getSearchSuggestions(params) {
  return request({
    url: '/knowledge-bases/suggestions',
    method: 'get',
    params
  })
}

// ============================================================================
// 智能体关联
// ============================================================================

/**
 * 获取智能体可用但未关联的知识库列表
 */
export function getAvailableKnowledgeBases(agent_uuid) {
  return request({
    url: `/knowledge-bases/agents/${agent_uuid}/available-knowledge-bases`,
    method: 'get'
  })
}

/**
 * 获取智能体关联的知识库列表
 */
export function getAgentKnowledgeBases(agent_uuid) {
  return request({
    url: `/knowledge-bases/agents/${agent_uuid}/knowledge-bases`,
    method: 'get'
  })
}

/**
 * 为智能体添加知识库关联
 */
export function addAgentKnowledgeBase(agent_uuid, data) {
  return request({
    url: `/knowledge-bases/agents/${agent_uuid}/knowledge-bases`,
    method: 'post',
    data
  })
}

/**
 * 批量为智能体添加知识库关联
 */
export function batchAddAgentKnowledgeBases(agent_uuid, knowledge_bases) {
  return request({
    url: `/knowledge-bases/agents/${agent_uuid}/knowledge-bases/batch`,
    method: 'post',
    data: knowledge_bases
  })
}

/**
 * 更新智能体知识库关联配置
 */
export function updateAgentKnowledgeBase(agent_uuid, kb_uuid, data) {
  return request({
    url: `/knowledge-bases/agents/${agent_uuid}/knowledge-bases/${kb_uuid}`,
    method: 'put',
    data
  })
}

/**
 * 移除智能体知识库关联
 */
export function removeAgentKnowledgeBase(agent_uuid, kb_uuid) {
  return request({
    url: `/knowledge-bases/agents/${agent_uuid}/knowledge-bases/${kb_uuid}`,
    method: 'delete'
  })
}

// ============================================================================
// 向量检索
// ============================================================================

/**
 * 在知识库中进行向量检索
 * @param {string} kb_uuid - 知识库UUID
 * @param {Object} params - 查询参数
 * @param {string} params.query - 查询文本
 * @param {number} params.top_k - 返回结果数量（默认5，最大20）
 */
export function searchInKnowledgeBase(kb_uuid, params) {
  return request({
    url: `/kb-documents/${kb_uuid}/search`,
    method: 'post',
    params,
    timeout: 30000 // 30秒超时（向量化查询可能需要一些时间）
  })
}

