// 管理员相关API
import request from '@/utils/request'
import { API_ENDPOINTS, createApiUrl, handleApiError } from './config'

/**
 * 平台管理员登录（用户名+密码）
 */
export const platformAdminLogin = async (loginData) => {
  try {
    const response = await request.post('/pbl/admin/auth/platform-login', loginData)
    return response
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 机构管理员登录（学校代码+工号+密码）
 */
export const adminLogin = async (loginData) => {
  try {
    const response = await request.post('/pbl/admin/auth/login', loginData)
    return response
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取当前管理员信息
 */
export const getCurrentAdmin = async () => {
  try {
    const response = await request.get('/pbl/admin/auth/me')
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取课程列表
 */
export const getCourses = async (params = {}) => {
  try {
    const response = await request.get('/pbl/admin/courses', { params })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取课程完整详情（包括所有单元、资料和任务）
 */
export const getCourseFullDetail = async (courseId) => {
  try {
    const response = await request.get(`/pbl/admin/courses/${courseId}/full-detail`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 创建课程
 */
export const createCourse = async (courseData) => {
  try {
    const response = await request.post('/pbl/admin/courses', courseData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 更新课程
 */
export const updateCourse = async (courseId, courseData) => {
  try {
    const response = await request.put(`/pbl/admin/courses/${courseId}`, courseData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 删除课程
 */
export const deleteCourse = async (courseId) => {
  try {
    const response = await request.delete(`/pbl/admin/courses/${courseId}`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取学习单元列表
 */
export const getUnits = async (courseUuid) => {
  try {
    const response = await request.get(`/pbl/admin/units/course/${courseUuid}`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 创建学习单元
 */
export const createUnit = async (unitData) => {
  try {
    const response = await request.post('/pbl/admin/units', unitData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 更新学习单元
 */
export const updateUnit = async (unitUuid, unitData) => {
  try {
    const response = await request.put(`/pbl/admin/units/${unitUuid}`, unitData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 删除学习单元
 */
export const deleteUnit = async (unitUuid) => {
  try {
    const response = await request.delete(`/pbl/admin/units/${unitUuid}`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取资料列表
 */
export const getResources = async (unitId) => {
  try {
    const response = await request.get(`/pbl/admin/resources/unit/${unitId}`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 创建资料
 */
export const createResource = async (resourceData) => {
  try {
    const response = await request.post('/pbl/admin/resources', resourceData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 上传资料文件
 */
export const uploadResourceFile = async (unitId, fileType, file) => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('file_type', fileType)
    
    const response = await request.post(
      `/pbl/admin/resources/upload?unit_id=${unitId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 更新资料
 */
export const updateResource = async (resourceId, resourceData) => {
  try {
    const response = await request.put(`/pbl/admin/resources/${resourceId}`, resourceData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 删除资料
 */
export const deleteResource = async (resourceId) => {
  try {
    const response = await request.delete(`/pbl/admin/resources/${resourceId}`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取单元的任务列表
 */
export const getTasks = async (unitId) => {
  try {
    const response = await request.get(`/pbl/admin/tasks/unit/${unitId}`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 创建任务
 */
export const createTask = async (taskData) => {
  try {
    const response = await request.post('/pbl/admin/tasks', taskData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取任务详情
 */
export const getTaskDetail = async (taskId) => {
  try {
    const response = await request.get(`/pbl/admin/tasks/${taskId}`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 更新任务
 */
export const updateTask = async (taskId, taskData) => {
  try {
    const response = await request.put(`/pbl/admin/tasks/${taskId}`, taskData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 删除任务
 */
export const deleteTask = async (taskId) => {
  try {
    const response = await request.delete(`/pbl/admin/tasks/${taskId}`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取任务的学生提交列表
 */
export const getTaskProgressList = async (taskId) => {
  try {
    const response = await request.get(`/pbl/admin/tasks/${taskId}/progress`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 教师评分任务
 */
export const gradeTask = async (taskId, userId, score, feedback) => {
  try {
    const response = await request.post(`/pbl/admin/tasks/${taskId}/grade`, null, {
      params: {
        user_id: userId,
        score: score,
        feedback: feedback
      }
    })
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取成果列表
 */
export const getOutputs = async (params = {}) => {
  try {
    const response = await request.get('/pbl/admin/outputs', { params })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取成果详情
 */
export const getOutputDetail = async (uuid) => {
  try {
    const response = await request.get(`/pbl/admin/outputs/${uuid}`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 更新成果公开状态
 */
export const updateOutputStatus = async (uuid, isPublic) => {
  try {
    const response = await request.put(`/pbl/admin/outputs/${uuid}/status`, {
      is_public: isPublic
    })
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 评审成果
 */
export const reviewOutput = async (uuid, data) => {
  try {
    const response = await request.post(`/pbl/admin/outputs/${uuid}/review`, data)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 删除成果
 */
export const deleteOutput = async (uuid) => {
  try {
    const response = await request.delete(`/pbl/admin/outputs/${uuid}`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取成果统计数据
 */
export const getOutputStatistics = async () => {
  try {
    const response = await request.get('/pbl/admin/outputs/statistics/overview')
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// ========== 视频权限管理 API ==========

/**
 * 获取视频的观看权限配置
 */
export const getVideoPermission = async (resourceUuid, userId) => {
  try {
    const response = await request.get(`/video/permission/${resourceUuid}/user/${userId}`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 设置单个学生的视频观看权限
 */
export const setVideoPermission = async (resourceUuid, permissionData) => {
  try {
    const response = await request.post(`/video/permission/${resourceUuid}`, permissionData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 批量设置多个学生的视频观看权限
 */
export const batchSetVideoPermissions = async (resourceUuid, permissionData) => {
  try {
    const response = await request.post(`/video/permission/${resourceUuid}/batch`, permissionData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 删除学生的个性化视频权限配置
 */
export const deleteVideoPermission = async (resourceUuid, userId) => {
  try {
    const response = await request.delete(`/video/permission/${resourceUuid}/user/${userId}`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取视频的观看统计信息
 */
export const getVideoWatchStats = async (resourceUuid) => {
  try {
    const response = await request.get(`/video/watch-stats/${resourceUuid}`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取视频的观看历史记录
 */
export const getVideoWatchHistory = async (resourceUuid, limit = 50) => {
  try {
    const response = await request.get(`/video/watch-history/${resourceUuid}`, {
      params: { limit }
    })
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// ========== 课程单元管理 API（新版） ==========

/**
 * 为课程创建单元
 */
export const createCourseUnit = async (courseUuid, unitData) => {
  try {
    const response = await request.post(`/pbl/admin/courses/${courseUuid}/units`, unitData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 更新课程单元
 */
export const updateCourseUnit = async (courseUuid, unitUuid, unitData) => {
  try {
    const response = await request.put(`/pbl/admin/courses/${courseUuid}/units/${unitUuid}`, unitData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 删除课程单元
 */
export const deleteCourseUnit = async (courseUuid, unitUuid) => {
  try {
    const response = await request.delete(`/pbl/admin/courses/${courseUuid}/units/${unitUuid}`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// ========== 课程资源管理 API（新版） ==========

/**
 * 为单元创建资源
 */
export const createCourseResource = async (courseUuid, unitUuid, resourceData) => {
  try {
    const response = await request.post(`/pbl/admin/courses/${courseUuid}/units/${unitUuid}/resources`, resourceData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 更新课程资源
 */
export const updateCourseResource = async (courseUuid, unitUuid, resourceUuid, resourceData) => {
  try {
    const response = await request.put(`/pbl/admin/courses/${courseUuid}/units/${unitUuid}/resources/${resourceUuid}`, resourceData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 删除课程资源
 */
export const deleteCourseResource = async (courseUuid, unitUuid, resourceUuid) => {
  try {
    const response = await request.delete(`/pbl/admin/courses/${courseUuid}/units/${unitUuid}/resources/${resourceUuid}`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 更新资源顺序
 */
export const updateResourceOrder = async (courseUuid, unitUuid, resourceUuid, newOrder) => {
  try {
    const response = await request.patch(
      `/pbl/admin/courses/${courseUuid}/units/${unitUuid}/resources/${resourceUuid}/order`,
      null,
      { params: { new_order: newOrder } }
    )
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// ========== 课程任务管理 API（新版） ==========

/**
 * 为单元创建任务
 */
export const createCourseTask = async (courseUuid, unitUuid, taskData) => {
  try {
    const response = await request.post(`/pbl/admin/courses/${courseUuid}/units/${unitUuid}/tasks`, taskData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 更新课程任务
 */
export const updateCourseTask = async (courseUuid, unitUuid, taskUuid, taskData) => {
  try {
    const response = await request.put(`/pbl/admin/courses/${courseUuid}/units/${unitUuid}/tasks/${taskUuid}`, taskData)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 删除课程任务
 */
export const deleteCourseTask = async (courseUuid, unitUuid, taskUuid) => {
  try {
    const response = await request.delete(`/pbl/admin/courses/${courseUuid}/units/${unitUuid}/tasks/${taskUuid}`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

// ========== 从模板选择资源和任务 API ==========

/**
 * 获取课程所对应模板的所有资源
 */
export const getCourseTemplateResources = async (courseUuid) => {
  try {
    const response = await request.get(`/pbl/admin/courses/${courseUuid}/template-resources`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 获取课程所对应模板的所有任务
 */
export const getCourseTemplateTasks = async (courseUuid) => {
  try {
    const response = await request.get(`/pbl/admin/courses/${courseUuid}/template-tasks`)
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 从模板复制资源到课程单元
 */
export const copyResourceFromTemplate = async (courseUuid, unitUuid, resourceTemplateUuid) => {
  try {
    const response = await request.post(
      `/pbl/admin/courses/${courseUuid}/units/${unitUuid}/resources/copy-from-template`,
      null,
      { params: { resource_template_uuid: resourceTemplateUuid } }
    )
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * 从模板复制任务到课程单元
 */
export const copyTaskFromTemplate = async (courseUuid, unitUuid, taskTemplateUuid) => {
  try {
    const response = await request.post(
      `/pbl/admin/courses/${courseUuid}/units/${unitUuid}/tasks/copy-from-template`,
      null,
      { params: { task_template_uuid: taskTemplateUuid } }
    )
    return response.data.data || response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}
