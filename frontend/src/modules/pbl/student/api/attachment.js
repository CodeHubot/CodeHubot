/**
 * 学生作业附件API
 */
import request from '@/utils/request'

/**
 * 临时上传附件（不需要progress_id）
 * 用户选择文件后立即调用，返回file_token
 * @param {File} file - 文件对象
 * @returns {Promise<Object>} 临时附件信息（包含file_token）
 */
export function uploadTempAttachment(file) {
  const formData = new FormData()
  formData.append('file', file)
  
  return request({
    url: '/pbl/student/temp-attachments/upload-temp',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 删除临时附件
 * @param {string} fileToken - 临时文件标识
 * @returns {Promise<Object>} 删除结果
 */
export function deleteTempAttachment(fileToken) {
  return request({
    url: `/pbl/student/temp-attachments/temp/${fileToken}`,
    method: 'delete'
  })
}

/**
 * 上传作业附件（已废弃，使用uploadTempAttachment代替）
 * @param {number} progressId - 任务进度ID
 * @param {File} file - 文件对象
 * @returns {Promise<Object>} 上传的附件信息
 */
export function uploadAttachment(progressId, file) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('progress_id', progressId)
  
  return request({
    url: `/pbl/student/attachments/upload?progress_id=${progressId}`,
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 删除作业附件
 * @param {string} attachmentUuid - 附件UUID
 * @returns {Promise<Object>} 删除结果
 */
export function deleteAttachment(attachmentUuid) {
  return request({
    url: `/pbl/student/attachments/${attachmentUuid}`,
    method: 'delete'
  })
}

/**
 * 获取任务进度的所有附件
 * @param {number} progressId - 任务进度ID
 * @returns {Promise<Array>} 附件列表
 */
export function getAttachmentsByProgress(progressId) {
  return request({
    url: `/pbl/student/attachments/progress/${progressId}`,
    method: 'get'
  })
}

/**
 * 下载附件
 * @param {string} attachmentUuid - 附件UUID
 * @returns {Promise<Blob>} 文件数据
 */
export function downloadAttachment(attachmentUuid) {
  return request({
    url: `/pbl/student/attachments/${attachmentUuid}/download`,
    method: 'get',
    responseType: 'blob'
  })
}

/**
 * 格式化文件大小
 * @param {number} bytes - 文件大小（字节）
 * @returns {string} 格式化后的文件大小
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

/**
 * 检查文件类型是否允许
 * @param {File} file - 文件对象
 * @returns {boolean} 是否允许上传
 */
export function isAllowedFileType(file) {
  const allowedTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ]
  
  const allowedExtensions = ['.pdf', '.doc', '.docx']
  
  const fileName = file.name.toLowerCase()
  const hasValidExtension = allowedExtensions.some(ext => fileName.endsWith(ext))
  const hasValidType = allowedTypes.includes(file.type)
  
  return hasValidExtension || hasValidType
}

/**
 * 获取文件类型图标
 * @param {string} fileExt - 文件扩展名
 * @returns {string} 图标名称
 */
export function getFileIcon(fileExt) {
  const ext = fileExt.toLowerCase()
  if (ext === '.pdf') {
    return 'document'
  } else if (ext === '.doc' || ext === '.docx') {
    return 'document'
  }
  return 'document'
}

