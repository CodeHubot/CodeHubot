<template>
  <el-dialog
    v-model="dialogVisible"
    :title="currentTab === 'profile' ? '个人信息' : '修改密码'"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <el-tabs v-model="currentTab" class="profile-tabs">
      <!-- 个人信息标签 -->
      <el-tab-pane label="个人信息" name="profile">
        <el-form
          ref="profileFormRef"
          :model="profileForm"
          label-width="100px"
          class="profile-form"
        >
          <el-form-item label="用户名">
            <el-input v-model="profileForm.username" disabled />
          </el-form-item>
          
          <el-form-item label="昵称">
            <el-input
              v-model="profileForm.nickname"
              placeholder="请输入昵称（可选）"
              clearable
            />
          </el-form-item>
          
          <el-form-item label="邮箱">
            <el-input
              v-model="profileForm.email"
              placeholder="请输入邮箱（可选）"
              clearable
            />
          </el-form-item>
          
          <el-form-item label="角色">
            <el-tag :type="getRoleType(userInfo?.role)">
              {{ getRoleText(userInfo?.role) }}
            </el-tag>
          </el-form-item>
          
          <el-form-item v-if="userInfo?.school_name" label="所属学校">
            <span>{{ userInfo.school_name }}</span>
          </el-form-item>
          
          <el-form-item label="注册时间">
            <span>{{ formatDateTime(userInfo?.created_at) }}</span>
          </el-form-item>
          
          <el-form-item label="最后登录">
            <span>{{ formatDateTime(userInfo?.last_login) || '未记录' }}</span>
          </el-form-item>
        </el-form>
        
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            :loading="profileLoading"
            @click="handleUpdateProfile"
          >
            保存修改
          </el-button>
        </div>
      </el-tab-pane>
      
      <!-- 修改密码标签 -->
      <el-tab-pane label="修改密码" name="password">
        <el-alert
          v-if="forceChangePassword"
          title="首次登录需要修改密码"
          type="warning"
          :closable="false"
          style="margin-bottom: 20px;"
        >
          为了您的账户安全，请立即修改您的初始密码
        </el-alert>
        
        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="100px"
          class="profile-form"
        >
          <el-form-item label="当前密码" prop="old_password">
            <el-input
              v-model="passwordForm.old_password"
              type="password"
              placeholder="请输入当前密码"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="新密码" prop="new_password">
            <el-input
              v-model="passwordForm.new_password"
              type="password"
              placeholder="请输入新密码"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="确认密码" prop="confirm_password">
            <el-input
              v-model="passwordForm.confirm_password"
              type="password"
              placeholder="请再次输入新密码"
              show-password
            />
            <div class="password-tips">
              <p>密码要求：</p>
              <ul>
                <li>长度至少8个字符</li>
                <li>必须包含字母和数字</li>
                <li>不能包含空格</li>
              </ul>
            </div>
          </el-form-item>
        </el-form>
        
        <div class="dialog-footer">
          <el-button
            v-if="!forceChangePassword"
            @click="dialogVisible = false"
          >
            取消
          </el-button>
          <el-button
            type="primary"
            :loading="passwordLoading"
            @click="handleChangePassword"
          >
            确认修改
          </el-button>
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { changePassword, updateProfile } from '@/shared/api/auth'
import dayjs from 'dayjs'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  defaultTab: {
    type: String,
    default: 'profile'
  },
  forceChangePassword: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'password-changed', 'profile-updated'])

// Store
const authStore = useAuthStore()

// 响应式数据
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => {
    // 如果是强制修改密码模式，不允许关闭对话框
    if (props.forceChangePassword && !val) {
      ElMessage.warning('请先修改密码后再继续使用系统')
      return
    }
    emit('update:modelValue', val)
  }
})

const currentTab = ref(props.defaultTab)
const profileFormRef = ref(null)
const passwordFormRef = ref(null)
const profileLoading = ref(false)
const passwordLoading = ref(false)

// 用户信息
const userInfo = computed(() => authStore.userInfo)

// 个人信息表单
const profileForm = reactive({
  username: '',
  nickname: '',
  email: ''
})

// 密码表单
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

// 密码验证规则
const passwordRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少8个字符', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (!/[a-zA-Z]/.test(value)) {
          callback(new Error('密码必须包含字母'))
        } else if (!/[0-9]/.test(value)) {
          callback(new Error('密码必须包含数字'))
        } else if (/\s/.test(value)) {
          callback(new Error('密码不能包含空格'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 监听对话框打开，初始化表单数据
watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      // 重置表单
      resetForms()
      
      // 加载用户信息
      loadUserInfo()
      
      // 如果是强制修改密码，自动切换到密码标签
      if (props.forceChangePassword) {
        currentTab.value = 'password'
      } else {
        currentTab.value = props.defaultTab
      }
    }
  }
)

