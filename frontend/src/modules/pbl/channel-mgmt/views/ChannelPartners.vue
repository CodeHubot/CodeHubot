<template>
  <div class="channel-partners">
    <el-card class="header-card" shadow="never">
      <div class="header-content">
        <div>
          <h2 class="page-title">渠道商管理</h2>
          <p class="page-description">管理平台所有渠道商账号</p>
        </div>
        <el-button type="primary" :icon="Plus" @click="showCreateDialog">
          新增渠道商
        </el-button>
      </div>
    </el-card>

    <el-card class="content-card" shadow="never" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span class="card-title">渠道商列表</span>
          <el-input
            v-model="searchText"
            placeholder="搜索渠道商名称"
            style="width: 300px"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>

      <el-table :data="filteredPartners" style="width: 100%">
        <el-table-column prop="username" label="账号" width="150" />
        <el-table-column prop="name" label="渠道商名称" width="150" />
        <el-table-column prop="company_name" label="公司名称" min-width="200" />
        <el-table-column prop="phone" label="联系电话" width="130" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        
        <el-table-column prop="school_count" label="负责学校数" width="120" align="center">
          <template #default="{ row }">
            <el-tag>{{ row.school_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="course_count" label="课程数" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="success">{{ row.course_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="is_active" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '正常' : '已禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="300" align="center" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">查看</el-button>
            <el-button size="small" type="primary" @click="showEditDialog(row)">编辑</el-button>
            <el-button size="small" type="warning" @click="resetPassword(row)">重置密码</el-button>
            <el-button
              size="small"
              :type="row.is_active ? 'danger' : 'success'"
              @click="toggleStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="filteredPartners.length === 0 && !loading" class="empty-state">
        <el-empty description="暂无渠道商数据" />
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'create' ? '新增渠道商' : '编辑渠道商'"
      width="600px"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="100px" autocomplete="off">
        <!-- 防止浏览器自动填充的隐藏字段 -->
        <input type="text" style="display:none" />
        <input type="password" style="display:none" />
        
        <el-form-item label="账号" prop="username" v-if="dialogType === 'create'">
          <el-input 
            v-model="formData.username" 
            placeholder="请输入账号"
            autocomplete="off"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="dialogType === 'create'">
          <el-input 
            v-model="formData.password" 
            type="password" 
            placeholder="请输入密码（至少6位）"
            autocomplete="new-password"
            data-lpignore="true"
          />
        </el-form-item>
        <el-form-item label="渠道商名称" prop="name">
          <el-input 
            v-model="formData.name" 
            placeholder="请输入渠道商名称"
            autocomplete="off"
          />
        </el-form-item>
        <el-form-item label="公司名称" prop="company_name">
          <el-input 
            v-model="formData.company_name" 
            placeholder="请输入公司名称"
            autocomplete="off"
          />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input 
            v-model="formData.phone" 
            placeholder="请输入联系电话"
            autocomplete="off"
          />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input 
            v-model="formData.email" 
            placeholder="请输入邮箱"
            autocomplete="off"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog
      v-model="resetPasswordDialogVisible"
      title="重置密码"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="resetPasswordForm" :rules="resetPasswordRules" ref="resetPasswordFormRef" label-width="100px">
        <el-alert
          title="密码规则"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        >
          <ul style="margin: 5px 0; padding-left: 20px; font-size: 13px;">
            <li>密码长度至少6位</li>
            <li>建议包含大小写字母、数字和特殊字符</li>
          </ul>
        </el-alert>

        <el-form-item label="渠道商" style="margin-bottom: 15px;">
          <el-tag>{{ currentResetPartner?.name || currentResetPartner?.username }}</el-tag>
        </el-form-item>

        <el-form-item label="新密码" prop="newPassword">
          <div style="display: flex; gap: 8px;">
            <el-input
              v-model="resetPasswordForm.newPassword"
              type="password"
              placeholder="请输入新密码（至少6位）"
              show-password
              autocomplete="new-password"
              data-lpignore="true"
              @input="checkPasswordStrength"
              style="flex: 1;"
            />
            <el-tooltip content="自动生成强密码" placement="top">
              <el-button 
                type="primary" 
                :icon="Refresh" 
                @click="generatePassword"
                style="flex-shrink: 0;"
              >
                生成密码
              </el-button>
            </el-tooltip>
            <el-tooltip content="复制密码到剪贴板" placement="top" v-if="resetPasswordForm.newPassword">
              <el-button 
                :icon="CopyDocument" 
                @click="copyPasswordToClipboard"
                style="flex-shrink: 0;"
              />
            </el-tooltip>
          </div>
        </el-form-item>

        <el-form-item label="密码强度" v-if="resetPasswordForm.newPassword">
          <div class="password-strength">
            <div class="strength-bar">
              <div 
                class="strength-fill" 
                :class="passwordStrength.class"
                :style="{ width: passwordStrength.percent + '%' }"
              ></div>
            </div>
            <span class="strength-text" :class="passwordStrength.class">
              {{ passwordStrength.text }}
            </span>
          </div>
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <div style="display: flex; gap: 8px;">
            <el-input
              v-model="resetPasswordForm.confirmPassword"
              type="password"
              placeholder="请再次输入新密码"
              show-password
              autocomplete="new-password"
              data-lpignore="true"
              style="flex: 1;"
            />
            <el-tooltip content="复制密码" placement="top">
              <el-button 
                :icon="DocumentCopy" 
                @click="copyPasswordToClipboard"
                :disabled="!resetPasswordForm.newPassword"
                style="flex-shrink: 0;"
              />
            </el-tooltip>
          </div>
        </el-form-item>
        
        <el-alert 
          v-if="resetPasswordForm.newPassword && resetPasswordForm.newPassword === resetPasswordForm.confirmPassword"
          type="success" 
          :closable="false"
          style="margin-bottom: 15px;"
        >
          <template #title>
            <span style="font-size: 13px;">
              ✓ 两次密码输入一致，点击"确定重置"即可完成密码重置
            </span>
          </template>
        </el-alert>
      </el-form>

      <template #footer>
        <el-button @click="resetPasswordDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="handleResetPasswordSubmit" 
          :loading="resettingPassword"
          :disabled="passwordStrength.level < 1"
        >
          确定重置
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Refresh, CopyDocument, DocumentCopy } from '@element-plus/icons-vue'
import {
  getChannelPartners,
  createChannelPartner,
  updateChannelPartner,
  resetPartnerPassword
} from '../api'

const router = useRouter()

const loading = ref(false)
const partners = ref([])
const searchText = ref('')
const dialogVisible = ref(false)
const dialogType = ref('create')
const formRef = ref(null)
const submitting = ref(false)

const formData = ref({
  username: '',
  password: '',
  name: '',
  company_name: '',
  phone: '',
  email: ''
})

const formRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  name: [{ required: true, message: '请输入渠道商名称', trigger: 'blur' }]
}

// 重置密码相关
const resetPasswordDialogVisible = ref(false)
const resetPasswordFormRef = ref(null)
const resettingPassword = ref(false)
const currentResetPartner = ref(null)

const resetPasswordForm = ref({
  newPassword: '',
  confirmPassword: ''
})

const passwordStrength = ref({
  level: 0,
  text: '弱',
  class: 'weak',
  percent: 0
})

const resetPasswordRules = {
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== resetPasswordForm.value.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const filteredPartners = computed(() => {
  if (!searchText.value) return partners.value
  return partners.value.filter(partner =>
    partner.name?.toLowerCase().includes(searchText.value.toLowerCase()) ||
    partner.username?.toLowerCase().includes(searchText.value.toLowerCase()) ||
    partner.company_name?.toLowerCase().includes(searchText.value.toLowerCase())
  )
})

async function fetchPartners() {
  loading.value = true
  try {
    const response = await getChannelPartners()
    partners.value = response.data || []
  } catch (error) {
    console.error('获取渠道商列表失败:', error)
    ElMessage.error(error.message || '获取渠道商列表失败')
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  dialogType.value = 'create'
  formData.value = {
    username: '',
    password: '',
    name: '',
    company_name: '',
    phone: '',
    email: ''
  }
  dialogVisible.value = true
}

function showEditDialog(partner) {
  dialogType.value = 'edit'
  formData.value = {
    uuid: partner.uuid,
    name: partner.name,
    company_name: partner.company_name,
    phone: partner.phone,
    email: partner.email
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  try {
    await formRef.value.validate()
    submitting.value = true

    if (dialogType.value === 'create') {
      await createChannelPartner(formData.value)
      ElMessage.success('渠道商创建成功')
    } else {
      await updateChannelPartner(formData.value.uuid, formData.value)
      ElMessage.success('渠道商信息更新成功')
    }

    dialogVisible.value = false
    fetchPartners()
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    submitting.value = false
  }
}

function resetPassword(partner) {
  currentResetPartner.value = partner
  resetPasswordForm.value = {
    newPassword: '',
    confirmPassword: ''
  }
  passwordStrength.value = {
    level: 0,
    text: '弱',
    class: 'weak',
    percent: 0
  }
  resetPasswordDialogVisible.value = true
}

// 检查密码强度
function checkPasswordStrength() {
  const password = resetPasswordForm.value.newPassword
  if (!password) {
    passwordStrength.value = { level: 0, text: '弱', class: 'weak', percent: 0 }
    return
  }

  let level = 0
  let percent = 20

  // 长度检查
  if (password.length >= 6) level++
  if (password.length >= 8) level++
  if (password.length >= 12) level++

  // 复杂度检查
  if (/[a-z]/.test(password)) { level++; percent += 15 }
  if (/[A-Z]/.test(password)) { level++; percent += 15 }
  if (/[0-9]/.test(password)) { level++; percent += 15 }
  if (/[^a-zA-Z0-9]/.test(password)) { level++; percent += 20 }

  percent = Math.min(percent, 100)

  if (level <= 2) {
    passwordStrength.value = { level, text: '弱', class: 'weak', percent }
  } else if (level <= 4) {
    passwordStrength.value = { level, text: '中等', class: 'medium', percent }
  } else {
    passwordStrength.value = { level, text: '强', class: 'strong', percent }
  }
}

// 生成强密码
function generatePassword() {
  // 定义字符集
  const lowercase = 'abcdefghijklmnopqrstuvwxyz'
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  const numbers = '0123456789'
  const symbols = '!@#$%^&*-_=+'
  
  // 生成12位密码，确保包含所有类型的字符
  let password = ''
  
  // 确保至少包含一个小写字母
  password += lowercase[Math.floor(Math.random() * lowercase.length)]
  
  // 确保至少包含一个大写字母
  password += uppercase[Math.floor(Math.random() * uppercase.length)]
  
  // 确保至少包含两个数字
  password += numbers[Math.floor(Math.random() * numbers.length)]
  password += numbers[Math.floor(Math.random() * numbers.length)]
  
  // 确保至少包含一个特殊字符
  password += symbols[Math.floor(Math.random() * symbols.length)]
  
  // 剩余7位从所有字符中随机选择
  const allChars = lowercase + uppercase + numbers + symbols
  for (let i = 0; i < 7; i++) {
    password += allChars[Math.floor(Math.random() * allChars.length)]
  }
  
  // 打乱密码顺序
  password = password.split('').sort(() => Math.random() - 0.5).join('')
  
  // 填充到表单
  resetPasswordForm.value.newPassword = password
  resetPasswordForm.value.confirmPassword = password
  
  // 检查密码强度
  checkPasswordStrength()
  
  // 复制到剪贴板
  copyToClipboard(password)
  
  ElMessage.success('已生成强密码并复制到剪贴板')
}

// 复制到剪贴板
function copyToClipboard(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).catch(() => {
      // 如果失败，使用旧方法
      fallbackCopyToClipboard(text)
    })
  } else {
    fallbackCopyToClipboard(text)
  }
}

// 兼容旧浏览器的复制方法
function fallbackCopyToClipboard(text) {
  const textArea = document.createElement('textarea')
  textArea.value = text
  textArea.style.position = 'fixed'
  textArea.style.left = '-999999px'
  textArea.style.top = '-999999px'
  document.body.appendChild(textArea)
  textArea.focus()
  textArea.select()
  try {
    document.execCommand('copy')
  } catch (err) {
    console.error('复制失败:', err)
  }
  document.body.removeChild(textArea)
}

// 复制密码按钮
function copyPasswordToClipboard() {
  if (resetPasswordForm.value.newPassword) {
    copyToClipboard(resetPasswordForm.value.newPassword)
    ElMessage.success('密码已复制到剪贴板')
  }
}

// 提交重置密码
async function handleResetPasswordSubmit() {
  try {
    await resetPasswordFormRef.value.validate()
    resettingPassword.value = true

    await resetPartnerPassword(currentResetPartner.value.uuid, resetPasswordForm.value.newPassword)
    
    ElMessage.success('密码重置成功')
    resetPasswordDialogVisible.value = false
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    resettingPassword.value = false
  }
}

function toggleStatus(partner) {
  const action = partner.is_active ? '禁用' : '启用'
  ElMessageBox.confirm(`确定要${action}该渠道商吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await updateChannelPartner(partner.uuid, { is_active: !partner.is_active })
      ElMessage.success(`${action}成功`)
      fetchPartners()
    } catch (error) {
      ElMessage.error(error.message || `${action}失败`)
    }
  }).catch(() => {})
}

function viewDetail(partner) {
  router.push({
    name: 'AdminChannelPartnerDetail',
    params: { partnerId: partner.uuid }
  })
}

onMounted(() => {
  fetchPartners()
})
</script>

<style scoped lang="scss">
.channel-partners {
  .header-card {
    margin-bottom: 20px;
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .page-title {
        font-size: 24px;
        font-weight: 600;
        color: #2c3e50;
        margin: 0 0 8px 0;
      }
      
      .page-description {
        color: #909399;
        margin: 0;
      }
    }
  }
  
  .content-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .card-title {
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
      }
    }
    
    .empty-state {
      padding: 40px 0;
    }
  }

  // 密码强度样式
  .password-strength {
    display: flex;
    align-items: center;
    gap: 12px;

    .strength-bar {
      flex: 1;
      height: 8px;
      background-color: #e4e7ed;
      border-radius: 4px;
      overflow: hidden;

      .strength-fill {
        height: 100%;
        transition: all 0.3s ease;
        border-radius: 4px;

        &.weak {
          background: linear-gradient(90deg, #f56c6c, #f78989);
        }

        &.medium {
          background: linear-gradient(90deg, #e6a23c, #ebb563);
        }

        &.strong {
          background: linear-gradient(90deg, #67c23a, #85ce61);
        }
      }
    }

    .strength-text {
      font-size: 14px;
      font-weight: 500;
      min-width: 40px;
      text-align: center;

      &.weak {
        color: #f56c6c;
      }

      &.medium {
        color: #e6a23c;
      }

      &.strong {
        color: #67c23a;
      }
    }
  }
}
</style>
