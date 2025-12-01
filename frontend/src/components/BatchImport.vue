<template>
  <div class="batch-import">
    <el-dialog
      v-model="visible"
      :title="title"
      width="600px"
      :close-on-click-modal="false"
      @close="handleClose"
    >
      <div class="import-content">
        <!-- 步骤1：下载模板 -->
        <div class="step-section">
          <div class="step-title">
            <el-icon><Document /></el-icon>
            <span>步骤1：下载Excel模板</span>
          </div>
          <div class="step-content">
            <el-button type="primary" plain @click="downloadTemplate">
              <el-icon><Download /></el-icon>
              下载模板文件
            </el-button>
            <div class="tips">
              <el-icon><InfoFilled /></el-icon>
              请按照模板格式填写数据
            </div>
          </div>
        </div>

        <!-- 步骤2：上传文件 -->
        <div class="step-section">
          <div class="step-title">
            <el-icon><Upload /></el-icon>
            <span>步骤2：上传填好的Excel文件</span>
          </div>
          <div class="step-content">
            <el-upload
              ref="uploadRef"
              :action="uploadUrl"
              :headers="uploadHeaders"
              :on-success="handleSuccess"
              :on-error="handleError"
              :before-upload="beforeUpload"
              :auto-upload="false"
              :limit="1"
              :on-exceed="handleExceed"
              :file-list="fileList"
              accept=".xlsx,.xls"
              drag
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  仅支持 .xlsx 或 .xls 格式的Excel文件
                </div>
              </template>
            </el-upload>
          </div>
        </div>

        <!-- 导入结果 -->
        <div v-if="importResult" class="result-section">
          <el-alert
            :title="importResult.success ? '导入成功！' : '导入失败！'"
            :type="importResult.success ? 'success' : 'error'"
            :closable="false"
          >
            <div v-if="importResult.success">
              <p>成功导入 {{ importResult.data?.success || 0 }} 条数据</p>
              <div v-if="importResult.data?.created_users?.length" class="created-users">
                <p style="font-weight: bold; margin-top: 10px;">导入的用户：</p>
                <ul>
                  <li v-for="(user, index) in importResult.data.created_users.slice(0, 5)" :key="index">
                    {{ user.real_name }} ({{ user.username }})
                  </li>
                  <li v-if="importResult.data.created_users.length > 5">
                    ... 还有 {{ importResult.data.created_users.length - 5 }} 个
                  </li>
                </ul>
              </div>
            </div>
            <div v-else>
              <p>{{ importResult.message }}</p>
              <div v-if="importResult.data?.errors?.length" class="error-details">
                <p style="font-weight: bold; margin-top: 10px;">错误详情：</p>
                <ul>
                  <li v-for="(error, index) in importResult.data.errors.slice(0, 10)" :key="index" style="color: #f56c6c;">
                    {{ error }}
                  </li>
                  <li v-if="importResult.data.errors.length > 10">
                    ... 还有 {{ importResult.data.errors.length - 10 }} 个错误
                  </li>
                </ul>
              </div>
            </div>
          </el-alert>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleClose">取消</el-button>
          <el-button 
            type="primary" 
            @click="submitUpload"
            :loading="uploading"
            :disabled="fileList.length === 0"
          >
            {{ uploading ? '导入中...' : '开始导入' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Download, Upload, UploadFilled, InfoFilled } from '@element-plus/icons-vue'
import request from '@/api/request'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  type: {
    type: String,
    required: true,
    validator: (value) => ['teacher', 'student'].includes(value)
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const title = computed(() => {
  return props.type === 'teacher' ? '批量导入教师' : '批量导入学生'
})

const uploadUrl = computed(() => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  return props.type === 'teacher' 
    ? `${baseURL}/user-management/teachers/batch-import`
    : `${baseURL}/user-management/students/batch-import`
})

const templateUrl = computed(() => {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
  return props.type === 'teacher'
    ? `${baseURL}/user-management/teachers/import-template`
    : `${baseURL}/user-management/students/import-template`
})

const uploadRef = ref(null)
const fileList = ref([])
const uploading = ref(false)
const importResult = ref(null)

const uploadHeaders = computed(() => {
  const token = localStorage.getItem('token')
  return {
    'Authorization': `Bearer ${token}`
  }
})

// 下载模板
const downloadTemplate = async () => {
  try {
    const response = await request({
      url: templateUrl.value,
      method: 'get',
      responseType: 'blob'
    })
    
    const blob = new Blob([response], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = props.type === 'teacher' ? 'teacher_import_template.xlsx' : 'student_import_template.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('模板下载成功')
  } catch (error) {
    console.error('下载模板失败:', error)
    ElMessage.error('下载模板失败')
  }
}

// 上传前验证
const beforeUpload = (file) => {
  const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                  file.type === 'application/vnd.ms-excel' ||
                  file.name.endsWith('.xlsx') ||
                  file.name.endsWith('.xls')
  
  if (!isExcel) {
    ElMessage.error('只能上传Excel文件！')
    return false
  }
  
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过10MB！')
    return false
  }
  
  return true
}

// 文件数量超限
const handleExceed = () => {
  ElMessage.warning('只能上传一个文件，请先移除已选文件')
}

// 提交上传
const submitUpload = () => {
  if (!uploadRef.value) return
  
  importResult.value = null
  uploading.value = true
  uploadRef.value.submit()
}

// 上传成功
const handleSuccess = (response) => {
  uploading.value = false
  
  console.log('上传响应:', response)
  
  if (response.code === 200) {
    importResult.value = {
      success: true,
      message: response.message,
      data: response.data
    }
    
    ElMessage.success(response.message || '导入成功')
    
    // 通知父组件刷新列表
    setTimeout(() => {
      emit('success')
      handleClose()
    }, 2000)
  } else {
    importResult.value = {
      success: false,
      message: response.message || '导入失败',
      data: response.data
    }
    ElMessage.error(response.message || '导入失败')
  }
}

// 上传失败
const handleError = (error) => {
  uploading.value = false
  console.error('上传失败:', error)
  
  importResult.value = {
    success: false,
    message: '上传失败，请检查网络或文件格式',
    data: null
  }
  
  ElMessage.error('上传失败')
}

// 关闭对话框
const handleClose = () => {
  fileList.value = []
  importResult.value = null
  uploading.value = false
  visible.value = false
}
</script>

<style scoped>
.batch-import {
  .import-content {
    padding: 20px 0;
  }
  
  .step-section {
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px solid #ebeef5;
    
    &:last-child {
      border-bottom: none;
    }
  }
  
  .step-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: bold;
    color: #303133;
    margin-bottom: 15px;
    
    .el-icon {
      color: #409eff;
      font-size: 20px;
    }
  }
  
  .step-content {
    padding-left: 28px;
  }
  
  .tips {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 10px;
    padding: 8px 12px;
    background: #f4f4f5;
    border-radius: 4px;
    font-size: 13px;
    color: #606266;
    
    .el-icon {
      color: #909399;
    }
  }
  
  .result-section {
    margin-top: 20px;
    
    .created-users,
    .error-details {
      ul {
        margin: 5px 0;
        padding-left: 20px;
        
        li {
          margin: 3px 0;
          font-size: 13px;
        }
      }
    }
  }
  
  :deep(.el-upload-dragger) {
    padding: 40px;
  }
  
  :deep(.el-icon--upload) {
    font-size: 67px;
    color: #c0c4cc;
    margin-bottom: 16px;
  }
}
</style>