// 加载用户信息
function loadUserInfo() {
  if (userInfo.value) {
    profileForm.username = userInfo.value.username || ''
    profileForm.nickname = userInfo.value.nickname || ''
    profileForm.email = userInfo.value.email || ''
  }
}

// 重置表单
function resetForms() {
  passwordForm.old_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
  
  if (passwordFormRef.value) {
    passwordFormRef.value.resetFields()
  }
  if (profileFormRef.value) {
    profileFormRef.value.resetFields()
  }
}

// 更新个人信息
async function handleUpdateProfile() {
  try {
    profileLoading.value = true
    
    // 准备更新数据（只提交修改过的字段）
    const updateData = {}
    
    if (profileForm.nickname !== (userInfo.value?.nickname || '')) {
      updateData.nickname = profileForm.nickname || null
    }
    
    if (profileForm.email !== (userInfo.value?.email || '')) {
      updateData.email = profileForm.email || null
    }
    
    // 如果没有修改，提示用户
    if (Object.keys(updateData).length === 0) {
      ElMessage.info('没有修改任何信息')
      return
    }
    
    // 调用API
    const response = await updateProfile(updateData)
    
    // 检查响应是否成功
    if (response.success) {
      // 显示成功提示
      ElMessage.success(response.message || '个人信息更新成功')
      
      // 更新Store中的用户信息
      if (response.data) {
        authStore.userInfo = {
          ...authStore.userInfo,
          ...response.data
        }
      }
      
      // 触发个人信息更新事件
      emit('profile-updated')
      
      // 重置表单
      resetForms()
      
      // 关闭对话框
      dialogVisible.value = false
    }
  } catch (error) {
    console.error('更新个人信息失败:', error)
    // 错误提示已在 request 拦截器中统一处理，这里只记录日志
  } finally {
    profileLoading.value = false
  }
}

// 修改密码
async function handleChangePassword() {
  try {
    // 验证表单
    const valid = await passwordFormRef.value.validate()
    if (!valid) return
    
    passwordLoading.value = true
    
    // 调用API
    const response = await changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })
    
    // 检查响应是否成功
    if (response.success) {
      // 显示成功提示
      ElMessage.success(response.message || '密码修改成功')
      
      // 清除强制修改密码标志（更新本地Store）
      if (authStore.userInfo) {
        authStore.userInfo.need_change_password = false
      }
      
      // 触发密码修改成功事件
      emit('password-changed')
      
      // 重置密码表单
      resetForms()
      
      // 关闭对话框
      dialogVisible.value = false
    }
  } catch (error) {
    console.error('修改密码失败:', error)
    // 错误提示已在 request 拦截器中统一处理，这里只记录日志
    // 如果需要额外处理可以在这里添加
  } finally {
    passwordLoading.value = false
  }
}

// 关闭对话框
function handleClose() {
  if (props.forceChangePassword) {
    ElMessage.warning('请先修改密码后再继续使用系统')
    return
  }
  resetForms()
}

// 格式化时间
function formatDateTime(dateTime) {
  if (!dateTime) return ''
  return dayjs(dateTime).format('YYYY-MM-DD HH:mm:ss')
}

// 获取角色文本
function getRoleText(role) {
  const roleMap = {
    individual: '独立用户',
    platform_admin: '平台管理员',
    school_admin: '学校管理员',
    channel_manager: '渠道管理员',
    channel_partner: '渠道商',
    teacher: '教师',
    student: '学生'
  }
  return roleMap[role] || role
}

// 获取角色标签类型
function getRoleType(role) {
  const typeMap = {
    individual: '',
    platform_admin: 'danger',
    school_admin: 'warning',
    channel_manager: 'success',
    channel_partner: 'info',
    teacher: 'primary',
    student: ''
  }
  return typeMap[role] || ''
}
</script>

<style scoped lang="scss">
.profile-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 20px;
  }
}

.profile-form {
  padding: 10px 20px;
  
  :deep(.el-form-item) {
    margin-bottom: 18px;
  }
  
  :deep(.el-input) {
    width: 100%;
  }
}

.password-tips {
  margin-top: 8px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 12px;
  color: #606266;
  
  p {
    margin: 0 0 5px 0;
    font-weight: 500;
  }
  
  ul {
    margin: 0;
    padding-left: 20px;
    
    li {
      margin: 3px 0;
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px 20px 10px;
  border-top: 1px solid #f0f0f0;
  margin-top: 20px;
}
</style>
